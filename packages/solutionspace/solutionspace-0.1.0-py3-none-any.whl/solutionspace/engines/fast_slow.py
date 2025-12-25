from typing import Any, Optional

class FastSlowSolver:
    """
    Engine for Linked List patterns using Floyd's Cycle-Finding Algorithm.
    """
    
    def has_cycle(self, head: Any) -> bool:
        """
        Detects if a linked list has a cycle.
        Assumes nodes have a '.next' attribute.
        """
        if not head or not hasattr(head, 'next'):
            return False
            
        slow = head
        fast = head
        
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            
            if slow == fast:
                return True
                
        return False

    def find_middle(self, head: Any) -> Any:
        """
        Finds the middle node of a linked list.
        If even length, returns the second middle node.
        """
        if not head: return None
        
        slow = head
        fast = head
        
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            
        return slow