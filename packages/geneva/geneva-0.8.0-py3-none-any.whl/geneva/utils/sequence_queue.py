from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(order=True)
class _QueueItem(Generic[T]):
    position: int
    size: int
    item: T = field(compare=False)


class SequenceQueue(Generic[T]):
    """A queue that maintains order based on sequence positions.

    Items can be inserted with their position and size, and the queue will maintain
    them in order. The pop() method will only return an item if the next
    expected position is available. When an item is popped, the next position
    advances by the item's size.

    This only works if the sequence covers the entire range of positions
    without any gaps.  If there are gaps then the queue will never emit an
    item and just fill up.

    Example:
        >>> q = SequenceQueue[str]()
        >>> q.put(1, 2, "second")  # position 2, size 2
        >>> q.put(0, 1, "first")   # position 0, size 2
        >>> q.put(3, 1, "third")   # position 3, size 1
        >>> q.pop()  # Returns "first" (advances position by 1)
        >>> q.pop()  # Returns "second" (advances position by 2)
        >>> q.pop()  # Returns "third" (advances position by 1)
    """

    def __init__(self) -> None:
        self._heap = []
        self._next_position = 0

    def put(self, position: int, size: int, item: T) -> None:
        """Insert an item with its position and size into the queue.

        Args:
            position: The sequence position of the item
            size: The size of the item (how much to advance next_position)
            item: The item to insert
        """
        heappush(self._heap, _QueueItem(position, size, item))

    def pop(self) -> T | None:
        """Pop the next item in sequence if available.

        Returns:
            The next item in sequence if available, None otherwise.
            An item is only returned if it matches the next expected position.
            When an item is popped, next_position advances by the item's size.
        """
        if not self._heap:
            return None

        next_item = self._heap[0]
        if next_item.position == self._next_position:
            heappop(self._heap)
            self._next_position += next_item.size
            return next_item.item
        return None

    def peek(self) -> T | None:
        """Peek at the next item in sequence without removing it.

        Returns:
            The next item in sequence if available and ready, None otherwise.
        """
        if not self._heap:
            return None

        next_item = self._heap[0]
        if next_item.position == self._next_position:
            return next_item.item
        return None

    def is_empty(self) -> bool:
        """Check if the queue is empty.

        Returns:
            True if the queue is empty, False otherwise.
        """
        return len(self._heap) == 0 or self._heap[0].position > self._next_position

    def next_position(self) -> int:
        """Get the next expected position.

        Returns:
            The next position that will be returned by pop()
        """
        return self._next_position
