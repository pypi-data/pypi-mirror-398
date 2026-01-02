import threading

class ThreadSafeList:
    def __init__(self):
        self._list = []
        self._lock = threading.Lock()

    def append(self, item):
        with self._lock:
            self._list.append(item)

    def remove(self, item):
        with self._lock:
            self._list.remove(item)

    def __contains__(self, item):
        with self._lock:
            return item in self._list

    def __getitem__(self, index):
        with self._lock:
            return self._list[index]

    def __setitem__(self, index, value):
        with self._lock:
            self._list[index] = value

    def __delitem__(self, index):
        with self._lock:
            del self._list[index]

    def __iter__(self):
        with self._lock:
            return iter(self._list.copy())

    def __len__(self):
        with self._lock:
            return len(self._list)

    def insert(self, index, item):
        with self._lock:
            self._list.insert(index, item)
    
    def to_list(self):
        with self._lock:
            return list(self._list)
    
    def __str__(self) -> str:
        with self._lock:
            return str(self._list)
    
    def __repr__(self) -> str:
        with self._lock:
            return repr(self._list)