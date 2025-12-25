from abc import ABC, abstractmethod
from typing import Any, List

class BacktrackingSolver(ABC):
    """
    Engine for combinatorial search (Permutations, Subsets, Combination Sum).
    Manages the recursion stack and state restoration automatically.
    """

    def __init__(self):
        self.results = []

    def solve(self, nums: List[Any]) -> List[List[Any]]:
        self.nums = nums
        self.results = []
        self._backtrack(start_index=0, current_path=[])
        return self.results

    def _backtrack(self, start_index: int, current_path: List[Any]):
        # 1. Check if current path is a valid solution
        if self._is_valid_solution(current_path):
            self.results.append(list(current_path))
            # Optional: Determine if we should stop exploring deeper 
            # (e.g., for subsets, we keep going; for permutations of fixed len, we might stop)
            if self._should_stop_after_solution(current_path):
                return

        # 2. Iterate through candidates
        for i in range(start_index, len(self.nums)):
            candidate = self.nums[i]
            
            # Pruning hook
            if not self._is_valid_candidate(candidate, current_path):
                continue

            # Place
            current_path.append(candidate)
            
            # Recurse
            # Users define if we reuse elements (i) or move to next (i+1)
            next_index = self._get_next_index(i)
            self._backtrack(next_index, current_path)
            
            # Remove (Backtrack)
            current_path.pop()

    @abstractmethod
    def _is_valid_solution(self, path: List[Any]) -> bool:
        pass
    
    def _should_stop_after_solution(self, path: List[Any]) -> bool:
        """Override to True if valid solution is a leaf (e.g. fixed length permutation)."""
        return False

    def _is_valid_candidate(self, candidate: Any, path: List[Any]) -> bool:
        """Override for pruning logic (e.g., no duplicates)."""
        return True

    def _get_next_index(self, current_index: int) -> int:
        """
        Return current_index for reusable elements (unbounded knapsack).
        Return current_index + 1 for unique usage (subsets).
        """
        return current_index + 1