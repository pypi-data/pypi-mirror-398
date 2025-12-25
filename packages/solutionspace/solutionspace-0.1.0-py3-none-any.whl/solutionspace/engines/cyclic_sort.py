from typing import List

class CyclicSortSolver:
    """
    Engine for sorting arrays containing numbers in range [0, n] or [1, n] in O(N).
    Useful for finding missing numbers or duplicates.
    """
    
    def solve(self, nums: List[int]) -> List[int]:
        """
        Sorts the array in-place.
        """
        i = 0
        n = len(nums)
        while i < n:
            correct_idx = self._get_correct_index(nums[i])
            
            # If number is within bounds and not in correct spot, swap
            if 0 <= correct_idx < n and nums[i] != nums[correct_idx]:
                # Swap
                nums[i], nums[correct_idx] = nums[correct_idx], nums[i]
            else:
                i += 1
        return nums

    def _get_correct_index(self, val: int) -> int:
        """
        Default logic for 0-indexed arrays (val 0 goes to index 0).
        Override for 1-indexed (val 1 goes to index 0 -> return val - 1).
        """
        return val