import random
import bisect
from typing import List, Iterator, Any

class SamplingSolver:
    """
    Engine for Probabilistic Sampling.
    Covers Reservoir Sampling (Streaming) and Weighted Random Pick.
    """
    
    def reservoir_sampling(self, stream: Iterator[Any], k: int) -> List[Any]:
        """
        Selects k items from a stream of unknown length with uniform probability.
        """
        reservoir = []
        for i, item in enumerate(stream):
            if i < k:
                reservoir.append(item)
            else:
                # Randomly replace items in reservoir with decreasing probability
                # Pick index j from 0 to i
                j = random.randint(0, i)
                if j < k:
                    reservoir[j] = item
        return reservoir

    class WeightedPicker:
        """
        Class for selecting an index based on weights (w[i] / sum(w)).
        Efficient for multiple picks: O(N) init, O(log N) pick.
        """
        def __init__(self, weights: List[int]):
            self.prefix_sums = []
            current_sum = 0
            for w in weights:
                current_sum += w
                self.prefix_sums.append(current_sum)
            self.total_sum = current_sum

        def pick_index(self) -> int:
            target = random.random() * self.total_sum
            # Binary search for the first prefix sum > target
            # bisect_right returns insertion point to maintain order
            # Usually equivalent to finding the range target falls into
            idx = bisect.bisect_left(self.prefix_sums, target)
            return idx