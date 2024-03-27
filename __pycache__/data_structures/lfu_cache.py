from threading import lock


class CacheNode:
    def __init__(self, key, value):
        """
        initialises a CacheNode with a key and value
        RETURNS: None
        """
        self.key = key
        self.value = value
        self.freq_node = None
        self.pre = None # previous CacheNode
        self.nxt = None # next CacheNode

    def remove_cache_node(self):
        """
        removes the current CacheNode from its FreqNode's linked list
        RETURNS: None
        """
        if self.freq_node.cache_head == self.freq_node.cache_tail:
            self.freq_node.cache_head = self.freq_node.cache_tail = None
        elif self.freq_node.cache_head == self:
            self.nxt.pre = None
            self.freq_node.cache_head = self.nxt
        elif self.freq_node.cache_tail == self:
            self.pre.nxt = None
            self.freq_node.cache_tail = self.pre
        else:
            self.pre.nxt = self.nxt
            self.nxt.pre = self.pre

        self.pre = self.nxt = self.freq_node = None


class FreqNode:
    def __init__(self, freq):
        """
        initialises a doubly linked list
        RETURNS: None
        """
        self.freq = freq
        self.pre = None # previous FreqNode
        self.nxt = None # next FreqNode
        self.cache_head = None # CacheNode head under this linked list
        self.cache_tail = None # CacheNode tail under this linked list

    def count_caches(self):
        """
        counts the number of caches in the currententent FreqNode
        RETURNS: integer/string
        """

        if self.cache_head is None and self.cache_tail is None:
          return 0
        elif self.cache_head == self.cache_tail:
          return 1
        else:
          return '2+'

    def remove_freq_node(self):
        """
        removes the current FreqNode from the linked list
        RETURNS: pointer
        """
        if self.pre:
            self.pre.nxt = self.nxt
        if self.nxt:
            self.nxt.pre = self.pre

        pre, nxt = self.pre, self.nxt
        self.pre = self.nxt = self.cache_head = self.cache_tail = None

        return pre, nxt

    def pop_head_cache(self):
        """
        removes and returns the CacheNode head of the linked list
        RETURNS: pointer
        """
        if not self.cache_head and not self.cache_tail:
            return None
        elif self.cache_head == self.cache_tail:
            cache_head = self.cache_head
            self.cache_head = self.cache_tail = None
            return cache_head
        else:
            cache_head = self.cache_head
            self.cache_head.nxt.pre = None
            self.cache_head = self.cache_head.nxt
            return cache_head

    def append_cache_to_tail(self, cache_node):
        """
        appends cache node to linked list's tail
        RETURNS: None
        """
        cache_node.freq_node = self
        if not self.cache_head and not self.cache_tail:
            self.cache_head = self.cache_tail = cache_node
        else:
            cache_node.pre = self.cache_tail
            cache_node.nxt = None
            self.cache_tail.nxt = cache_node
            self.cache_tail = cache_node

    def insert_after_current_freq_node(self, freq_node):
        """
        inserts a FreqNode after the current one
        RETURNS: None
        """
        freq_node.pre = self
        freq_node.nxt = self.nxt
        if self.nxt:
            self.nxt.pre = freq_node
        self.nxt = freq_node

    def insert_before_current_freq_node(self, freq_node):
        """
        inserts a FreqNode before the current one
        RETURNS: None
        """
        if self.pre:
            self.pre.nxt = freq_node
        freq_node.pre = self.pre
        freq_node.nxt = self
        self.pre = freq_node


class LFUCache:
    def __init__(self, capacity):
        """
        initialises a least frequently used (LFU) cache with a given capacity and the head of the frequency linked list
        RETURNS: None
        """
        self.cache = {}
        self.capacity = capacity
        self.freq_link_head = None
        self.lock = Lock()

    def get_value(self, key):
        """
        retrieves the value associated with a given key from the cache, updating the frequency of the CacheNode and linked list
        RETURNS: string/integer
        """
        with self.lock:
            if key in self.cache:
                cache_node = self.cache[key]
                freq_node = cache_node.freq_node
                value = cache_node.value
                self.move_forward(cache_node, freq_node)
                return value
            else:
                return -1

    def set_value(self, key, value):
        """
        sets the value associated with the given key in the cache
        RETURNS: None
        """
        with self.lock:
            if self.capacity <= 0:
                return -1
    
            if key not in self.cache:
                if len(self.cache) >= self.capacity:
                    self.dump_cache()
                    self.create_cache_node(key, value)
            else:
                cache_node = self.cache[key]
                freq_node = cache_node.freq_node
                cache_node.value = value
    
                self.move_forward(cache_node, freq_node)

    def move_forward(self, cache_node, freq_node):
        """
        moves a candidate node to the next FreqNode in the linked list
        RETURNS: None
        """
        if not freq_node.nxt or freq_node.nxt.freq != freq_node.freq + 1:
            target_freq_node = FreqNode(freq_node.freq + 1)
            target_empty = True
        else:
            target_freq_node = freq_node.nxt
            target_empty = False

        cache_node.remove_cache_node()
        target_freq_node.append_cache_to_tail(cache_node)

        if target_empty:
            freq_node.insert_after_currententent_freq_node(target_freq_node)

        if freq_node.count_caches() == 0:
            if self.freq_link_head == freq_node:
                self.freq_link_head = target_freq_node

            freq_node.remove_freq_node()

    def dump_cache(self):
        """
        removes the least frequently used CacheNode from the cache
        RETURNS: None
        """

        head_freq_node = self.freq_link_head
        self.cache.pop(head_freq_node.cache_head.key)
        head_freq_node.pop_head_cache()

        if head_freq_node.count_caches() == 0:
            self.freq_link_head = head_freq_node.nxt
            head_freq_node.remove_freq_node()

    def create_cache_node(self, key, value):
        """ 
        creates a new CacheNode and add it to the cache
        RETURNS: None
        """
        cache_node = CacheNode(key, value)
        self.cache[key] = cache_node

        if not self.freq_link_head or self.freq_link_head.freq != 0:/
            new_freq_node = FreqNode(0)
            new_freq_node.append_cache_to_tail(cache_node)

            if self.freq_link_head:
                self.freq_link_head.insert_before_current_freq_node(new_freq_node)

            self.freq_link_head = new_freq_node
        else:
            self.freq_link_head.append_cache_to_tail(cache_node)
