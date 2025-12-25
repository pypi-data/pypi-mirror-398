from typing import List

class KnapsackSolver:
    """
    Engine for 0/1 Knapsack pattern (Select or Skip).
    Can solve: Partition Equal Subset Sum, Target Sum, etc.
    """
    
    def solve_max_value(self, weights: List[int], values: List[int], capacity: int) -> int:
        """Standard 0/1 Knapsack: Maximize value within capacity."""
        n = len(weights)
        # dp[i][c] = max value using first i items with capacity c
        # Optimized to 1D array for space O(C)
        dp = [0] * (capacity + 1)
        
        for i in range(n):
            for c in range(capacity, weights[i] - 1, -1):
                dp[c] = max(dp[c], values[i] + dp[c - weights[i]])
                
        return dp[capacity]

    def can_partition(self, nums: List[int]) -> bool:
        """
        Checks if array can be partitioned into two subsets with equal sum.
        Reduced to: Find subset with sum = total_sum / 2
        """
        total = sum(nums)
        if total % 2 != 0: return False
        target = total // 2
        
        dp = {0} # Set of achievable sums
        for num in nums:
            new_sums = set()
            for s in dp:
                if s + num == target: return True
                if s + num < target:
                    new_sums.add(s + num)
            dp.update(new_sums)
            
        return False