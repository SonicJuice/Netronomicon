def partition(to_sort, low, high):  
    """  
    determines where pivot is in list  
    RETURNS: int  
    """  

    pivot = to_sort[high] #initial pivot  
    i = low - 1 #pointer  

    for j in range(low, high): #compare all elements with pivot 
        if to_sort[j] <= pivot:  
            i += 1  
            (to_sort[i], to_sort[j]) = (to_sort[j], to_sort[i]) #swap elements  

    (to_sort[i + 1], to_sort[high]) = (to_sort[high], to_sort[i + 1]) #then swap pivot element  

    return i + 1 #end position  

 

def quick_sort(to_sort, low, high):  
    """  
    recursive quicksort  
    RETURNS: list  
    """

    if low < high:  

        pivot = partition(to_sort, low, high)  
        quick_sort(to_sort, low, pivot - 1) #left recursive call  
        quick_sort(to_sort, pivot + 1, high) #right recursive call  

    return to_sort
