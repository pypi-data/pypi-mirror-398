from abc import ABC, abstractmethod
from typing import Any, List

class TwoPointerSolver(ABC):
    """
    Engine for solving problems where two pointers move towards each other 
    (or in specific relation) to find a target.
    Common in sorted arrays or finding container boundaries.
    """

    def solve(self, data: List[Any]) -> Any:
        self.data = data
        left = 0
        right = len(data) - 1
        
        while left < right:
            should_stop = self._process_step(left, right)
            if should_stop:
                return self._get_result()
            
            # Decide how to move
            direction = self._decide_movement(left, right)
            if direction < 0:
                left += 1
            elif direction > 0:
                right -= 1
            else:
                # Both move (rare, but sometimes needed)
                left += 1
                right -= 1
                
        return self._get_default_result()

    @abstractmethod
    def _process_step(self, left: int, right: int) -> bool:
        """
        Check logic at current pointers. 
        Return True if we found the answer and should stop.
        """
        pass

    @abstractmethod
    def _decide_movement(self, left: int, right: int) -> int:
        """
        Return -1 to move LEFT pointer forward.
        Return 1 to move RIGHT pointer backward.
        Return 0 to move BOTH (optional).
        """
        pass

    @abstractmethod
    def _get_result(self) -> Any:
        """Return the answer found."""
        pass
    
    def _get_default_result(self) -> Any:
        """Return default if loop finishes without success."""
        return -1