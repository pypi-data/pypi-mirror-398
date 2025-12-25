from abc import ABC, abstractmethod
from typing import Any, Iterable, List, Union
from enum import Enum

class WindowMode(Enum):
    SHRINK_WHILE_INVALID = 1  # Classic "Longest Substring" pattern (Maximize)
    SHRINK_WHILE_VALID = 2    # Classic "Min Subarray Sum" pattern (Minimize)

class SlidingWindowSolver(ABC):
    """
    A Universal Solver for O(N) Sliding Window problems.
    
    The user only needs to define:
    1. What happens when a number enters the window (_add)
    2. What happens when a number leaves the window (_remove)
    3. The condition to check (_condition)
    """

    def __init__(self):
        self.left = 0
        self.right = 0
        # window_state can be a dict, int, set, etc. defined by the subclass
        self.window_state = self._initial_state()
        self.best_result = self._initial_result()

    def solve(self, data: Iterable, mode: WindowMode) -> Any:
        """
        Executes the sliding window mechanics.
        
        Args:
            data: The input array or string.
            mode: 
                - SHRINK_WHILE_INVALID: Expand right. If invalid, shrink left until valid. (For Max Length)
                - SHRINK_WHILE_VALID: Expand right. If valid, record result and shrink left to find smaller. (For Min Length)
        """
        # Convert string/iterable to list for indexing if needed, 
        # though purely iterable approach is possible, indexing is safer for interview style.
        self.data = list(data) if not isinstance(data, list) else data
        n = len(self.data)
        
        for right in range(n):
            self.right = right
            item = self.data[right]
            
            # 1. EXPAND: Ingest the new element
            self._add(item)
            
            if mode == WindowMode.SHRINK_WHILE_INVALID:
                # Logic: We want the longest valid window.
                # If current window is invalid, we MUST shrink until it becomes valid.
                while self._condition(self.window_state): # _condition returns True if INVALID
                    remove_item = self.data[self.left]
                    self._remove(remove_item)
                    self.left += 1
                
                # Now the window is valid, record the result
                self._update_result()

            elif mode == WindowMode.SHRINK_WHILE_VALID:
                # Logic: We want the smallest valid window.
                # While the window is valid, record it, then shrink to see if we can do better.
                while self._condition(self.window_state): # _condition returns True if VALID
                    self._update_result()
                    remove_item = self.data[self.left]
                    self._remove(remove_item)
                    self.left += 1

        return self.best_result

    # --- Hooks to be implemented by the specific problem ---

    @abstractmethod
    def _initial_state(self) -> Any:
        """Initialize the data structure that tracks window state (e.g., HashMap, Sum)."""
        pass

    @abstractmethod
    def _initial_result(self) -> Any:
        """Initialize the result variable (e.g., 0 for max, float('inf') for min)."""
        pass

    @abstractmethod
    def _add(self, item: Any):
        """Logic to update state when 'item' enters the window."""
        pass

    @abstractmethod
    def _remove(self, item: Any):
        """Logic to update state when 'item' leaves the window."""
        pass

    @abstractmethod
    def _condition(self, state: Any) -> bool:
        """
        The condition check.
        - If mode is SHRINK_WHILE_INVALID, return True if window is BROKEN.
        - If mode is SHRINK_WHILE_VALID, return True if window is VALID (met requirement).
        """
        pass

    def _update_result(self):
        """
        Default implementation records the window length.
        Override this if the answer isn't the length (e.g., counting subarrays).
        """
        current_len = self.right - self.left + 1
        
        # We need a way to know if we are maximizing or minimizing based on the initial result
        # Simple heuristic:
        if isinstance(self.best_result, (int, float)):
            if self.best_result == float('inf'):
                self.best_result = min(self.best_result, current_len)
            else:
                self.best_result = max(self.best_result, current_len)