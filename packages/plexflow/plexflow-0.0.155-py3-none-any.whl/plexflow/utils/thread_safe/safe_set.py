import threading

class ThreadSafeSet:
    def __init__(self):
        self._set = set()
        self._lock = threading.Lock()

    def add(self, item):
        with self._lock:
            self._set.add(item)

    def remove(self, item):
        with self._lock:
            self._set.remove(item)

    def __contains__(self, item):
        with self._lock:
            return item in self._set

    def __iter__(self):
        with self._lock:
            return iter(self._set.copy())

    def __len__(self):
        with self._lock:
            return len(self._set)

    def update(self, items):
        with self._lock:
            self._set.update(items)

    def difference(self, other_set):
        with self._lock:
            if isinstance(other_set, ThreadSafeSet):
                other_set = other_set._set
            result = self._set.difference(other_set)
        return ThreadSafeSet.from_set(result)

    def intersection(self, other_set):
        with self._lock:
            if isinstance(other_set, ThreadSafeSet):
                other_set = other_set._set
            result = self._set.intersection(other_set)
        return ThreadSafeSet.from_set(result)

    def union(self, other_set):
        with self._lock:
            if isinstance(other_set, ThreadSafeSet):
                other_set = other_set._set
            result = self._set.union(other_set)
        return ThreadSafeSet.from_set(result)
    
    def to_set(self):
        with self._lock:
            return set(self._set)
    
    def __str__(self) -> str:
        with self._lock:
            return str(self._set)
    
    def __repr__(self) -> str:
        with self._lock:
            return repr(self._set)
    
    @classmethod
    def from_set(cls, input_set):
        instance = cls()
        instance._set = input_set
        return instance