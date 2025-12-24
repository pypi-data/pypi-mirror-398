# Stack abstraction
from typing import Optional


class Node:
    def __init__(self, value):
        self.value = value
        self.next: Optional[Node] = None


class Stack:

    def __init__(self):
        self._head = None
        self._size = 0

    # Get the current size of the stack
    def size(self):
        return self._size

    # Check if the stack is empty
    def empty(self):
        return self._size == 0

    def top(self):
        if self.empty() or self._head is None:
            return None

        return self._head.value

    def push(self, value):
        node = Node(value)
        node.next = self._head
        self._head = node
        self._size += 1

    def pop(self):
        if self.empty() or self._head is None:
            raise Exception("Popping from an empty stack")
        top_element = self._head
        self._head = top_element.next
        self._size -= 1
        return top_element.value
