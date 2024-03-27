from collections import deque


class _DawgNode: 
    def __init__(self): 
        """ 
        initialises a DAWG node with a word and children 
        RETURNS: None 
        """ 
        self.word = None 
        self.original_key = None 
        self.children = {} 
        self.count = 0 

    def __getitem__(self, key):
        return self.children[key]

    def __repr__(self):
        return f"{list(self.children.keys())}, {self.word}"

    @property 
    def value(self): 
        """ 
        returns a DAWG node's value as either its original key or word 
        RETURNS: string 
        """ 
        return self.original_key or self.word 

    def insert_dawg_node(self, word, normalised_word, add_word=True, original_key=None, count=0, insert_count=True): 
        """
        inserts a word into the DAWG 
        RETURNS: string 
        """ 
        node = self 
        for letter in normalised_word: 
            if letter not in node.children: 
                node.children[letter] = _DawgNode() 
            node = node.children[letter] 
        if add_word: 
            node.word = word 
            node.original_key = original_key 
            if insert_count: 
                node.count = int(count) # converts any str to int 
        return node 

    def get_descendant_nodes(self, size, should_traverse=True, full_stop_words=None, insert_count=True): 
        """ 
        gets descendant nodes of a DAWG node 
        RETURNS: None 
        """ 
        if insert_count is True: 
            size = float('inf') 

        que = deque() 
        unique_nodes = {self} 
        found_nodes_set = set() 
        full_stop_words = full_stop_words if full_stop_words else set() 

        for letter, child_node in self.children.items(): 
            if child_node not in unique_nodes: 
                unique_nodes.add(child_node) 
                que.append((letter, child_node)) 
                
        while que: 
            letter, child_node = que.popleft() 
            child_value = child_node.value 
            if child_value: 
                if child_value in full_stop_words: 
                    should_traverse = False 
                if child_value not in found_nodes_set: 
                    found_nodes_set.add(child_value) 
                    yield child_node 
                    if len(found_nodes_set) > size: 
                        break 

            if should_traverse: 
                for letter, grand_child_node in child_node.children.items(): 
                    if grand_child_node not in unique_nodes: 
                        unique_nodes.add(grand_child_node) 
                        que.append((letter, grand_child_node))  

    def get_descendant_words(self, size, should_traverse=True, full_stop_words=None, insert_count=True): 
        """ 
        gets descendant words of a DAWG node 
        RETURNS: iterator 
        """ 
        found_nodes_gen = self.get_descendant_nodes(size, should_traverse=should_traverse, full_stop_words=full_stop_words, \ 
        insert_count=insert_count) 
        if insert_count is True: 
            found_nodes = sorted(found_nodes_gen, key=lambda node: node.count, reverse=True)[:size + 1] 
        else: 
            found_nodes = islice(found_nodes_gen, size) 
        return map(lambda word: word.value, found_nodes) 
