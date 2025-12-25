from abc import ABC, abstractmethod
from typing import List, Any

class IntervalSolver(ABC):
    """
    Engine for handling overlapping intervals.
    Sorts input automatically and merges based on user logic.
    """
    
    def merge(self, intervals: List[Any]) -> List[Any]:
        if not intervals:
            return []
            
        # 1. Sort intervals by start time
        intervals.sort(key=lambda x: self._get_start(x))
        
        merged = [intervals[0]]
        
        for current in intervals[1:]:
            last_merged = merged[-1]
            
            if self._should_merge(last_merged, current):
                # In-place update of the last merged interval
                self._merge_logic(last_merged, current)
            else:
                merged.append(current)
                
        return merged

    @abstractmethod
    def _get_start(self, interval: Any) -> int:
        pass

    @abstractmethod
    def _should_merge(self, a: Any, b: Any) -> bool:
        """Return True if interval 'b' overlaps with 'a'."""
        pass

    @abstractmethod
    def _merge_logic(self, a: Any, b: Any):
        """Update 'a' to include 'b'. (e.g., a.end = max(a.end, b.end))"""
        pass