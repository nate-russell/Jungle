from jungle.utils.jungleprofiler import JungleController, JungleProfiler
import numpy as np

class Sorting_Prototype:


    def sort(self, l):
        ''' Sort L '''
        pass

    def test_correctness(self):
        ''' Simple test case to make sure '''
        pass


    @JungleController(n=[10,20,30])
    def test_sort_n(self,n=100):
        ''' Test sorting an iterable of size n with a random distribution '''
        print('OUTSIDE: Setting Up list to Sort')
        list_2_sort = list(np.random.randn(n))

        @JungleProfiler
        def sort_n(l):
            print('INSIDE: Sorting List')
            return l



        print('OUTSIDE: Checking correctness of sort')


class MySorter(Sorting_Prototype):














