import unittest
import random
from collections import defaultdict, deque

# Import ALL 19 Engines
from solutionspace.engines import (
    SlidingWindowSolver, WindowMode,
    BinarySearchSolver, SearchMode,
    TwoPointerSolver,
    BacktrackingSolver,
    BFSSolver,
    UnionFind,
    TopKSolver,
    FastSlowSolver,
    IntervalSolver,
    MonotonicStackSolver, StackMode,
    Trie,
    CyclicSortSolver,
    LinkedListReversalSolver,
    TopologicalSortSolver,
    MatrixSolver,
    KnapsackSolver,
    BitwiseSolver,
    DijkstraSolver,
    SamplingSolver
)

# ==============================================================================
# HELPER CLASSES FOR INTEGRATION TESTS
# ==============================================================================

# --- Pattern 1: Sliding Window (LeetCode 3) ---
class LongestSubstringSolver(SlidingWindowSolver):
    def _initial_state(self):
        return defaultdict(int)
    
    def _initial_result(self):
        return 0
    
    def _add(self, item):
        self.window_state[item] += 1
        
    def _remove(self, item):
        self.window_state[item] -= 1
        
    def _condition(self, state):
        # Return True if INVALID (has duplicates)
        return any(count > 1 for count in state.values())

# --- Pattern 2: Binary Search (LeetCode 35) ---
class SearchInsertSolver(BinarySearchSolver):
    def __init__(self, nums, target):
        self.nums = nums
        self.target = target
    
    def _check(self, idx):
        return self.nums[idx] >= self.target

# --- Pattern 3: Two Pointers (LeetCode 167) ---
class TwoSumSolver(TwoPointerSolver):
    def __init__(self, target):
        self.target = target
        self.result = []

    def _process_step(self, left, right):
        s = self.data[left] + self.data[right]
        if s == self.target:
            self.result = [left + 1, right + 1]
            return True
        return False

    def _decide_movement(self, left, right):
        s = self.data[left] + self.data[right]
        if s < self.target:
            return -1 # Move left forward
        return 1      # Move right backward

    def _get_result(self):
        return self.result

# --- Pattern 4: Backtracking (LeetCode 78) ---
class SubsetSolver(BacktrackingSolver):
    def _is_valid_solution(self, path):
        return True # Every node is a subset

# --- Pattern 5: BFS (LeetCode 752) ---
class LockSolver(BFSSolver):
    def __init__(self, target, deadends):
        self.target = target
        self.deadends = set(deadends)
        
    def _is_target(self, node):
        return node == self.target
    
    def _is_valid_neighbor(self, node):
        return node not in self.deadends

    def _get_neighbors(self, node):
        res = []
        for i in range(4):
            x = int(node[i])
            for d in (-1, 1):
                y = (x + d) % 10
                res.append(node[:i] + str(y) + node[i+1:])
        return res

# --- Pattern 6: Top K (LeetCode 215) ---
class KthLargestSolver:
    def solve(self, nums, k):
        engine = TopKSolver(k, largest=True)
        for n in nums:
            engine.push(n)
        return engine.get_result()[0] 

# --- Pattern 8: Fast & Slow Pointers Helper ---
class ListNode:
    def __init__(self, x=0, next=None):
        self.val = x
        self.next = next

# --- Pattern 9: Merge Intervals (LeetCode 56) ---
class MyIntervalSolver(IntervalSolver):
    def _get_start(self, interval):
        return interval[0]
    
    def _should_merge(self, a, b):
        return b[0] <= a[1]
        
    def _merge_logic(self, a, b):
        a[1] = max(a[1], b[1])

# --- Pattern 10: Monotonic Stack ---
class NextGreaterSolver(MonotonicStackSolver):
    pass 

# --- Pattern 12: Cyclic Sort ---
class MissingNumberSolver(CyclicSortSolver):
    pass 

# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================
class TestSolutionSpace(unittest.TestCase):
    
    # --- Phase 1 Tests ---
    def test_longest_substring(self):
        solver = LongestSubstringSolver()
        self.assertEqual(solver.solve("abcabcbb", WindowMode.SHRINK_WHILE_INVALID), 3)

    def test_search_insert(self):
        solver = SearchInsertSolver([1,3,5,6], 5)
        self.assertEqual(solver.solve(0, 3, SearchMode.MIN_SATISFYING), 2)

    def test_two_sum(self):
        solver = TwoSumSolver(9)
        self.assertEqual(solver.solve([2,7,11,15]), [1, 2])

    # --- Phase 2 Tests ---
    def test_subsets(self):
        solver = SubsetSolver()
        res = solver.solve([1])
        # Expected [], [1]
        self.assertEqual(len(res), 2)

    def test_bfs_lock(self):
        solver = LockSolver(target="0009", deadends=[])
        self.assertEqual(solver.solve("0000"), 1)

    def test_union_find(self):
        uf = UnionFind(3)
        uf.union(0, 1)
        uf.union(1, 2)
        self.assertTrue(uf.is_connected(0, 2))
        
    def test_top_k(self):
        solver = KthLargestSolver()
        self.assertEqual(solver.solve([3,2,1,5,6,4], 2), 5)

    # --- Phase 3 Tests ---
    def test_fast_slow_pointers(self):
        head = ListNode(1, ListNode(2, ListNode(3)))
        # Create cycle 3 -> 2
        head.next.next.next = head.next 
        engine = FastSlowSolver()
        self.assertTrue(engine.has_cycle(head))

    def test_merge_intervals(self):
        solver = MyIntervalSolver()
        intervals = [[1,3],[2,6],[8,10],[15,18]]
        res = solver.merge(intervals)
        self.assertEqual(res, [[1,6],[8,10],[15,18]])

    def test_monotonic_stack(self):
        solver = NextGreaterSolver()
        res = solver.solve([2, 1, 2, 4, 3], StackMode.NEXT_GREATER)
        self.assertEqual(res, [4, 2, 4, -1, -1])

    def test_trie(self):
        trie = Trie()
        trie.insert("apple")
        self.assertTrue(trie.search("apple"))
        self.assertFalse(trie.search("app"))
        self.assertTrue(trie.starts_with("app"))

    def test_cyclic_sort(self):
        solver = MissingNumberSolver()
        nums = [3, 0, 1]
        sorted_nums = solver.solve(nums)
        # Check mismatch
        missing = -1
        for i, val in enumerate(sorted_nums):
            if i != val:
                missing = i
                break
        if missing == -1: missing = len(sorted_nums)
        self.assertEqual(missing, 2)

    # --- Phase 4 Tests ---
    def test_reverse_sublist(self):
        # 1->2->3->4->5, reverse 2 to 4
        head = ListNode(1, ListNode(2, ListNode(3, ListNode(4, ListNode(5)))))
        solver = LinkedListReversalSolver()
        new_head = solver.reverse_sublist(head, 2, 4)
        vals = []
        curr = new_head
        while curr:
            vals.append(curr.val)
            curr = curr.next
        self.assertEqual(vals, [1, 4, 3, 2, 5])

    def test_topological_sort(self):
        # 1->0, 2->0
        solver = TopologicalSortSolver()
        res = solver.solve(3, [[1,0], [2,0]])
        # 0 must come before 1 and 2
        idx0 = res.index(0)
        idx1 = res.index(1)
        idx2 = res.index(2)
        self.assertTrue(idx0 < idx1)
        self.assertTrue(idx0 < idx2)

    def test_matrix_islands(self):
        grid = [
            ["1","1","0"],
            ["1","0","0"],
            ["0","0","1"]
        ]
        solver = MatrixSolver(grid)
        count = solver.count_islands(lambda x: x == "1")
        self.assertEqual(count, 2)

    def test_knapsack_partition(self):
        solver = KnapsackSolver()
        self.assertTrue(solver.can_partition([1, 5, 11, 5]))
        self.assertFalse(solver.can_partition([1, 2, 3, 5]))

    def test_bitwise_single_number(self):
        solver = BitwiseSolver()
        self.assertEqual(solver.find_single_number([4,1,2,1,2]), 4)

    # --- Phase 5 Tests ---
    def test_dijkstra_network_delay(self):
        # 1->2 (1), 2->3 (1), 1->3 (4). Shortest 1->3 is 2.
        graph = {
            1: [(2, 1), (3, 4)],
            2: [(3, 1)],
            3: []
        }
        solver = DijkstraSolver()
        dist = solver.solve_target(graph, 1, 3)
        self.assertEqual(dist, 2)

    def test_reservoir_sampling(self):
        solver = SamplingSolver()
        stream = range(50)
        sample = solver.reservoir_sampling(stream, 5)
        self.assertEqual(len(sample), 5)

if __name__ == '__main__':
    unittest.main()