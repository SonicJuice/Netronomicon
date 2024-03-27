import collections.abc


class OrderedSet(collections.abc.MutableSet):
  def __init__(self, iterable=None):
      """
      constructor for an ordered set, initalising a doubly linked list
      RETURNS: None
      """
      self.end = [] 
      self.end += [None, self.end, self.end]
      self.map = {}
      self._key_parts = set()
      if iterable is not None:
          self |= iterable

  def __len__(self):
      """
      yield the number of map items 
      RETURNS: int
      """
      return len(self.map)

  def __contains__(self, key):
      """
      check if a 'key' is in '_key_parts' by searching for it in 'map'
      RETURNS: bool
      """
      return key in self.map

  def add(self, key):
      """
      add a new 'key' to 'map' and update the doubly linked list to maintain the order. If 'key' is a tuple or another type
      that supports indexing, add the first element of the 'key' to '_keyParts'
      RETURNS: None
      """
      if key not in self.map:
          end = self.end
          curr = end[1]
          curr[2] = end[1] = self.map[key] = [key, curr, end]
          try: 
              self._key_parts.add(key[0])
          except TypeError:
              pass

  def discard(self, key):
      """
      remove a 'key' from 'map' and update the doubly linked list
      RETURNS: None
      """
      if key in self.map:        
          key, prev, next_ = self.map.pop(key)
          prev[2] = next_
          next_[1] = prev
          try: 
              self._key_parts.remove(key[0])
          except (KeyError, TypeError):
              pass

  def __iter__(self):
      """
      traverse the doubly linked list in insertion order starting from the beginning and yields each element.
      RETURNS: None
      """
      end = self.end
      curr = end[2]
      while curr is not end:
          yield curr[0]
          curr = curr[2]

  def pop(self, last=True):
      """
      removes and returns the last/first element from '_key_parts'
      RETURNS: None
      """
      if not self:
          raise KeyError("Set is empty.")
      key = self.end[1][0] if last else self.end[2][0]
      self.discard(key)
      return key

  def __repr__(self):
      """
      string representation of '_key_parts'
      RETURNS: string
      """
      if not self:
          return f"{self.__class__.__name__}()"
      return f"{self.__class__.__name__}({list(self)})"

  def contains_url(self, url):
      """
      check for a URL in '_key_parts'
      RETURNS: bool
      """
      return url in self._key_parts
