def levenshtein_distance(token1, token2): 
    """ 
    calculates minimum number of single-character edits to convert one string 
    into another 
    RETURNS: int 
    """ 

    len_token1 = len(token1) 
    len_token2 = len(token2) 

# only need the previous row values are necessary for computation 

    if len_token1 > len_token2: 
        token1, token2 = token2, token1 
        len_token1, len_token2 = len_token2, len_token1

    distances = list(range(len_token1 + 1)) 

    for j in range(1, len_token2 + 1): 
        prev_diagonal = distances[0] # current value of distance_vector[0] 
        distances[0] = j # update to the current position in token2 

        for i in range(1, len_token1 + 1):	 
            current_diagonal = distances[i] 
            if token1[i - 1] == token2[j - 1]: # if the current characters from tokens 1 and 2 are the same  
                distances[i] = prev_diagonal 
            else: 
                distances[i] = 1 + min(distances[i - 1], distances[i], prev_diagonal) # update based on which one is the minimum value 
                prev_diagonal = current_diagonal 

    return distances[len_token1] # represents final Levenshtein distance
