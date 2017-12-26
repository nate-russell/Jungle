import platform
import sys
import psutil
from memory_profiler import profile as mprofile
import inspect
import io
from contextlib import redirect_stdout
import itertools
import random
import time
from functools import wraps, update_wrapper
import datetime


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


class JungleController(object):

    def __init__(self, reps=2, comb=True, tlim=5, **kwargs):
        '''
        Decorator class for standardized profiling and reporting
        Called before decorated function is read
        :param reps:
        '''
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

    def __call__(self, f):
        """ decorator wrapper """
        lines = inspect.getsourcelines(f)
        self.source_code = "".join(lines[0])
        self.source_file = inspect.getsourcefile(f)
        self.f_docs = f.__doc__
        self.func_name = f.__name__

        # update_wrapper(wrapper=persistent_locals,wrapped=f)
        f = persistent_locals(f)

        self.test_seq = self.make_test_sequence()

        @wraps(f)
        def junglecontroller_wrapped_f(*args):
            ''' Called when decorated function is called '''
            for i, kwarg_dict in enumerate(self.test_seq):
                # strip out rep kwarg
                kwarg_dict.pop('rep', None)
                run = {
                    'kwargs': kwarg_dict,
                    'start_seconds': time.time(),
                    'stdout': None,
                    'error': None,
                    'profile': None
                }

                try:
                    # Start memory and time profiling
                    sio = io.StringIO()
                    with redirect_stdout(sio):

                        # Call the decorated function with the kwarg_dict provided by controller
                        # arg should have a self and
                        f(*args, **kwarg_dict)

                        for local in f.locals:
                            obj = f.locals[local]
                            # print('\nLocal: %s\tObject:%s'%(local,f.locals[local]))
                            if isinstance(obj, JungleProfile):
                                run['profile'] = obj
                                break
                            else:
                                try:
                                    # for item in itertools.chain.from_iterable(obj):
                                    for item in obj:
                                        if isinstance(item, JungleProfile):
                                            run['profile'] = item
                                            break
                                except TypeError:
                                    pass
                                    # print('Not Iterable... type = %s'%type(obj))

                    run['stdout'] = sio.getvalue()
                    # End memory and time profiling
                except Exception as e:
                    run['error'] = e
                run['stop_seconds'] = time.time()

                # Get Date Time formatted objs
                run['start_datetime'] = str(datetime.datetime.fromtimestamp(run['start_seconds']))
                run['stop_datetime'] = str(datetime.datetime.fromtimestamp(run['stop_seconds']))

                self.run_dict[i] = run
            return self

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

    def analyze_rundict(self):
        #todo test for statistical trends in data, including run order
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

    def __init__(self, memory=True, **kwargs):
        self.memory = memory
        self.kwargs = kwargs
        pass

    def __call__(self, f):
        @wraps(f)
        def jungleprofiler_wrapped_f(*args, **kwargs):
            ''' Wrapper that collects time and system usage data on wrapped function f'''
            freturn = f(*args, **kwargs)
            self.prof = JungleProfile()
            return freturn, self.prof

        return jungleprofiler_wrapped_f

    def __str__(self):
        return ''


class JungleProfile(object):

    def __init__(self):
        pass

    def __str__(self):
        return 'This is a Profile Object!'


if __name__ == '__main__':

    @JungleController(a=[10, 100], b=[20], c=[30])
    def simple_func(a=1, b=2, c=3):
        ''' Dummy Function used with Jungle Controller with Kwargs and NO JungleProfiler '''
        print('A:%d\tB:%d\tC:%d' % (a, b, c))
        return 'something', 'another something'


    @JungleController()
    def simple_func2(a=1, b=2, c=3):
        ''' Dummy Function used with Jungle Controller without Kwargs and NO JungleProfiler '''
        print('A:%d\tB:%d\tC:%d' % (a, b, c))
        return 'something', 'another something'


    @JungleController(a=[10, 100], b=[20], c=[30])
    @JungleProfiler()
    def simple_func3(a=1, b=2, c=3):
        ''' Dummy Function used with Jungle Controller with Kwargs and JungleProfiler '''
        print('A:%d\tB:%d\tC:%d' % (a, b, c))
        return 'something', 'another something'


    @JungleController()
    @JungleProfiler()
    def simple_func4(a=1, b=2, c=3):
        ''' Dummy Function used with Jungle Controller without Kwargs but with JungleProfiler '''
        print('A:%d\tB:%d\tC:%d' % (a, b, c))
        return 'something', 'another something'


    @JungleController(a=[10, 100], b=[20, 20], c=[30, 30])
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
