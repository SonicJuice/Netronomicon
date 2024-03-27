import string 
from collections import defaultdict, deque 
from threading import Lock


class AutoComplete: 
    def __init__(self, words, synonyms=None, full_stop_words=None, valid_chars_for_string=None, valid_chars_for_integer=None): 
        """ 
        initialises an AutoComplete with a list of words and synonyms 
        RETURNS: None 
        """ 
        self._lock = Lock()
        self._dawg = None
        self._raw_synonyms = synonyms or {} 
        self._lfu_cache = LFUCache(2048) 
        self._clean_synonyms, self._partial_synonyms = self._get_clean_and_partial_synonyms() 
        self._reverse_synonyms = self._get_reverse_synonyms(self._clean_synonyms) 
        self._full_stop_words = set(full_stop_words) if full_stop_words else None 
        self.words = words 
        self.original_key = 'original_key' 
        self.inf = float('inf') 
        self.prefix_autofill_part_condition_suffix = ' ' 
        
        self.normaliser = Normaliser( 
        valid_chars_for_string=valid_chars_for_string, 
        valid_chars_for_integer=valid_chars_for_integer) 
        self._update_words_with_partial_synonyms() 
        self._populate_dawg() 

    def _get_clean_and_partial_synonyms(self): 
        """ 
        helper method retrieves clean and partial synonyms. Synonyms are words that should produce the same result 
        RETURNS: dictionary 
        """ 
        clean_synonyms = {} # phrases that share little or no words 
        partial_synonyms = {} # one phrase is a substring of another 
        
        for key, synonyms in self._raw_synonyms.items(): 
            key = key.strip().lower() 
            _clean, _partial = [], [] 
            for syn in synonyms: 
                syn = syn.strip().lower() 
                if key.startswith(syn):
                    _partial.append(syn)
                else:
                    _clean.append(syn)
            if _clean:
                clean_synonyms[key] = _clean
            if _partial:
                partial_synonyms[key] = _partial

        return clean_synonyms, partial_synonyms

    def _get_reverse_synonyms(self, synonyms): 
        """ 
        helper method retrieves reverse synonyms to be sorted 
        RETURNS: dictionary 
        """ 
        result = {} 
        if synonyms: 
            for key, value in synonyms.items(): 
                for item in value: 
                    result[item] = key 
        return result 

    def _get_partial_synonyms_to_words(self): 
        new_words = {} 
        for key, value in self.words.items(): 
            try: 
                value = value.copy() 
            except Exception: 
                new_value = value._asdict() 
                new_value[self.original_key] = key 
                value = type(value)(**new_value) 
            else: 
                value[self.original_key] = key 
            for syn_key, syns in self._partial_synonyms.items(): 
                if key.startswith(syn_key): 
                    for syn in syns: 
                        new_key = key.replace(syn_key, syn) 
                        new_words[new_key] = value 

        return new_words 

    def _populate_dawg(self): 
        """ 
        inserts words and their synonyms into the DAWG 
        RETURNS: None 
        """ 
        if not self._dawg: 
            with self._lock:
                self._dawg = _DawgNode() 
                for word, value in self.words.items(): 
                    original_key = value.get(self.original_key) 
                    count = value.get('count', 0) 
                    leaf_node = self.insert_word_branch(word, original_key=original_key, count=count) 
                    
                    if leaf_node and self._clean_synonyms: 
                        synonyms = self._clean_synonyms.get(word, []) 
                        for synonym in synonyms:
                            self.insert_word_branch(synonym, leaf_node=leaf_node, add_word=False, count=count)

    def insert_word_callback(self, word): 
        """ 
        callback function after a word is inserted 
        RETURNS: None 
        """ 
        pass 

    def insert_word_branch(self, word, leaf_node=None, add_word=True, original_key=None, count=0): 
        """ 
        inserts a word into the DAWG and updates its present leaf node 
        RETURNS: leaf node 
        """ 
        normalised_word = self.normaliser.normalise_node_name(word) 
        if not normalised_word: 
            return 
        last_char = normalised_word[-1] 

        if leaf_node: 
            temp_leaf_node = self._dawg.insert_dawg_node(word=word, normalised_word=normalised_word[:-1], \
            add_word=add_word, original_key=original_key, count=count, insert_count=True) 
            if temp_leaf_node.children and last_char in temp_leaf_node.children: 
                temp_leaf_node.children[last_char].word = leaf_node.word 
            else: 
                temp_leaf_node.children[last_char] = leaf_node # merge into leaf node if it doesn't have children 

        else: 
            leaf_node = self._dawg.insert_dawg_node(word=word, normalised_word=normalised_word, \ 
            original_key=original_key, count=count, insert_count=True) 
        self.insert_word_callback(word) 
        return leaf_node 

    def _sort_words(self, word, max_cost, size): 
        """ 
        helper method to sort results based on a given word's size and cost in terms of Levenshtein distance 
        RETURNS: generator 
        """ 
        output_keys_set = set()
        results, find_steps = self._find(word, max_cost, size)
        results_keys = list(results.keys())
        results_keys.sort()
        for key in results_keys:
            for output_items in results[key]:
                for i, item in enumerate(output_items):
                    reversed_item = self._reverse_synonyms.get(item)
                    if reversed_item:
                        output_items[i] = reversed_item
                    elif item not in self.words:
                        output_items[i] = item
                output_items_str = '__'.join(output_items) 
                if output_items_str not in output_keys_set:             
                    output_keys_set.add(output_items_str) 
                    yield output_items 
                    if len(output_keys_set) >= size: 
                        return  

    def search_for_similar_words(self, word, max_cost=2, size=5): 
        """ 
        searches for words similar to the given word within a Levenshtein distance and size. 
        RETURNS: list 
        """ 
        word = self.normaliser.normalise_node_name(word) 
        if not word: 
            return [] 
        key = f'{word}-{max_cost}-{size}' 
        result = self._lfu_cache.get_value(key)
        if result == -1: 
            result = list(self._sort_words(word, max_cost, size)) 
            self._lfu_cache.set_value(key, result) 
        return result 

    def _is_stop_word_condition(self, matched_words, matched_prefix_of_last_word): 
        """ 
        helper method checks if the stop word condition is met 
        RETURNS: bool 
        """ 
        return (self._full_stop_words and matched_words and matched_words[-1] in self._full_stop_words and not matched_prefix_of_last_word) 

    def _find_words(self, word, max_cost, size, call_count=0): 
        """ 
        helper method finds similar words via fuzzy string matching 
        RETURNS: tuple 
        """ 
        results = defaultdict(list) 
        fuzzy_matches = defaultdict(list) 
        rest_of_results = {} 
        fuzzy_matches_len = 0 
        fuzzy_min_distance = min_distance = self.inf 
        matched_prefix_of_last_word, rest_of_word, new_node, matched_words = self._prefix_autofill(word=word) 
        last_word = matched_prefix_of_last_word + rest_of_word 

        if matched_words: 
            results[0] = [matched_words.copy()]
            min_distance = 0 
            if self._is_stop_word_condition(matched_words, matched_prefix_of_last_word): 
                find_steps = [FindStep.start] 
                return results, find_steps 

        if len(rest_of_word) < 3: 
            find_steps = [FindStep.descendant_only] 
            self._add_descendant_words_to_results(node=new_node, size=size, matched_words=matched_words, results=results, distance=1) 
        else: 
            find_steps = [FindStep.fuzzy_try] 
            word_chunks = deque(filter(lambda x: x, last_word.split(' '))) 
            new_word = word_chunks.popleft() 

            while len(new_word) < 5 and word_chunks:
                new_word = f'{new_word} {word_chunks.popleft()}'
            fuzzy_rest_of_word = ' '.join(word_chunks)

            for _word in self.words: 
                if abs(len(_word) - len(new_word)) > max_cost: 
                    continue 

                dist = levenshtein_distance(new_word, _word) 
                if dist < max_cost: 
                    fuzzy_matches_len += 1 
                    _value = self.words[_word].get(self.original_key, _word) 
                    fuzzy_matches[dist].append(_value) 
                    fuzzy_min_distance = min(fuzzy_min_distance, dist) 
                    
                    if fuzzy_matches_len >= size or dist < 2: 
                        break 

            if fuzzy_matches_len: 
                find_steps.append(FindStep.fuzzy_found) 
                if fuzzy_rest_of_word: 
                    call_count += 1 
                    if call_count < 2: 
                        rest_of_results, rest_find_steps = self._find_words(word=fuzzy_rest_of_word, max_cost=max_cost, \ 
                        size=size, call_count=call_count) 
                        find_steps.append({FindStep.rest_of_fuzzy: rest_find_steps}) 

                for _word in fuzzy_matches[fuzzy_min_distance]: 
                    if rest_of_results: 
                        rest_of_results_min_key = min(rest_of_results.keys()) 
                        for _rest_of_matched_word in rest_of_results[rest_of_results_min_key]: 
                            results[fuzzy_min_distance].append(matched_words + [_word] + _rest_of_matched_word) 
                    else: 
                    results[fuzzy_min_distance].append(matched_words + [_word]) 
                    _matched_prefix_of_last_word_b, not_used_rest_of_word, fuzzy_new_node, _matched_words_b = self._prefix_autofill(word=_word) 
                    if self._is_stop_word_condition(matched_words=_matched_words_b, matched_prefix_of_last_word=_matched_prefix_of_last_word_b): 
                        break 
                    self._add_descendant_words_to_results(node=fuzzy_new_node, size=size, matched_words=matched_words, \ 
                    results=results, distance=fuzzy_min_distance) 

            if matched_words and not sum(map(len, results.values())) >= size: 
                find_steps.append(FindStep.not_enough_results_add_some_descandants) 
                total_min_distance = min(min_distance, fuzzy_min_distance) 
                self._add_descendant_words_to_results(node=new_node, size=size, matched_words=matched_words, results=results, \ 
                distance=total_min_distance+1) 

        return results, find_steps 

    def _prefix_autofill(self, word, node=None): 
        """ 
        helper method attempts to predict the rest of a word 
        RETURNS: tuple 
        """ 
        len_prev_rest_of_last_word = self.inf 
        matched_words = [] 
        matched_words_set = set()  

    def _add_words(words): 
        """ 
        helper method adds words to undergo prefix autofill 
        RETURNS: bool 
        """ 
        is_added = False 
        for word in words: 
            if word not in matched_words_set: 
                matched_words.append(word) 

matched_words_set.add(word) 

is_added = True 

return is_added 

 

matched_prefix_of_last_word, rest_of_word, node, matched_words_part, matched_condition_ever, matched_condition_in_branch = \ 
self._prefix_autofill_part(word, node) 

_add_words(matched_words_part) 

result = (matched_prefix_of_last_word, rest_of_word, node, matched_words) 

len_rest_of_last_word = len(rest_of_word) 

 

while len_rest_of_last_word and len_rest_of_last_word < len_prev_rest_of_last_word: 

 

word = matched_prefix_of_last_word + rest_of_word 

word = word.strip() 

len_prev_rest_of_last_word = len_rest_of_last_word 

matched_prefix_of_last_word, rest_of_word, node, matched_words_part, matched_condition_ever, matched_condition_in_branch = self._prefix_autofill_part(word, node=self._dawg, matched_condition_ever=matched_condition_ever, matched_condition_in_branch=matched_condition_in_branch) 

is_added = _add_words(matched_words_part) 

 

if is_added is False: 

break 

len_rest_of_last_word = len(rest_of_word) 

result = (matched_prefix_of_last_word, rest_of_word, node, matched_words) 

return result 

def prefix_autofill_part_condition(self, node): 
    pass 

def _add_to_matched_words(self, node, matched_words, matched_condition_in_branch, matched_condition_ever, matched_prefix_of_last_word): 
    """ 
    helper method verifies matched words 
    RETURNS: tuple 
    """ 
    if matched_words: 

last_matched_word = matched_words[-1].replace(self.prefix_autofill_part_condition_suffix, '') 

if node.value.startswith(last_matched_word): 

matched_words.pop() 

value = node.value 

if self.prefix_autofill_part_condition_suffix: 

if self._node_word_info_matches_condition(node, self.prefix_autofill_part_condition): 

matched_condition_in_branch = True 

if matched_condition_ever and matched_prefix_of_last_word: 

value = f"{matched_prefix_of_last_word}{self.prefix_autofill_part_condition_suffix}" 

matched_words.append(value) 

return matched_words, matched_condition_in_branch 

def _prefix_autofill_part(self, word, node=None, matched_condition_ever=False, matched_condition_in_branch=False): 
    """ 
    helper method builds a prefix by matching characters in the word with the nodes 
    RETURNS: tuple 
    """ 
    node = node or self._dawg 
    que = deque(word) 
    matched_prefix_of_last_word = '' 
    matched_words = [] 
    nodes_that_words_were_extracted = set() 
    
    while que: 

char = que.popleft()  

if node.children: 

if char not in node.children: 

space_child = node.children.get(' ') 

if space_child and char in space_child.children: 

node = space_child 

else: 

que.appendleft(char) 

break 

node = node.children[char] 

if char != ' ' or matched_prefix_of_last_word: 

matched_prefix_of_last_word += char 

if node.word: 

if que: 

next_char = que[0] 

if next_char != ' ': 

continue 

matched_words, matched_condition_in_branch = self._add_to_matched_words(node, matched_words, matched_condition_in_branch, matched_condition_ever, matched_prefix_of_last_word) 

nodes_that_words_were_extracted.add(node) 

matched_prefix_of_last_word = '' 

else:				 

if char == ' ' 

node = self._dawg 

if matched_condition_in_branch: 

matched_condition_ever = True 

else: 

que.appendleft(char) 

break 

if not que and node.word and node not in nodes_that_words_were_extracted: 

matched_words, matched_condition_in_branch = self._add_to_matched_words(node, matched_words, matched_condition_in_branch, \ 
matched_condition_ever, matched_prefix_of_last_word) 
matched_prefix_of_last_word = '' 
rest_of_word = "".join(que) 

if matched_condition_in_branch: 
    matched_condition_ever = True
    
return matched_prefix_of_last_word, rest_of_word, node, matched_words, matched_condition_ever, matched_condition_in_branch 

def _add_descendant_words_to_results(self, node, size, matched_words, results, distance, should_traverse=True): 
    """ 
    helper method adds descendant words to results 
    RETURNS: integer 
    """ 
    descendant_words = list(node.get_descendant_words(size, should_traverse, full_stop_words=self._full_stop_words)) 
    extended = _extend_and_repeat(matched_words, descendant_words) 
    if extended: 
        results[distance].extend(extended) 

    return distance 

def _node_word_info_matches_condition(self, node, condition): 
    """ 
    helper method checks if a node word satisfies a condition 
    RETURNS: bool 
    """ 
    _word = node.word 
    word_info = self.words.get(_word) 
    if word_info: 
        return condition(word_info) 
    else: 
        return False 

def get_all_descendant_words_for_condition(self, word, size, condition): 
    """ 
    returns all descendant words which satisfy a condition 
    RETURNS: list 
    """ 
    new_tokens = [] 
    matched_prefix_of_last_word, rest_of_word, node, matched_words_part, matched_condition_ever, \
    matched_condition_in_branch = self._prefix_autofill_part(word=word) 

if not rest_of_word and self._node_word_info_matches_condition(node, condition): 

found_nodes_gen = node.get_descendant_nodes(size, insert_count=True) 

for node in found_nodes_gen: 

if self._node_word_info_matches_condition(node, condition): 

new_tokens.append(node.word) 

return new_tokens 

def update_count_of_word(self, word, count=None, offset=None): 
    """ 
    updates the count of a node in the DAWG 
    RETURNS: integer 
    """ 
    matched_prefix_of_last_word, rest_of_word, node, matched_words_part, matched_condition_ever, \ 
    matched_condition_in_branch = self._prefix_autofill_part(word=word) 
    if offset: 
        node.count += offset 
    elif count: 
        node.count = count 
    return node.count
