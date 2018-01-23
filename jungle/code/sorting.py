'''
Sorting Examples for showcasing and developing Jungle features
'''
import inspect
from jungle import JungleExperiment, JungleProfiler
import numpy as np

print('Finished Loading Modules')

class Sorting_Prototype:

    print('\n---Test Sort N---')
    @JungleExperiment(reps=1, n=[100, 500])
    def test_sort_n(self, n=100, seed=1234):
        ''' Test sorting an iterable of size n with a random distribution '''
        # make data to sort with random distribution
        np.random.seed(seed)
        list_2_sort = list(np.random.randn(n))

        @JungleProfiler()
        def sort_n(l):
            sorted_list = self.sort(l)
            return sorted_list

        # Sort and check sort status
        sorted_list, _ = sort_n(list_2_sort)
        sort_status = all(sorted_list[i] <= sorted_list[i + 1] for i in range(len(sorted_list) - 1))
        return sort_status

    print('\n---Test Block Sort---')
    @JungleExperiment(reps=1, n_blocks=[2, 4], block_size=[50, 100])
    @JungleProfiler()
    def test_block_random_sort(self, n_blocks=4, block_size=100):
        print('n_blocks: %s' % n_blocks)
        print('block_size: %s' % block_size)
        return 'something'






class NP_QuickSort(Sorting_Prototype):

    def sort(self, l):
        return np.sort(l, kind='quicksort')


class NP_MergeSort(Sorting_Prototype):

    def sort(self, l):
        return np.sort(l, kind='mergesort')


class NP_HeapSort(Sorting_Prototype):

    def sort(self, l):
        return np.sort(l, kind='heapsort')


if __name__ == '__main__':
    print('\n__main__\n')

    print('\n---Starting Call #1---')
    m1 = NP_QuickSort()
    jc1 = m1.test_sort_n()

    print('\n---Starting Call #2---')
    m2 = NP_MergeSort()
    jc2 = m2.test_sort_n()

    print('\n---Starting Call #3---')
    m1 = NP_QuickSort()
    jc1 = m1.test_block_random_sort()

    print('\n---Starting Call #4---')
    m2 = NP_MergeSort()
    jc2 = m2.test_block_random_sort()
