import threading
from collections import deque
from time import monotonic as time


class Empty(Exception):
    """
    signifies that the queue is currently empty, and no items can be dequeued
    """
    pass


class Full(Exception):
    """
    signifies an attempted enqueuing when the queue has reached its maximum capacity.
    """
    pass


class ShutDown(Exception):
    """
    indicates that queue operations have been stopped, notifying threads that further operations are not allowed.
    """


class Queue:
    def __init__(self, max_size=0):
        """
        constructor for Queue data structure
        RETURNS: None
        """
        self.max_size = max_size 
        self._init(max_size)
        self.mutual_exclusion = threading.Lock() # allows only one thread (queue modifying-operation) to acquire the lock at any given time
        self.not_empty = threading.Condition(self.mutual_exclusion) # notifies threads to retrieve items from the Queue
        self.not_full = threading.Condition(self.mutual_exclusion) # notifies threads to add items to the queue
        self.unfinished_tasks = 0 # tracks no. of unfinished tasks
        self.is_shutdown = False # shutdown state

    def qsize(self):
        """
        retrieves approximate size of the queue
        RETURNS: function call
        """
        with self.mutual_exclusion:
            return self._qsize()

    def enqueue(self, item, block=True, timeout=None):
        """
        puts an item into the queue. If 'block' is true and 'timeout' is None, block if necessary until a free slot
        is available. Then, block at most 'timeout' seconds and raise Full' if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot is immediately available;
        else, raise Full (ignoring 'timeout'). Raises ShutDown if the queue has been shut down.
        RETURNS: None
        """
        
        with self.not_full:
            if self.is_shutdown:
               raise ShutDown
            if self.max_size > 0:
                   if not block:
                       if self._qsize() >= self.max_size:
                           raise Full
                   elif timeout is None:
                       while self._qsize() >= self.max_size:
                           self.not_full.wait()
                           if self.is_shutdown:
                                raise ShutDown
                   else:
                       endtime = time() + timeout
                       while self._qsize() >= self.max_size:
                           remaining = endtime - time()
                           if remaining <= 0.0:
                               raise Full
                           self.not_full.wait(remaining)
                           if self.is_shutdown:
                               raise ShutDown
            self._enqueue(item)
            self.unfinished_tasks += 1
            self.not_empty.notify() # 'wakes up' any thread waiting for the queue to become non-empty

    def dequeue(self, block=True, timeout=None):
        """
        Remove and return an item from the queue. Raises ShutDown if the queue has been shut down and is empty,
        or if it has been shut down immediately.
        RETURNS: item
        """
        with self.not_empty:
           if self.is_shutdown and not self._qsize():
               raise ShutDown
           if not block:
               if not self._qsize():
                    raise Empty
           elif timeout is None:
               while not self._qsize():
                   self.not_empty.wait()
                   if self.is_shutdown and not self._qsize():
                       raise ShutDown
           else:
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                       raise Empty
                    self.not_empty.wait(remaining)
                    if self.is_shutdown and not self._qsize():
                       raise ShutDown
           item = self._dequeue()
           self.not_full.notify() # 'wakes up' any thread waiting for the queue to become non-full
           return item

    def shutdown(self, immediate=False):
        """
        shuts down the queue operations. If 'immediate' is False, wait for all currently running tasks to complete
        before shutting it. If it's True, immediately stop the queue operations, discarding any pending tasks.
        RETURNS: None
        """
        with self.mutual_exclusion:
           self.is_shutdown = True
           if immediate:
               while self._qsize():
                   self._dequeue()
                   if self.unfinished_tasks > 0:
                       self.unfinished_tasks -= 1
               self.not_empty.notify_all()
           self.not_full.notify_all()

    def _init(self, max_size):
        """
        creates a double-ended queue instance using 'max_size'
        RETURNS: None
        """
        self.queue = deque()

    def _qsize(self):
        """
        yields number of items in the queue
        RETURNS: None
        """
        return len(self.queue)

    def _enqueue(self, item):
        """
        adds an item to the queue's rear
        RETURNS: None
        """
        self.queue.append(item)

    def _dequeue(self):
        """
        removes and returns the first item from the queue
        RETURNS: item
        """
        return self.queue.popleft()
