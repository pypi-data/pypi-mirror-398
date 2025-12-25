import heapq
from typing import Any, List, Iterable

class TopKSolver:
    """
    A wrapper around heapq to standardize "Keep Top K" logic.
    """
    def __init__(self, k: int, largest: bool = True):
        self.k = k
        self.largest = largest # True for K Largest, False for K Smallest
        self.heap = []

    def push(self, item: Any):
        """Push an item into the tracker, maintaining size K."""
        # If we want K Largest, we use a Min Heap of size K.
        # If a new item is larger than the smallest in heap, we swap.
        if self.largest:
            heapq.heappush(self.heap, item)
            if len(self.heap) > self.k:
                heapq.heappop(self.heap)
        else:
            # If we want K Smallest, we effectively need a Max Heap of size K.
            # Python only has Min Heap, so we invert values (assuming numbers) or use custom wrapper.
            # Simpler approach: Use Max Heap logic by inverting numbers if numeric.
            # For generic objects, this requires custom comparator. 
            # For simplicity here, assuming numeric input for 'Smallest' logic or relying on negations.
            heapq.heappush(self.heap, -item)
            if len(self.heap) > self.k:
                heapq.heappop(self.heap)

    def get_result(self) -> List[Any]:
        if not self.largest:
            return sorted([-x for x in self.heap])
        return sorted(self.heap)