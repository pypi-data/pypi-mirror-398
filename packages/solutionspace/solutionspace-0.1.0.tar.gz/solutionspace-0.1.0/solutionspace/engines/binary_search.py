from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

class SearchMode(Enum):
    FIND_EXACT = 1          # Standard Binary Search
    MIN_SATISFYING = 2      # Find smallest K where condition(K) is True (Lower Bound)
    MAX_SATISFYING = 3      # Find largest K where condition(K) is True (Upper Bound)

class BinarySearchSolver(ABC):
    """
    A Universal Solver for Binary Search patterns.
    It abstracts the standard 'left <= right' boilerplate.
    User focuses on the _check() function.
    """

    def solve(self, low: int, high: int, mode: SearchMode) -> int:
        ans = -1
        left, right = low, high

        while left <= right:
            mid = left + (right - left) // 2
            
            if self._check(mid):
                if mode == SearchMode.FIND_EXACT:
                    return mid
                elif mode == SearchMode.MIN_SATISFYING:
                    ans = mid
                    right = mid - 1  # Try to find a smaller valid value
                elif mode == SearchMode.MAX_SATISFYING:
                    ans = mid
                    left = mid + 1   # Try to find a larger valid value
            else:
                # Logic Inversion depending on the problem monotonicity.
                # Assuming monotonic increasing truth (False, False, True, True) for MIN_SATISFYING
                if mode == SearchMode.MIN_SATISFYING:
                    left = mid + 1
                # Assuming monotonic decreasing truth (True, True, False, False) for MAX_SATISFYING
                elif mode == SearchMode.MAX_SATISFYING:
                    right = mid - 1
                else:
                    # For Exact match, standard logic (assuming sorted ascending)
                    # Note: You might need to override this block for complex logic
                    # This implies _check returned False because mid < target
                    if self._compare_direction(mid) < 0:
                        left = mid + 1
                    else:
                        right = mid - 1
                        
        return ans

    @abstractmethod
    def _check(self, idx: int) -> bool:
        """Return True if the index/value meets the condition."""
        pass
        
    def _compare_direction(self, idx: int) -> int:
        """
        Only used for FIND_EXACT mode.
        Return -1 if target is to the right, 1 if target is to the left.
        """
        return 0