'''
Sorting Examples for showcasing and developing Jungle features
'''
import inspect
from jungle import JungleExperiment, JungleProfiler
import numpy as np
print('Finished Loading Modules')





class Sorting_Prototype:

    @JungleExperiment(reps=1,n=[100,500,1000])
    def test_sort_n(self,n=100,seed=1234):
        ''' Test sorting an iterable of size n with a random distribution '''
        # make data to sort with random distribution
        np.random.seed(seed)
        list_2_sort = list(np.random.randn(n))

        @JungleProfiler()
        def sort_n(l):
            sorted_list = self.sort(l)
            return sorted_list

        # Sort and check sort status
        sorted_list,_ = sort_n(list_2_sort)
        sort_status = all(sorted_list[i] <= sorted_list[i+1] for i in range(len(sorted_list)-1))
        return sort_status

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

    print('\n__main__\n')

    print('Starting Call #1')
    m1 = NP_QuickSort()
    jc1 = m1.test_sort_n()

    print('\nStarting Call #2')
    m2 = NP_MergeSort()
    jc2 = m2.test_sort_n()










