import inspect
from line_profiler import LineProfiler
from memory_profiler import memory_usage, profile
from jungle import JungleProfiler, JungleExperiment

class Parent:
    ''' Parent Class '''

    def __init__(self):
        pass

    def parent_test(self):
        print('parent_test called')
        self.child_do(100)


class Child(Parent):
    ''' Child Class '''

    def __init__(self):
        print('Child Initialized')
        pass

    def child_do(self, n):
        print('Child.child_do Called')
        c = 0
        for i in range(n):
            c += i
        return c


if __name__ == '__main__':
    child = Child()
    test_func = child.parent_test

    print('\n__main__')
    print('Is Function: %s' % inspect.isfunction(test_func))
    print('Is Method: %s' % inspect.ismethod(test_func))
    print(test_func.__self__)
    print(test_func.__self__.__getattribute__('child_do'))

    methods = ['child_do', 'parent_test']
    funcs_to_add = []

    print(dir(test_func.__self__))

    if inspect.ismethod(test_func):
        for method in dir(test_func.__self__):
            if method not in dir(object()):
                print('Method: %s' % method)

    cdo = getattr(test_func.__self__, 'child_do')
    print(cdo)

    lines = inspect.getsourcelines(test_func)
    source_code = "".join(lines[0])
    print('Source Code: \n%s' % source_code)
