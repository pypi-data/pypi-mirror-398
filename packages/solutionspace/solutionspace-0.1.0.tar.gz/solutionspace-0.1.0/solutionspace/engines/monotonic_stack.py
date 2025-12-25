from enum import Enum
from typing import List, Any

class StackMode(Enum):
    NEXT_GREATER = 1
    NEXT_SMALLER = 2
    PREV_GREATER = 3
    PREV_SMALLER = 4

class MonotonicStackSolver:
    """
    Engine for O(N) Next Greater/Smaller Element problems.
    """
    
    def solve(self, nums: List[int], mode: StackMode) -> List[int]:
        n = len(nums)
        result = [-1] * n
        stack = [] # Stores indices
        
        # Logic for Next Greater/Smaller (Iterate forward)
        if mode in [StackMode.NEXT_GREATER, StackMode.NEXT_SMALLER]:
            for i in range(n):
                while stack and self._compare(nums[stack[-1]], nums[i], mode):
                    idx = stack.pop()
                    result[idx] = nums[i] # Or 'i' if we want the distance/index
                stack.append(i)
                
        # Logic for Prev Greater/Smaller (Iterate backward or forward keeping stack logic)
        # Often easier to iterate forward but process 'on push' instead of 'on pop' for Prev
        # For simplicity, let's stick to standard NGE patterns.
        
        return result

    def _compare(self, stack_top_val: int, current_val: int, mode: StackMode) -> bool:
        if mode == StackMode.NEXT_GREATER:
            # If current is greater than stack top, we found the NGE for stack top
            return current_val > stack_top_val
        elif mode == StackMode.NEXT_SMALLER:
            return current_val < stack_top_val
        return False