from inspectiontest import Child, Parent
import inspect

child = Child()
test_func = child.parent_test

print('Is Method: %s' % inspect.ismethod(test_func))
print('Is Function: %s' % inspect.isfunction(test_func))
print(test_func.__self__)
lines = inspect.getsourcelines(test_func)
source_code = "".join(lines[0])
print(source_code)