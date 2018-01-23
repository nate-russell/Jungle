import platform
import sys
import psutil
from memory_profiler import profile as mprofile
from line_profiler import LineProfiler
import inspect
import io
from contextlib import redirect_stdout
import itertools
import random
import time
from functools import wraps, update_wrapper, partial
import datetime
import json
from pprint import pprint
from collections import defaultdict
import pandas as pd
import seaborn as sns
import copy


class DelayedDecorator(object):
    """Wrapper that delays decorating a function until it is invoked.

    This class allows a decorator to be used with both ordinary functions and
    methods of classes. It wraps the function passed to it with the decorator
    passed to it, but with some special handling:

      - If the wrapped function is an ordinary function, it will be decorated
        the first time it is called.

      - If the wrapped function is a method of a class, it will be decorated
        separately the first time it is called on each instance of the class.
        It will also be decorated separately the first time it is called as
        an unbound method of the class itself (though this use case should
        be rare).
    """

    def __init__(self, deco, func):
        # The base decorated function (which may be modified, see below)
        self._func = func
        # The decorator that will be applied
        self._deco = deco
        # Variable to monitor calling as an ordinary function
        self.__decofunc = None
        # Variable to monitor calling as an unbound method
        self.__clsfunc = None

    def _decorated(self, cls=None, instance=None):
        """Return the decorated function.

        This method is for internal use only; it can be implemented by
        subclasses to modify the actual decorated function before it is
        returned. The ``cls`` and ``instance`` parameters are supplied so
        this method can tell how it was invoked. If it is not overridden,
        the base function stored when this class was instantiated will
        be decorated by the decorator passed when this class was instantiated,
        and then returned.

        Note that factoring out this method, in addition to allowing
        subclasses to modify the decorated function, ensures that the
        right thing is done automatically when the decorated function
        itself is a higher-order function (e.g., a generator function).
        Since this method is called every time the decorated function
        is accessed, a new instance of whatever it returns will be
        created (e.g., a new generator will be realized), which is
        exactly the expected semantics.
        """
        return self._deco(self._func)

    def __call__(self, *args, **kwargs):
        """Direct function call syntax support.

        This makes an instance of this class work just like the underlying
        decorated function when called directly as an ordinary function.
        An internal reference to the decorated function is stored so that
        future direct calls will get the stored function.
        """
        if not self.__decofunc:
            self.__decofunc = self._decorated()
        return self.__decofunc(*args, **kwargs)

    def __get__(self, instance, cls):
        """Descriptor protocol support.

        This makes an instance of this class function correctly when it
        is used to decorate a method on a user-defined class. If called
        as a bound method, we store the decorated function in the instance
        dictionary, so we will not be called again for that instance. If
        called as an unbound method, we store a reference to the decorated
        function internally and use it on future unbound method calls.
        """
        if instance:
            deco = instancemethod(self._decorated(cls, instance), instance, cls)
            # This prevents us from being called again for this instance
            setattr(instance, self._func.__name__, deco)
        elif cls:
            if not self.__clsfunc:
                self.__clsfunc = instancemethod(self._decorated(cls), None, cls)
            deco = self.__clsfunc
        else:
            raise ValueError("Must supply instance or class to descriptor.")
        return deco


def get_class_that_defined_method(meth):
    if inspect.ismethod(meth):
        print('method')
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        print('function')
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    return getattr(meth, '__objclass__', None)  # handle special descriptor objects


class JungleEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, JungleExperiment):
            return 'Placeholder for serialized Jungle Controller'
        else:
            return super(JungleEncoder, self).default(obj)


class persistent_locals(object):

    def __init__(self, func):
        self._locals = {}
        update_wrapper(self, func)
        self.func = func

    def __call__(self, *args, **kwargs):

        def tracer(frame, event, arg):
            if event == 'return':
                self._locals = frame.f_locals.copy()

        # tracer is activated on next call, return or exception
        sys.setprofile(tracer)
        try:
            # trace the function call
            f = self.func(*args, **kwargs)
        finally:
            # disable tracer and replace with old one
            sys.setprofile(None)
        return f

    def clear_locals(self):
        self._locals = {}

    @property
    def locals(self):
        return self._locals


def delayinit(cls):
    def init_before_get(obj, attr):
        if not object.__getattribute__(obj, '_initialized'):
            obj.__init__(*obj._init_args, **obj._init_kwargs)
            obj._initialized = True
        return object.__getattribute__(obj, attr)

    cls.__getattribute__ = init_before_get

    def construct(*args, **kwargs):
        obj = cls.__new__(cls, *args, **kwargs)
        obj._init_args = args
        obj._init_kwargs = kwargs
        obj._initialized = False
        return obj

    return construct


class JungleExperiment(object):
    """ Decorator Class for """

    def __init__(self, reps=2, comb=True, tlim=5, **kwargs):
        '''
        Decorator class for standardized profiling and reporting
        Called before decorated function is read
        :param reps:
        '''
        print('%s.__init__ called' % self.__class__.__name__)
        self.kwargs = kwargs  # These will be used to generate testing
        self.reps = reps
        self.comb = comb
        self.tlim = tlim
        self.run_dict = {}

        self.platform_specs = 'Machine: %s\n' \
                              'Version: %s\n' \
                              'Platform: %s\n' \
                              'Processor: %s' % (platform.machine(),
                                                 platform.version(),
                                                 platform.platform(),
                                                 platform.processor())
        self.python_version = '%d.%d.%d\nRelease lvl: %s\nSerial #:%d' % sys.version_info
        self.vm = psutil.virtual_memory()
        self.cpu = psutil.cpu_stats()

    def __call__(self, f, *args, **kwargs):
        """ decorator wrapper """
        print('%s.__call__ called' % self.__class__.__name__)
        lines = inspect.getsourcelines(f)
        self.source_code = "".join(lines[0])
        self.source_file = inspect.getsourcefile(f)
        self.f_docs = f.__doc__
        self.func_name = f.__name__

        # Modify f to pick up JungleProfiler instance even if it isn't returned explicitly
        f = persistent_locals(f)
        # Generate randomized test sequence
        self.test_seq = self.make_test_sequence()

        @wraps(f)
        def junglecontroller_wrapped_f(*args):
            ''' Called when decorated function is called '''
            for i, kwarg_dict in enumerate(self.test_seq):
                try:
                    repnum = kwarg_dict['rep']
                except KeyError as ke:  # think there is an issue here
                    repnum = 'na'
                    pass

                kwarg_dict.pop('rep', None)
                run = {
                    'kwargs': kwarg_dict,
                    'start_seconds': time.time(),
                    'stdout': None,
                    'error': None,
                    'profile': None,
                    'rep': repnum
                }

                try:
                    # Call the decorated function with the kwarg_dict provided by JungleExperiment
                    f(*args, **kwarg_dict)

                    # Collect JungleProfile Instances
                    for local in f.locals:
                        obj = f.locals[local]
                        if isinstance(obj, JungleProfiler):
                            run['profile'] = obj
                            break
                        else:
                            try:
                                for item in obj:
                                    if isinstance(item, JungleProfiler):
                                        run['profile'] = item
                                        break
                            except TypeError:
                                pass

                    # End memory and time profiling
                except Exception as e:
                    run['error'] = e
                    raise e
                run['stop_seconds'] = time.time()

                # Get Date Time formatted objs
                run['start_datetime'] = str(datetime.datetime.fromtimestamp(run['start_seconds']))
                run['stop_datetime'] = str(datetime.datetime.fromtimestamp(run['stop_seconds']))
                run['controller walltime'] = run['stop_seconds'] - run['start_seconds']

                self.run_dict[i] = run
            self.postprocess_runs()
            return copy.deepcopy(self)

        return junglecontroller_wrapped_f

    def __str__(self):
        s = 'JungleProfiler'
        s += '\n\nPython Version: %s' % self.python_version
        s += '\n\nMachine Specs:\n%s' % self.platform_specs
        s += '\n\nSource File:\n%s' % self.source_file
        s += '\n\nSource Code:\n%s' % self.source_code
        s += '\n\nDocumentation:\n%s' % self.f_docs
        s += '\n\nRuns:'
        for (k, v) in self.run_dict.items():
            s += '\n\t%d: %s' % (k, v)
        # s += '\n\nCaptured StdOut:\n%s' % self.f_stdout
        # todo timing
        # todo memory
        return s

    def make_test_sequence(self):
        '''
        Convert kwargs into
        :return: iterable of kwargs dicts
        '''
        # Make sure rep arg isn't in kwargs
        if 'rep' in self.kwargs:
            raise ValueError('JungleProfiler received a kwarg named \'rep\'.'
                             ' This arg is used by JungleProfiler already. ')
        else:
            self.kwargs['rep'] = list(range(self.reps))
        # Make sure each arg in kwargs is a list
        for arg in self.kwargs:
            if not isinstance(self.kwargs[arg], list):
                raise ValueError('kwarg: %s provided to JungleProfiler is of'
                                 ' type %s and should be a list' % (arg, type(self.kwargs[arg])))

        # All Combinations
        arg_names = sorted(self.kwargs)
        test_tuples = itertools.product(*(self.kwargs[arg] for arg in arg_names))
        test_seq = [{arg_names[i]: val for i, val in enumerate(tt)} for tt in test_tuples]
        # todo add alternatives to all combinations

        # Shuffle to mitigate temporal confounding factors
        random.shuffle(test_seq)
        return test_seq

    def postprocess_runs(self):
        ''' Convert Run Dict into pandas df'''
        self.controller_dict = defaultdict(list)
        for key, rd in self.run_dict.items():
            self.controller_dict['index'].append(key)
            for rd_key, x in rd.items():
                if rd_key == 'profile':
                    self.controller_dict['profile'].append('Coming to Jungle Soon!')
                    self.controller_dict['walltime'].append(x.walltime)
                elif rd_key == 'kwargs':
                    assert isinstance(x, dict)
                    for arg, val in x.items():
                        self.controller_dict['kwarg: %s' % arg].append(val)
                else:
                    self.controller_dict[rd_key].append(x)

        self.controller_df = pd.DataFrame(self.controller_dict)
        self.controller_df.set_index('index')

    def analyze_rundict(self):
        # todo test for statistical trends in data, including run order
        pass

    def plot(self, path):
        '''

        :param path:
        :return:
        '''
        pass

    def dump_(self, path):
        '''

        :param path:
        :return:
        '''
        pass


class JungleProfiler(object):
    """ Decorator class for profiling a function or method """

    def __init__(self, m_prof=True, t_prof=True, other_funcs=None, **kwargs):
        print('%s.__init__ called' % self.__class__.__name__)
        self.other_funcs = other_funcs
        self.m_prof = m_prof
        self.t_prof = t_prof
        self.kwargs = kwargs
        pass

    def __call__(self, f):
        print('%s.__call__ called' % self.__class__.__name__)
        print('Function Name: %s' % f.__name__)
        print('Is Function: %s' % inspect.isfunction(f))
        print('Is Method: %s' % inspect.ismethod(f))

        @wraps(f)
        def jungleprofiler_wrapped_f(*args, **kwargs):
            ''' Wrapper that collects time and system usage data on wrapped function f'''

            # Set up LineProfiler
            lp = LineProfiler()
            lp.add_function(f)

            # Set up MemoryProfiler
            pass  # todo add Memory Profiler

            # Start Counters
            if self.t_prof: lp.enable_by_count()
            if self.m_prof: pass
            try:
                t0 = time.time()
                sio = io.StringIO()  # Collects redirected stdout
                with redirect_stdout(sio):
                    preturn = f(*args, **kwargs)
                self.stdout = sio.getvalue()
                t1 = time.time()
            finally:
                # Stop Counters
                if self.m_prof: lp.disable_by_count()
                if self.m_prof: pass  # todo add Memory Profiler

            # Collect Stats
            # print('Get Stats: %s' % lp.print_stats())

            self.walltime = t1 - t0
            return preturn, copy.deepcopy(self)

        return jungleprofiler_wrapped_f

    def __str__(self):
        return 'Walltime: %s' % self.walltime


# JungleExperiment = partial(DelayedDecorator, JungleExperiment)
# JungleProfiler = partial(DelayedDecorator, JungleProfiler)


if __name__ == '__main__':

    @JungleExperiment(a=[10, 100], b=[20], c=[30])
    def simple_func(a=1, b=2, c=3):
        ''' Dummy Function used with Jungle Controller with Kwargs and NO JungleProfiler '''
        print('A:%d\tB:%d\tC:%d' % (a, b, c))
        return 'something', 'another something'


    @JungleExperiment()
    def simple_func2(a=1, b=2, c=3):
        ''' Dummy Function used with Jungle Controller without Kwargs and NO JungleProfiler '''
        print('A:%d\tB:%d\tC:%d' % (a, b, c))
        return 'something', 'another something'


    @JungleExperiment(a=[10, 100], b=[20], c=[30])
    @JungleProfiler()
    def simple_func3(a=1, b=2, c=3):
        ''' Dummy Function used with Jungle Controller with Kwargs and JungleProfiler '''
        print('A:%d\tB:%d\tC:%d' % (a, b, c))
        return 'something', 'another something'


    @JungleExperiment()
    @JungleProfiler()
    def simple_func4(a=1, b=2, c=3):
        ''' Dummy Function used with Jungle Controller without Kwargs but with JungleProfiler '''
        print('A:%d\tB:%d\tC:%d' % (a, b, c))
        return 'something', 'another something'


    @JungleExperiment(a=[10, 100], b=[20, 20], c=[30, 30])
    def func_with_setup_and_teardown(a=1, b=2, c=3):
        ''' Dummy Function used with Jungle Controller with Kwargs and JungleProfiler around only part of the function'''
        print("OUTSIDE PROFILED REGION: Setup")

        @JungleProfiler()
        def inner_func(a=1, b=2, c=3):
            print('INSIDE PROFILED REGION:\tA:%d\tB:%d\tC:%d' % (a, b, c))
            return 'inner something'

        inner_func_return = inner_func(a=a, b=b, c=c)
        print("OUTSIDE PROFILED REGION: Teardown")
        return 'something', 'another something'


    def test_func(f):
        print('\n------- %s -------' % f.__name__)
        print('Docs: %s' % f.__doc__)
        jp = f()
        for d in jp.run_dict:
            print('Run #%d -> %s' % (d, jp.run_dict[d]))
            print('Error: %s' % jp.run_dict[d]['error'])
            print('Profile: %s' % jp.run_dict[d]['profile'])
            print('StdOut: \n%s' % jp.run_dict[d]['stdout'])


    # test_func(simple_func)
    # test_func(simple_func2)
    # test_func(simple_func3)
    # test_func(simple_func4)
    test_func(func_with_setup_and_teardown)
