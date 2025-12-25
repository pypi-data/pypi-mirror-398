import heapq
from typing import List, Dict, Any, Tuple

class DijkstraSolver:
    """
    Engine for finding Shortest Path in Weighted Graphs.
    Essential for network routing or latency optimization problems.
    """
    
    def solve(self, graph: Dict[Any, List[Tuple[Any, int]]], start_node: Any) -> Dict[Any, int]:
        """
        Returns a dictionary of {node: shortest_distance_from_start}.
        Graph format: {node: [(neighbor, weight), ...]}
        """
        # Priority Queue stores tuples of (current_dist, node)
        pq = [(0, start_node)]
        shortest_paths = {start_node: 0}
        
        while pq:
            current_dist, current_node = heapq.heappop(pq)
            
            # Optimization: If we found a shorter way to current_node already, skip
            if current_dist > shortest_paths.get(current_node, float('inf')):
                continue
            
            # Explore neighbors
            if current_node in graph:
                for neighbor, weight in graph[current_node]:
                    distance = current_dist + weight
                    
                    # If shorter path found
                    if distance < shortest_paths.get(neighbor, float('inf')):
                        shortest_paths[neighbor] = distance
                        heapq.heappush(pq, (distance, neighbor))
                        
        return shortest_paths

    def solve_target(self, graph: Dict[Any, List[Tuple[Any, int]]], start_node: Any, end_node: Any) -> int:
        """Helper to get distance to a specific target."""
        distances = self.solve(graph, start_node)
        return distances.get(end_node, -1)