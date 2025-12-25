import heapq
import sys

sys.setrecursionlimit(10**6)


class Node:
    def __init__(self, data, left=None, right=None):
        self.data = data
        self.left = left
        self.right = right
        self.height = 1

    def __repr__(self):
        return str(self.data)

    # Comparisons for Priority Queues (Huffman)
    def __lt__(self, other):
        return self.data < other.data if (self.data and other.data) else False


class TreeOps:
    # --- BST Operations ---
    @staticmethod
    def bst_insert(root, val):
        if not root:
            return Node(val)
        if val < root.data:
            root.left = TreeOps.bst_insert(root.left, val)
        elif val > root.data:
            root.right = TreeOps.bst_insert(root.right, val)
        return root

    @staticmethod
    def bst_search(root, val):
        if not root:
            return False
        if root.data == val:
            return True
        return TreeOps.bst_search(root.left if val < root.data else root.right, val)

    @staticmethod
    def bst_delete(root, val):
        if not root:
            return root
        if val < root.data:
            root.left = TreeOps.bst_delete(root.left, val)
        elif val > root.data:
            root.right = TreeOps.bst_delete(root.right, val)
        else:
            if not root.left:
                return root.right
            if not root.right:
                return root.left
            temp = root.right
            while temp.left:
                temp = temp.left
            root.data = temp.data
            root.right = TreeOps.bst_delete(root.right, temp.data)
        return root

    # --- Builders ---
    @staticmethod
    def huffman_tree(chars, freqs):
        """Builds Huffman Tree, returning Root. Handles tie-breaking."""
        pq = []
        for i, (c, f) in enumerate(zip(chars, freqs)):
            heapq.heappush(pq, (f, i, c, Node(c)))

        unique_id = len(chars)
        while len(pq) > 1:
            f1, i1, c1, n1 = heapq.heappop(pq)
            f2, i2, c2, n2 = heapq.heappop(pq)
            parent = Node(None, left=n1, right=n2)
            heapq.heappush(pq, (f1 + f2, unique_id, None, parent))
            unique_id += 1

        return heapq.heappop(pq)[3] if pq else None

    @staticmethod
    def from_level_order(arr):
        if not arr:
            return None
        nodes = [
            None
            if (x is None or str(x).lower() in ["null", "n", "-1"])
            else Node(int(x) if str(x).lstrip("-").isdigit() else x)
            for x in arr
        ]
        if not nodes or nodes[0] is None:
            return None

        root = nodes[0]
        q = [root]
        i = 1
        while q and i < len(nodes):
            curr = q.pop(0)
            if i < len(nodes) and nodes[i]:
                curr.left = nodes[i]
                q.append(curr.left)
            i += 1
            if i < len(nodes) and nodes[i]:
                curr.right = nodes[i]
                q.append(curr.right)
            i += 1
        return root

    @staticmethod
    def build_pre_in(pre_arr, in_arr):
        if not pre_arr or not in_arr:
            return None
        val = pre_arr[0]
        root = Node(val)
        if val not in in_arr:
            return root
        mid = in_arr.index(val)
        root.left = TreeOps.build_pre_in(pre_arr[1 : mid + 1], in_arr[:mid])
        root.right = TreeOps.build_pre_in(pre_arr[mid + 1 :], in_arr[mid + 1 :])
        return root

    # --- Traversals & Metrics ---
    @staticmethod
    def get_traversals(root):
        res = {"in": [], "pre": [], "post": [], "level": []}

        def dfs(n):
            if not n:
                return
            res["pre"].append(n.data)
            dfs(n.left)
            res["in"].append(n.data)
            dfs(n.right)
            res["post"].append(n.data)

        dfs(root)
        res["level"] = TreeOps.bfs_list(root)
        return res

    @staticmethod
    def bfs_list(root):
        if not root:
            return []
        res, q = [], [root]
        while q:
            curr = q.pop(0)
            res.append(curr.data)
            if curr.left:
                q.append(curr.left)
            if curr.right:
                q.append(curr.right)
        return res

    @staticmethod
    def height(root):
        if not root:
            return 0
        return 1 + max(TreeOps.height(root.left), TreeOps.height(root.right))

    @staticmethod
    def diameter(root, edges=True):
        ans = 0

        def depth(n):
            nonlocal ans
            if not n:
                return 0
            L, R = depth(n.left), depth(n.right)
            ans = max(ans, L + R)
            return 1 + max(L, R)

        depth(root)
        return ans if edges else (ans + 1)

    # --- Problem Specific Checks ---
    @staticmethod
    def is_symmetric(root):
        if not root:
            return True

        def check(n1, n2):
            if not n1 and not n2:
                return True
            if not n1 or not n2 or n1.data != n2.data:
                return False
            return check(n1.left, n2.right) and check(n1.right, n2.left)

        return check(root.left, root.right)

    @staticmethod
    def perfect_family(root):
        if not root:
            return True
        if not root.left and not root.right:
            return True
        if root.left and root.right:
            return False
        return TreeOps.perfect_family(root.left) and TreeOps.perfect_family(root.right)

    @staticmethod
    def kth_smallest(root, k):
        stack = []
        curr = root
        count = 0
        while stack or curr:
            while curr:
                stack.append(curr)
                curr = curr.left
            curr = stack.pop()
            count += 1
            if count == k:
                return curr.data
            curr = curr.right
        return None

    @staticmethod
    def lca(root, n1, n2):
        while root:
            if root.data > n1 and root.data > n2:
                root = root.left
            elif root.data < n1 and root.data < n2:
                root = root.right
            else:
                return root.data
        return None

    @staticmethod
    def max_leaf_to_leaf_sum(root):
        ans = -float("inf")

        def solve(node):
            nonlocal ans
            if not node:
                return -float("inf")
            if not node.left and not node.right:
                return node.data
            l, r = solve(node.left), solve(node.right)
            if node.left and node.right:
                ans = max(ans, l + r + node.data)
                return max(l, r) + node.data
            return (l if node.left else r) + node.data

        solve(root)
        return ans

    # --- AVL ---
    @staticmethod
    def avl_insert(root, val, callback=None):
        if not root:
            return Node(val)
        if val < root.data:
            root.left = TreeOps.avl_insert(root.left, val, callback)
        elif val > root.data:
            root.right = TreeOps.avl_insert(root.right, val, callback)
        else:
            return root

        root.height = 1 + max(TreeOps.height(root.left), TreeOps.height(root.right))
        bal = TreeOps.height(root.left) - TreeOps.height(root.right)

        if bal > 1 and val < root.left.data:
            if callback:
                callback("LL")
            return TreeOps._rot_r(root)
        if bal < -1 and val > root.right.data:
            if callback:
                callback("RR")
            return TreeOps._rot_l(root)
        if bal > 1 and val > root.left.data:
            if callback:
                callback("LR")
            root.left = TreeOps._rot_l(root.left)
            return TreeOps._rot_r(root)
        if bal < -1 and val < root.right.data:
            if callback:
                callback("RL")
            root.right = TreeOps._rot_r(root.right)
            return TreeOps._rot_l(root)
        return root

    @staticmethod
    def _rot_r(y):
        x = y.left
        T2 = x.right
        x.right = y
        y.left = T2
        y.height = 1 + max(TreeOps.height(y.left), TreeOps.height(y.right))
        x.height = 1 + max(TreeOps.height(x.left), TreeOps.height(x.right))
        return x

    @staticmethod
    def _rot_l(x):
        y = x.right
        T2 = y.left
        y.left = x
        x.right = T2
        x.height = 1 + max(TreeOps.height(x.left), TreeOps.height(x.right))
        y.height = 1 + max(TreeOps.height(y.left), TreeOps.height(y.right))
        return y
