import platform
import sys
import psutil
from memory_profiler import profile as mprofile
import inspect
import io
from contextlib import redirect_stdout



class JungleProfiler(object):

    def __init__(self,reps=5):
        '''
        Decorator class for standardized profiling and reporting
        :param reps:
        '''
        self.reps = 5
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



    def __call__(self, f):
        """ decorator wrapper """
        lines = inspect.getsourcelines(f)
        self.source_code = "".join(lines[0])
        self.source_file = inspect.getsourcefile(f)
        self.f_docs = f.__doc__


        def wrapped_f(*args):
            # Start memory and time profiling
            sio = io.StringIO()
            with redirect_stdout(sio):
                f(*args)
            self.f_stdout = sio.getvalue()
            # End memory and time profiling
            return self

        return wrapped_f



@JungleProfiler()
def stuff():
    """
    Dummy Function used to test simple functions
    :return:
    """
    print('yo yo check it out')


if __name__ == '__main__':
    jp = stuff()
    print(jp)










