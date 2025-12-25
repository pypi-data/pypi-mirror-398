from typing import Any, Optional

class LinkedListReversalSolver:
    """
    Engine for in-place linked list reversal.
    Supports full reversal or sub-list reversal [left, right].
    """
    
    def reverse(self, head: Any) -> Any:
        """Standard full reversal."""
        prev = None
        curr = head
        while curr:
            next_node = curr.next
            curr.next = prev
            prev = curr
            curr = next_node
        return prev

    def reverse_sublist(self, head: Any, left: int, right: int) -> Any:
        """
        Reverses nodes from position 'left' to 'right' (1-indexed).
        """
        if not head or left == right:
            return head
            
        dummy = type(head)(0) # Create dummy node of same type
        dummy.next = head
        prev = dummy
        
        # 1. Move prev to node just before sublist
        for _ in range(left - 1):
            prev = prev.next
            
        # 2. Reverse the sublist
        # current is the first node of sublist (will move to end)
        current = prev.next 
        for _ in range(right - left):
            next_node = current.next
            current.next = next_node.next
            next_node.next = prev.next
            prev.next = next_node
            
        return dummy.next