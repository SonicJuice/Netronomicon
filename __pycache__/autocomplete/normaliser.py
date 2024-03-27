import string 


class Normaliser:
    def __init__(self, valid_chars_for_string=None, valid_chars_for_integer=None): 
        """
        initialises a Normaliser with sets of valid characters 
        RETURNS: None 
        """ 
        self.valid_chars_for_string = frozenset(valid_chars_for_string or string.ascii_letters.lower()) 
        self.valid_chars_for_integer = frozenset(valid_chars_for_integer or string.digits) 
        self.valid_chars_for_node_name = frozenset({' ', '-', ':', '_'}).union(self.valid_chars_for_string, self.valid_chars_for_integer) 
        self._normalised_lfu_cache = LFUCache(2048) 
        self.max_word_length = 40

    def normalise_node_name(self, name, extra_chars=None):
        """ 
        removes invalid characters from a node's name, before caching it 
        RETURNS: string 
        """ 
        if name is None: 
            return '' 
        name = name[:self.max_word_length] 
        key = name if extra_chars is None else f"{name}{extra_chars}" 
        result = self._normalised_lfu_cache.get_value(key) 
        if result == -1: 
            result = self._get_normalised_node_name(name, extra_chars=extra_chars) 
            self._normalised_lfu_cache.set_value(key, result) 
        return result 

    def _remove_invalid_chars(self, x): 
        """ 
        helper method removes invalid characters 
        RETURNS: string 
        """ 
        result = x in self.valid_chars_for_node_name 
        if x == '-' == self.prev_x: 
            result = False 
        self.prev_x = x 
        return result 

    def remove_any_special_character(self, name): 
        """ 
        remove any special characters from a node's name 
        RETURNS: string 
        """ 
        if name is None: 
            return '' 
        name = name.lower()[:self.max_word_length] 
        self.prev_x = '' 
        return ''.join(filter(self._remove_invalid_chars, name)).strip() 

    def _get_normalised_node_name(self, name, extra_chars=None): 
        """ 
        helper method returns the normalised form of the node's name 
        RETURNS: string 
        """ 
        name = name.lower() 
        result = [] 

        for i, char in enumerate(name): 
            if char in self.valid_chars_for_node_name or (extra_chars and char in extra_chars): 
                if char == '-' and name[i - 1] == '-': 
                    continue 
                if char in self.valid_chars_for_integer and name[i - 1] in self.valid_chars_for_string or \ 
                char in self.valid_chars_for_string and name[i - 1] in self.valid_chars_for_integer: 
                    result.append(' ') 
                result.append(char) 
        return ''.join(result).strip()
