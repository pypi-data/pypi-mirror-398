from typing import Any, List, Tuple, Set

class MatrixSolver:
    """
    Engine for Grid/Island problems.
    Handles boundaries and directions automatically.
    """
    
    def __init__(self, grid: List[List[Any]]):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0
        self.visited = set()

    def get_neighbors(self, r: int, c: int, diagonal: bool = False) -> List[Tuple[int, int]]:
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        if diagonal:
            directions += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            
        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                neighbors.append((nr, nc))
        return neighbors

    def dfs(self, r: int, c: int, visit_condition_fn):
        """Generic DFS on grid."""
        if (r, c) in self.visited or not visit_condition_fn(self.grid[r][c]):
            return
        
        self.visited.add((r, c))
        # Logic for visiting node can be injected here or in the caller loop
        
        for nr, nc in self.get_neighbors(r, c):
            self.dfs(nr, nc, visit_condition_fn)

    def count_islands(self, is_land_fn) -> int:
        """Counts connected components where is_land_fn returns True."""
        count = 0
        self.visited.clear()
        
        for r in range(self.rows):
            for c in range(self.cols):
                if is_land_fn(self.grid[r][c]) and (r, c) not in self.visited:
                    count += 1
                    self.dfs(r, c, is_land_fn)
        return count