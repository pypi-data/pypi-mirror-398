class UnionFind:
    """
    A concrete, optimized Disjoint Set Union (DSU) data structure.
    Includes Path Compression and Union by Rank.
    Ready to use directly, no subclassing needed usually.
    """
    def __init__(self, size: int):
        self.root = list(range(size))
        self.rank = [1] * size
        self.count = size # Count of disjoint components

    def find(self, x: int) -> int:
        if x == self.root[x]:
            return x
        # Path compression
        self.root[x] = self.find(self.root[x])
        return self.root[x]

    def union(self, x: int, y: int) -> bool:
        rootX = self.find(x)
        rootY = self.find(y)
        
        if rootX != rootY:
            if self.rank[rootX] > self.rank[rootY]:
                self.root[rootY] = rootX
            elif self.rank[rootX] < self.rank[rootY]:
                self.root[rootX] = rootY
            else:
                self.root[rootY] = rootX
                self.rank[rootX] += 1
            self.count -= 1
            return True
        return False

    def is_connected(self, x: int, y: int) -> bool:
        return self.find(x) == self.find(y)