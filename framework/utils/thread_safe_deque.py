from collections import deque
import threading

class ThreadSafeDeque:
    def __init__(self):
        self._deque = deque()
        self._lock = threading.Lock()

    # 从队列右侧添加一个元素
    def append(self, item):
        with self._lock:
            self._deque.append(item)

    # 从队列左侧添加一个元素
    def appendleft(self, item):
        with self._lock:
            self._deque.appendleft(item)

    # 查看队列队首元素
    def peek_front(self):
        with self._lock:
            return self._deque[0]

    # 从队列左侧移除并返回一个元素
    def popleft(self):
        with self._lock:
            return self._deque.popleft()

    # 从队列右侧移除并返回一个元素
    def pop(self):
        with self._lock:
            return self._deque.pop()

    # 检查队列是否为空
    def empty(self):
        with self._lock:
            return len(self._deque) == 0
    
    def __len__(self):
        with self._lock:
            return len(self._deque)

    def sort_priority(self):
        with self._lock:
            self._deque = deque(sorted(self._deque, key=lambda x: (x['priority'], x['start_time'])))
