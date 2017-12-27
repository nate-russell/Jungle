'''
Sorting Examples for showcasing and developing Jungle features
'''
from jungle import JungleController, JungleProfiler
import numpy as np

class Sorting_Prototype:

    def __init__(self):
        pass

    def sort(self):
        pass

    @JungleController(n=[10,20,30])
    def test_sort_n(self,n=100):
        ''' Test sorting an iterable of size n with a random distribution '''
        # make data to sort with random distribution
        list_2_sort = list(np.random.randn(n))

        @JungleProfiler()
        def sort_n(l):
            sorted_list = self.sort(l)
            return sorted_list

        # Sort and check sort status
        sorted_list,_ = sort_n(list_2_sort)
        sort_status = all(sorted_list[i] <= sorted_list[i+1] for i in range(len(sorted_list)-1))
        return sort_status

    @JungleController()
    @JungleProfiler()
    def test_nonrandom_sort(self):
        pass


class NP_QuickSort(Sorting_Prototype):

    def sort(self,l):
        return np.sort(l,kind='quicksort')

class NP_MergeSort(Sorting_Prototype):

    def sort(self,l):
        return np.sort(l,kind='mergesort')

class NP_HeapSort(Sorting_Prototype):

    def sort(self,l):
        return np.sort(l,kind='heapsort')



if __name__ == '__main__':

    m = NP_QuickSort()
    jc = m.test_sort_n()
    print(jc)








