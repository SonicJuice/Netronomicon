def _partition(to_sort, low, high):
    """ initialise pivot as the last array element. """
    pivot = to_sort[high]
    """ track position where elements <= pivot should be placed. """
    i = low - 1 
    for j in range(low, high):
        """ if j <= pivot, increment i and swap the elements at 
        indices i and j. """
        if to_sort[j] <= pivot:
            i += 1
            to_sort[i], to_sort[j] = to_sort[j], to_sort[i]
    """ swap the pivot element with the element at index i + 1, 
    ensuring that all elements <= pivot are to its left, and all elements > pivot 
    are to its right. """
    to_sort[i + 1], to_sort[high] = to_sort[high], to_sort[i + 1]
    return i + 1

def quick_sort(to_sort, low, high):
    """ when the lower bound index >= upper bound index, 
    there are no more elements to sort. """
    if low < high:
        """ recursively sort the array by selecting a pivot via _partition, then sorting 
        the subarrays to the left and right of the pivot. """
        pivot = _partition(to_sort, low, high)
        quick_sort(to_sort, low, pivot - 1)
        quick_sort(to_sort, pivot + 1, high)
    return to_sort
