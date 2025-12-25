from typing import List
from functools import reduce

class BitwiseSolver:
    """
    Engine for XOR patterns.
    """
    
    def find_single_number(self, nums: List[int]) -> int:
        """
        Finds the number that appears once while others appear twice.
        Uses property: A ^ A = 0, A ^ 0 = A.
        """
        return reduce(lambda x, y: x ^ y, nums)

    def find_two_single_numbers(self, nums: List[int]) -> List[int]:
        """
        Finds two numbers that appear once (others twice).
        """
        xor_sum = reduce(lambda x, y: x ^ y, nums)
        
        # Find rightmost set bit
        rightmost_set_bit = xor_sum & -xor_sum
        
        a, b = 0, 0
        for num in nums:
            if num & rightmost_set_bit:
                a ^= num
            else:
                b ^= num
                
        return [a, b]