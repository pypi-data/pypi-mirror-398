from abc import ABC, abstractmethod
from collections import deque
from typing import Any, List, Set

class BFSSolver(ABC):
    """
    Engine for Breadth-First Search. 
    Ideal for Shortest Path in unweighted graphs or Level Order Traversal.
    """

    def solve(self, start_node: Any) -> int:
        queue = deque([start_node])
        visited = {start_node}
        level = 0
        
        while queue:
            level_size = len(queue)
            for _ in range(level_size):
                curr = queue.popleft()
                
                if self._is_target(curr):
                    return level
                
                for neighbor in self._get_neighbors(curr):
                    if neighbor not in visited and self._is_valid_neighbor(neighbor):
                        visited.add(neighbor)
                        queue.append(neighbor)
            level += 1
            
        return -1

    @abstractmethod
    def _is_target(self, node: Any) -> bool:
        pass

    @abstractmethod
    def _get_neighbors(self, node: Any) -> List[Any]:
        pass
        
    def _is_valid_neighbor(self, node: Any) -> bool:
        return True