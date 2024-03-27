from enum import Enum


@dataclass 
class FindStep(Enum): 
    """ 
    data class to track the process of finding a similar word via fuzzy (approximate) string matching 
    """ 
    start = 0 # begin finding 
    descendant_only = 1 # consider only descendant nodes 
    fuzzy_try = 2 # attempt to find a fuzzy match 
    fuzzy_found = 3 # fuzzy matches are found 
    rest_of_fuzzy = 4 # attempt to find a fuzzy match again 
    not_enough_results_add_some_descandants = 5 # not enough results found, so consider additional descendants 
    
def _extend_and_repeat(list1, list2): 
    """ 
    helper method to traverse descendant words 
    RETURNS: list 
    """ 
    if not list1: 
        return [[i] for i in list2] 
    result = [] 
    for item in list2: 
        if item not in list1: 
            list1_copy = list1.copy() 

        if item.startswith(list1_copy[-1]): 
            list1_copy.pop() 
        list1_copy.append(item) 
        result.append(list1_copy) 
    return result 
