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


class JungleProfiler(object):

    def __init__(self,reps=2,comb=True,tlim=5,**kwargs):
        '''
        Decorator class for standardized profiling and reporting
        Called before decorated function is read
        :param reps:
        '''
        self.kwargs = kwargs # These will be used to generate testing
        self.reps = reps
        self.comb = comb
        self.tlim = tlim

        self.platform_specs = 'Machine: %s\n' \
                              'Version: %s\n' \
                              'Platform: %s\n' \
                              'Processor: %s'%(platform.machine(),
                                               platform.version(),
                                               platform.platform(),
                                               platform.processor())
        self.python_version = '%d.%d.%d\nRelease lvl: %s\nSerial #:%d'%sys.version_info
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
            if not isinstance(self.kwargs[arg],list):
                raise ValueError('kwarg: %s provided to JungleProfiler is of'
                                 ' type %s and should be a list'%(arg,type(self.kwargs[arg])))

        # All Combinations
        arg_names = sorted(self.kwargs)
        test_tuples = itertools.product(*(self.kwargs[arg] for arg in arg_names))
        test_seq = [{arg_names[i]:val for i,val in enumerate(tt)} for tt in test_tuples]
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
        self.test_seq = self.make_test_sequence()
        self.run_dict = {}



        def wrapped_f(*args):
            ''' Called when decorated function is called '''
            for i,kwarg_dict in enumerate(self.test_seq):
                # strip out rep kwarg
                kwarg_dict.pop('rep',None)
                run = {
                    'kwargs' : kwarg_dict,
                    'start' : time.time(),
                    'stdout' : None,
                    'error' : None
                }
                try:
                    # Start memory and time profiling
                    sio = io.StringIO()
                    with redirect_stdout(sio):
                        f(**kwarg_dict)
                    run['stdout'] = sio.getvalue()
                    # End memory and time profiling
                except Exception as e:
                    run['error'] = e
                run['stop'] = time.time()

                self.run_dict[i] = run
            return self

        return wrapped_f

    def __str__(self):
        s = 'JungleProfiler'
        s += '\n\nPython Version:\n%s' % self.python_version
        s += '\n\nMachine Specs:\n%s' % self.platform_specs
        s += '\n\nSource File:\n%s' % self.source_file
        s += '\n\nSource Code:\n%s' % self.source_code
        s += '\n\nDocumentation:\n%s' % self.f_docs
        s += '\n\nCaptured StdOut:\n%s' % self.f_stdout
        #todo timing
        #todo memory


        return s

    def plot(self,path):
        '''

        :param path:
        :return:
        '''
        pass

    def dump_(self,path):
        '''

        :param path:
        :return:
        '''
        pass



@JungleProfiler(a=[10,100],b=[20,200],c=[30,300])
def simple_func(a=1,b=2,c=3):
    '''
    Dummy Function used to test simple functions
    '''
    print('A:%d\tB:%d\tC:%d'%(a,b,c))


@JungleProfiler()
def simple_func2(a=1,b=2,c=3):
    '''
    Dummy Function used to test simple functions
    '''
    print('A:%d\tB:%d\tC:%d'%(a,b,c))

if __name__ == '__main__':
    print('\n---simple func ---')
    jp = simple_func()
    for d in jp.run_dict:
        print(d,jp.run_dict[d])
        print(jp.run_dict[d]['stdout'])

    print('\n---simple func 2 ---')
    jp = simple_func2()
    for d in jp.run_dict:
        print(d, jp.run_dict[d])
        print(jp.run_dict[d]['stdout'])











