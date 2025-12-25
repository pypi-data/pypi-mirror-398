from collections import deque, defaultdict
from typing import List, Dict, Any

class TopologicalSortSolver:
    """
    Engine for Kahn's Algorithm.
    Solves dependency problems (e.g., Course Schedule).
    """
    
    def solve(self, num_nodes: int, prerequisites: List[List[int]]) -> List[int]:
        """
        Returns the topological ordering.
        If cycle exists, returns empty list (or partial).
        """
        adj = defaultdict(list)
        in_degree = {i: 0 for i in range(num_nodes)}
        
        # 1. Build Graph
        for dest, src in prerequisites:
            adj[src].append(dest)
            in_degree[dest] += 1
            
        # 2. Init Queue with 0 in-degree nodes
        queue = deque([k for k, v in in_degree.items() if v == 0])
        sorted_order = []
        
        # 3. Process
        while queue:
            node = queue.popleft()
            sorted_order.append(node)
            
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        if len(sorted_order) != num_nodes:
            return [] # Cycle detected
            
        return sorted_order