import difflib

# Helper string for robust input reading in snippets
_PY_INPUT = """import sys
def input_gen():
    for line in sys.stdin:
        for t in line.split(): yield t
data = input_gen()
next_int = lambda: int(next(data))
next_str = lambda: next(data)
"""

# ==============================================================================
# THEORETICAL CONTENT FOR MCQ PREPARATION
# ==============================================================================
THEORY_ = {
    # -------------------------------------------------------------------------
    # UNIT 1: FUNDAMENTALS & COMPLEXITY ANALYSIS
    # -------------------------------------------------------------------------
    "Data Structure Basics": [
        "Core Definition: A data structure is a logical/mathematical model for organizing data to enable efficient operations (access, insert, delete).",
        "Data vs. Information: Data = Raw facts (e.g., 42). Information = Processed data (e.g., 'Age: 42').",
        "Primitive vs. Non-Primitive: Primitive (int, float, char) are machine-level. Non-primitive (arrays, lists) are derived/user-defined.",
        "Linear vs. Non-Linear: Linear (Array, Stack, Queue) stores data sequentially. Non-Linear (Tree, Graph) stores data hierarchically or arbitrarily.",
        "Static vs. Dynamic: Static (Array) size is fixed at compile-time (stack memory). Dynamic (Linked List) size changes at runtime (heap memory).",
        "Homogeneous vs. Non-Homogeneous: Arrays are homogeneous (same type). Structures/Classes are non-homogeneous.",
        "MCQ Trap: A 'Structure' in C/C++ is a non-homogeneous, linear (physically), user-defined data type."
    ],

    "Algorithm & Efficiency": [
        "Algorithm Properties: Input (0+), Output (1+), Definiteness (unambiguous), Finiteness (must stop), Effectiveness (feasible), Correctness.",
        "Time Complexity: A function T(n) representing the number of 'Elementary Operations' relative to input size 'n'. It is NOT the actual wall-clock time.",
        "Space Complexity: Total Memory = Instruction Space (Code) + Data Space (Variables/Constants) + Environment Space (Stack Frame). Complexity analysis usually focuses only on Data Space.",
        "Trade-off: Usually, reducing time complexity increases space complexity (Space-Time Trade-off)."
    ],

    "Asymptotic Notations (The MCQ Heavyweight)": [
        "Big-Oh (O) - Upper Bound: Represents the WORST case. f(n) <= c*g(n) for n >= n0. Used to guarantee 'it won't take longer than this'.",
        "Big-Omega (Ω) - Lower Bound: Represents the BEST case. f(n) >= c*g(n). Used to say 'it takes at least this much time'.",
        "Big-Theta (Θ) - Tight Bound: Represents the AVERAGE/EXACT case. c1*g(n) <= f(n) <= c2*g(n).",
        "Growth Rate Order (Memorize for MCQs): O(1) < O(log n) < O(sqrt(n)) < O(n) < O(n log n) < O(n^2) < O(n^3) < O(2^n) < O(n!).",
        "Constant Time O(1): Formulas, accessing array index, pushing to stack.",
        "Logarithmic O(log n): Binary Search, dividing problem in half.",
        "Linear O(n): Looping through array, Linear Search.",
        "Linearithmic O(n log n): Merge Sort, Heap Sort, Quick Sort (Avg).",
        "Quadratic O(n^2): Nested loops (Bubble/Insertion/Selection Sort).",
        "MCQ Trap: If f(n) = 3n^2 + 100n + 5000, the complexity is O(n^2). We drop constants (3) and lower order terms (100n).",
        "MCQ Trap: O(1) does not mean 'instant', it means 'time does not change as input grows'."
    ],

    # -------------------------------------------------------------------------
    # UNIT 2: SORTING & SEARCHING (DIVIDE AND CONQUER)
    # -------------------------------------------------------------------------
    "Divide and Conquer (D&C)": [
        "Paradigm: Divide (break into sub-problems), Conquer (solve recursively), Combine (merge results).",
        "Recurrence Relations: Used to calculate complexity. E.g., T(n) = 2T(n/2) + n (Merge Sort).",
        "Examples: Merge Sort, Quick Sort, Binary Search, Strassen's Matrix Multiplication.",
        "MCQ Trap: Binary Search is D&C but often lacks the 'Combine' step (it just returns the index)."
    ],

    "Binary Search": [
        "Prerequisite: Array MUST be sorted.",
        "Logic: Compare mid. If key < mid, High = mid-1. If key > mid, Low = mid+1.",
        "Complexity: Best Case O(1) (found at mid). Worst/Avg Case O(log n).",
        "Comparisons: Max comparisons = floor(log2 n) + 1.",
        "MCQ Trap: Binary Search works on Arrays (random access), but is inefficient on Linked Lists (sequential access)."
    ],

    "Merge Sort": [
        "Logic: Recursively split array until size 1, then merge sorted subarrays.",
        "Time Complexity: O(n log n) in ALL cases (Best, Worst, Avg). It is consistent.",
        "Space Complexity: O(n) auxiliary space (not in-place).",
        "Stability: STABLE (preserves original order of equal elements).",
        "MCQ Trap: Preferred for sorting Linked Lists because it doesn't require random access."
    ],

    "Quick Sort": [
        "Logic: Pick Pivot, Partition (elements < pivot left, > pivot right), Recurse.",
        "Time Complexity: Best/Avg: O(n log n). Worst: O(n^2).",
        "Worst Case Trigger: When array is already sorted (or reverse sorted) and pivot is always the smallest/largest element. Recursion depth becomes n.",
        "Space Complexity: O(log n) stack space (Best/Avg), O(n) (Worst).",
        "Stability: UNSTABLE.",
        "MCQ Trap: Quick Sort is usually faster than Merge Sort in practice due to lower constant factors and cache locality, despite the O(n^2) worst case."
    ],

    # -------------------------------------------------------------------------
    # UNIT 3: HASHING
    # -------------------------------------------------------------------------
    "Hashing Mechanics": [
        "Concept: Map large key space to small index range [0, S-1].",
        "Perfect Hashing: No collisions (O(1)). Hard to achieve.",
        "Load Factor (α): α = N / S (Elements / Table Size). Indicates how full the table is.",
        "Hash Functions: Division (k % S), Multiplication (floor(S*(kA mod 1))), Mid-Square, Folding.",
        "MCQ Trap: 'S' (Table Size) in Division method should be a PRIME number not close to a power of 2 to minimize collisions."
    ],

    "Collision Resolution": [
        "Definition: When h(k1) == h(k2).",
        "1. Separate Chaining (Open Hashing): Bucket contains a Linked List. α can be > 1. Search is O(1 + α). Deletion is easy.",
        "2. Open Addressing (Closed Hashing): Elements stored in table slots. α must be <= 1.",
        "   - Linear Probing: Index = (h(k) + i) % S. Problem: Primary Clustering (clusters grow and merge).",
        "   - Quadratic Probing: Index = (h(k) + i^2) % S. Problem: Secondary Clustering.",
        "   - Double Hashing: Index = (h1(k) + i*h2(k)) % S. Best distribution. Hash2 must not evaluate to 0.",
        "MCQ Trap: In Open Addressing, you cannot simply delete a node (it breaks the probe chain). You must mark it as 'Deleted/Tombstone'."
    ],

    # -------------------------------------------------------------------------
    # UNIT 4: TREES (THEORY & PROPERTIES)
    # -------------------------------------------------------------------------
    "Tree Properties": [
        "N Nodes => N-1 Edges.",
        "Depth: Edges from Root to Node (Root is 0).",
        "Height: Edges from Node to deepest Leaf (Leaf is 0). Height of Tree = Height of Root.",
        "Levels: Root is Level 0 (sometimes 1 in specific texts, usually 0). Max nodes at level L = 2^L.",
        "Max nodes in Binary Tree of height H: 2^(H+1) - 1.",
        "Relationship: If N is number of nodes, Min Height = floor(log2 N). Max Height = N-1 (Skewed)."
    ],

    "Binary Tree Types (Crucial for MCQs)": [
        "Full/Strict: Nodes have 0 or 2 children. (No node has 1 child). Number of leaf nodes L = Internal nodes I + 1.",
        "Complete: All levels filled completely, except possibly the last level which is filled left-to-right. (Used in Heaps).",
        "Perfect: All internal nodes have 2 children, all leaves at same level. Total nodes = 2^(h+1) - 1.",
        "Extended: Regular nodes replaced by internal nodes, NULLs replaced by special nodes.",
        "Skewed: Every node has only 1 child. (Left or Right). Effectively a Linked List."
    ],

    "Traversals": [
        "Pre-Order: Root, Left, Right (Prefix notation).",
        "In-Order: Left, Root, Right (Infix notation). **In a BST, In-Order gives sorted sequence.**",
        "Post-Order: Left, Right, Root (Postfix notation). Used for deleting tree (delete children first).",
        "Level-Order: BFS traversal using a Queue.",
        "MCQ Trap: To construct a unique tree, you need In-Order + (Pre-Order OR Post-Order). Pre+Post is NOT sufficient."
    ],

    "Threaded Binary Trees": [
        "Problem: In a standard Binary Tree of N nodes, there are N+1 NULL pointers (wasted space).",
        "Solution: Use NULL pointers to store 'Threads' (references) to In-Order Predecessor/Successor.",
        "Single Threaded: Only Right NULLs point to Successor.",
        "Double Threaded: Left NULL -> Predecessor, Right NULL -> Successor.",
        "Benefit: Allows linear traversal without a Stack or Recursion."
    ],

    "Huffman Coding": [
        "Type: Greedy Algorithm for Lossless Compression.",
        "Logic: Frequent chars -> Short codes (near root). Rare chars -> Long codes (deep leaves).",
        "Prefix Property: No code is a prefix of another.",
        "Construction: Build a tree bottom-up. Always merge 2 smallest frequencies.",
        "Complexity: O(N log N)."
    ],

    "AVL Trees (Height Balanced)": [
        "Definition: BST where |Height(Left) - Height(Right)| <= 1 for ALL nodes.",
        "Balance Factor: H(Left) - H(Right). Allowed: {-1, 0, 1}.",
        "Rotations (to fix imbalance):",
        "  - LL Imbalance (Left-Left): Single Right Rotation.",
        "  - RR Imbalance (Right-Right): Single Left Rotation.",
        "  - LR Imbalance: Double Rotation (Left on child, then Right on root).",
        "  - RL Imbalance: Double Rotation (Right on child, then Left on root).",
        "Complexity: All operations (Search/Insert/Delete) are guaranteed O(log n)."
    ],

    "AVL Tree Specifics": [
        "Rotations Count: For an insertion, at most 2 rotations (one single or one double) are needed overall.",
        "Update Scope: After insertion, balance factors update only along the path from inserted node to root.",
        "Max Height: ~1.44 * log2(n).",
        "Min Nodes at Height h: N(h) = N(h-1) + N(h-2) + 1 (Fibonacci-like)."
    ],

    "Extended Binary Tree (2-Tree)": [
        "Definition: Every null subtree replaced by a special external node.",
        "Transformation: Originals become internal nodes; added dummies are external nodes.",
        "Property: If I internal nodes, E external nodes, then E = I + 1."
    ],

    "Threaded Binary Trees (Advanced)": [
        "Pointer Logic: Threads reuse null pointers to link in-order neighbors.",
        "Right null -> in-order successor; Left null -> in-order predecessor.",
        "Leaf Threads: Leaf right pointer can thread to the next in-order node.",
        "Benefit: In-order traversal without recursion or stack."
    ],

    "Tree Construction Logic": [
        "Postorder + Inorder: Postorder last is root; locate in inorder, split left/right, recurse.",
        "Preorder + Inorder: Preorder first is root; locate in inorder, split, recurse.",
        "Level Order: First element is root; subsequent elements fill level by level left-to-right.",
        "Balanced BST from Sorted: Pick median as root, recurse on halves (gives height-balanced BST)."
    ],

    # -------------------------------------------------------------------------
    # UNIT 5: GRAPHS
    # -------------------------------------------------------------------------
    "Graph Representation & Properties": [
        "Max Edges: Directed = N*(N-1). Undirected = N*(N-1)/2.",
        "Adjacency Matrix: V*V array. O(1) to check edge. Space O(V^2). Good for Dense graphs.",
        "Adjacency List: Array of Lists. Space O(V+E). Good for Sparse graphs. Iterating neighbors is fast.",
        "Handshaking Lemma: Sum of degrees in undirected graph = 2 * |Edges|."
    ],

    "Graph Traversals": [
        "DFS (Depth First): Uses Stack (or Recursion). Backtracking. Finds Connected Components, Cycles, Topological Sort. Time: O(V+E).",
        "BFS (Breadth First): Uses Queue. Level-by-level. Finds Shortest Path (unweighted) and Connected Components. Time: O(V+E).",
        "MCQ Trap: DFS produces a 'Spanning Tree'. Edges not in the tree are 'Back Edges' (indicate cycles)."
    ],

    "Adjacency Matrix Properties": [
        "Undirected Graph: Matrix is symmetric (A[i][j] == A[j][i]).",
        "Directed Graph: Max non-zero entries = N*(N-1) without self-loops, or N^2 with self-loops.",
        "Edge Check: O(1) to test existence; space O(N^2)."
    ],

    "Adjacency List Properties": [
        "Undirected Storage: Each edge (u,v) is stored twice (u lists v; v lists u).",
        "Efficiency: Enumerating neighbors is O(degree) vs O(N) for matrix representation."
    ],

    "Connectivity & Articulation": [
        "Connected Component: Maximal subgraph where all vertices are reachable.",
        "Strongly Connected (Directed): Path exists u->v AND v->u for all pairs.",
        "Articulation Point (Cut Vertex): A vertex whose removal increases number of connected components (disconnects graph).",
        "Bi-Connected Graph: Graph with NO Articulation Points (requires at least 2 paths between any pair).",
        "Topological Sort: Linear ordering for Directed Acyclic Graphs (DAG). If cycle exists, Topo sort is impossible."
    ],

    # -------------------------------------------------------------------------
    # UNIT 6: ADVANCED DATA STRUCTURES
    # -------------------------------------------------------------------------
    "Binomial Heaps": [
        "Binomial Tree B_k: Order k. Height k. Nodes 2^k.",
        "Recursive Def: B_k is formed by linking two B_(k-1) trees. The root of one becomes the child of the other.",
        "Binomial Heap: A collection (forest) of Binomial Trees. No two trees have same order.",
        "Representation: Binary representation of N. If N=13 (1101 binary), Heap has trees B3, B2, B0.",
        "Operations:",
        "  - Merge (Union): The primary operation. O(log n). Links trees of same degree.",
        "  - Insert: Treat as merging heap with new node (B0).",
        "  - Extract Min: Find min root, remove it, reverse its children to form new heap, Merge.",
        "MCQ Trap: In Binary Heap, Insert is O(log n), but in Binomial Heap, 'Amortized' Insert is O(1) (though worst case is log n)."
    ],

    "Tries & Digital Search": [
        "Digital Search Tree (DST): Binary tree branching based on BIT values of key (0=Left, 1=Right).",
        "DST Complexity: Height depends on Key Length (B bits), not number of elements N. Search O(B).",
        "Trie (Prefix Tree): m-ary tree (usually 26 for alphabet). Root is null.",
        "Trie Usage: Dictionary, Autocomplete, Spell Check.",
        "Complexity: Search/Insert is O(L) where L is string length. Fast, but space-heavy.",
        "Compressed Trie: Chains of single-child nodes are collapsed into one edge to save space."
    ],

    "Tries (Prefix Trees) Deep Dive": [
        "Edge vs Node: Edges carry characters; nodes represent prefixes or word ends.",
        "Complexity: Search/Insert O(L) with L = word length; independent of number of stored words.",
        "Branching Factor: Driven by alphabet size (e.g., 26 for lowercase English).",
        "Primary Use: Longest prefix match, autocomplete, spell check.",
        "Shortest Unique Prefix: Tries quickly find shortest distinguishing prefixes."
    ],

    "Binomial Heap Nuances": [
        "Root List Order: Roots are ordered by strictly increasing degree.",
        "Structure: Forest of binomial trees; no two trees share the same degree.",
        "Merge Advantage: Merge/Union in O(log n) (binary heap merge is O(n)).",
        "Complexity Checklist:",
        "  - Insert: O(log n) worst, O(1) amortized.",
        "  - Extract-Min: O(log n).",
        "  - Decrease-Key: O(log n).",
        "  - Merge: O(log n).",
        "Node Count: Binomial tree B_k has exactly 2^k nodes.",
        "Root Degree: Root of B_k has degree k (k children)."
    ],

    "Disjoint Set (Union-Find) Details": [
        "Operations: Find returns representative/root; Union merges sets.",
        "Optimizations: Path compression and Union by rank/size keep trees shallow.",
        "Applications: Kruskal MST, cycle detection in undirected graphs, connectivity queries.",
        "Not For: Shortest paths/search (use BFS/Dijkstra instead)."
    ],

    "Priority Queues (Theory)": [
        "Implementation: Typically heaps (binary or binomial).",
        "Variants: Max-PQ serves largest key; Min-PQ serves smallest key.",
        "Insertion: O(log n) with heap; retrieval ordered by priority, not FIFO/LIFO."
    ]
# Additional Unit 5 programs
    ,
    "trie implementation": {
        "python": """class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True

    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

try:
    # Reading input
    n = int(input())
    words = input().split()
    key = input()

    trie = Trie()
    for w in words:
        trie.insert(w)

    if trie.search(key):
        print(1)
    else:
        print(0)
except:
    pass"""
    },

    "priority queue basic": {
        "python": """pq = []

while True:
    print("1.Enqueue 2.Display 3.Exit")
    try:
        op = int(input("Enter your option : "))
    except:
        break

    if op == 1:
        val = int(input("Enter element : "))
        prio = int(input("Enter priority : "))
        pq.append((val, prio))
    elif op == 2:
        if not pq:
            print("Priority queue is empty.")
        else:
            # Sort by priority (ascending). Python sort is stable, preserving insertion order for equal priorities.
            sorted_pq = sorted(pq, key=lambda x: x[1])
            print("Elements in the priority queue :", end=" ")
            for item in sorted_pq:
                print(item[0], end=" ")
            print()
    elif op == 3:
        break"""
    },

    "priority queue full": {
        "python": """pq = []

while True:
    print("1.Enqueue 2.Dequeue 3.Display 4.Is Empty 5.Size 6.Exit")
    try:
        op = int(input("Enter your option : "))
    except:
        break

    if op == 1:
        val = int(input("Enter element : "))
        prio = int(input("Enter priority : "))
        pq.append((val, prio))
    
    elif op == 2:
        if not pq:
            print("Priority queue is underflow.")
        else:
            # Find the item with the minimum priority value (highest priority)
            # min() returns the first occurrence if there are ties, acting like a stable selection
            target = min(pq, key=lambda x: x[1])
            pq.remove(target)
            print(f"Deleted value = {target[0]}")
    
    elif op == 3:
        if not pq:
            print("Priority queue is empty.")
        else:
            sorted_pq = sorted(pq, key=lambda x: x[1])
            print("Elements in the priority queue :", end=" ")
            for item in sorted_pq:
                print(item[0], end=" ")
            print()
    
    elif op == 4:
        if not pq:
            print("Priority queue is empty.")
        else:
            print("Priority queue is not empty.")
            
    elif op == 5:
        print(f"Priority queue size : {len(pq)}")
        
    elif op == 6:
        break"""
    },

    "bst to min heap": {
        "python": """# The problem asks for the Preorder traversal of a tree derived from the BST structure.
# The derived tree must satisfy Min Heap property and 'Left Subtree < Right Subtree'.
# This structure is achieved by filling the tree nodes in Preorder with the sorted values of the BST.
# Therefore, the Preorder traversal of the result is simply the sorted values of the input.

raw_input = list(map(int, input().split()))
# Filter out -1 (null nodes) and sort the values
values = sorted([x for x in raw_input if x != -1])
print(*values)"""
    }
}
_DOCS = {
    # ==============================================================================
    # 7.8 & 7.9 Series: TREES
    # ==============================================================================
    "tree traversals": {
        "baby": """from networkxx import scan, TreeOps\nn = scan.int()\nvals = []\nfor _ in range(n):\n    op = scan.int()\n    if op == 1: vals.append(scan.int())\n    else:\n        root = TreeOps.from_level_order(vals)\n        if not root: print("Empty")\n        else:\n            t = TreeOps.get_traversals(root)\n            print(*t['in'] if op==2 else (t['pre'] if op==3 else t['post']))""",
        "python": """from collections import deque\n\nclass N:\n    def __init__(s, x): s.v = x; s.l = s.r = None\n\nroot = None\n\ndef ins(x):\n    global root\n    if not root:\n        root = N(x)\n        return\n    q = deque([root])\n    while q:\n        n = q.popleft()\n        if not n.l: n.l = N(x); return\n        if not n.r: n.r = N(x); return\n        q += [n.l, n.r]\n\ndef tr(n, t, a):\n    if not n: return\n    if t == 3: a.append(n.v)\n    tr(n.l, t, a)\n    if t == 2: a.append(n.v)\n    tr(n.r, t, a)\n    if t == 4: a.append(n.v)\n\nout = []\nfor _ in range(int(input())):\n    op = input().split()\n    if op[0] == "1":\n        ins(int(op[1]))\n    else:\n        a = []\n        tr(root, int(op[0]), a)\n        out.append((" ".join(map(str, a)) + " ") if a else "Empty ")\n\nprint("\\n".join(out))"""
    },

    "binary search tree operations": {
        "baby": """from networkxx import scan, TreeOps\nn, root = scan.int(), None\nres = []\nfor _ in range(n):\n    op = scan.int()\n    if op == 1: root = TreeOps.bst_insert(root, scan.int())\n    elif op == 2: root = TreeOps.bst_delete(root, scan.int())\n    elif op == 3: res.append("found" if TreeOps.bst_search(root, scan.int()) else "not found")\n    elif op in (4,5,6):\n        if not root: res.append("Empty")\n        else: res.append(" ".join(map(str, TreeOps.get_traversals(root)['in' if op==4 else ('pre' if op==5 else 'post')] )))\nprint(*res, sep='\\n')""",
        "python": """class N:\n    def __init__(s, x): s.v = x; s.l = s.r = None\n\nroot = None\nout = []\n\ndef ins(n, x):\n    if not n: return N(x)\n    if x < n.v: n.l = ins(n.l, x)\n    elif x > n.v: n.r = ins(n.r, x)\n    return n\n\ndef mn(n):\n    while n.l: n = n.l\n    return n.v\n\ndef dele(n, x):\n    if not n: return n\n    if x < n.v: n.l = dele(n.l, x)\n    elif x > n.v: n.r = dele(n.r, x)\n    else:\n        if not n.l: return n.r\n        if not n.r: return n.l\n        t = mn(n.r)\n        n.v = t\n        n.r = dele(n.r, t)\n    return n\n\ndef sea(n, x):\n    if not n: return False\n    if x == n.v: return True\n    return sea(n.l, x) if x < n.v else sea(n.r, x)\n\ndef tr(n, t, a):\n    if not n: return\n    if t == 5: a.append(n.v)\n    tr(n.l, t, a)\n    if t == 4: a.append(n.v)\n    tr(n.r, t, a)\n    if t == 6: a.append(n.v)\n\nfor _ in range(int(input())):\n    op = input().split()\n    c = int(op[0])\n    if c == 1: root = ins(root, int(op[1]))\n    elif c == 2: root = dele(root, int(op[1]))\n    elif c == 3:\n        out.append("found" if sea(root, int(op[1])) else "not found")\n    else:\n        a = []; tr(root, c, a)\n        out.append(" ".join(map(str, a)) if a else "Empty")\n\nprint("\\n".join(out))"""
    },

    "huffman encoding tree": {
        "baby": """from networkxx import scan, TreeOps\nchars = scan.str()\nfreqs = scan.list_fixed(len(chars))\nroot = TreeOps.huffman_tree(chars, freqs)\ncodes = []\ndef dfs(n, p):\n    if not n: return\n    if n.data: codes.append(p)\n    dfs(n.left, p+"0"); dfs(n.right, p+"1")\ndfs(root, "")\nprint(*codes)""",
        "python": """import heapq\n\nclass N:\n    def __init__(s,f,c=None,o=0,l=None,r=None): s.f=f;s.c=c;s.o=o;s.l=l;s.r=r\n    def __lt__(s,o): return (s.f,s.o)<(o.f,o.o)\n\nchs = input().strip()\nfs  = list(map(int, input().split()))\n\npq=[N(f,c,i) for i,(c,f) in enumerate(zip(chs,fs))]\nheapq.heapify(pq)\n\no=len(chs)\nwhile len(pq)>1:\n    a,b=heapq.heappop(pq),heapq.heappop(pq)\n    heapq.heappush(pq, N(a.f+b.f, None, o, a, b))\n    o+=1\n\nans=[]\ndef dfs(n,p):\n    if n.c!=None: ans.append(p)\n    else: dfs(n.l,p+"0"); dfs(n.r,p+"1")\n\ndfs(pq[0],"")\n\n# EXACT FORMAT: items separated by space + one trailing space\nprint(" ".join(ans) + " ", end="")"""
    },

    "avl tree insert": {
        "baby": """from networkxx import scan, TreeOps\nvals = scan.list_fixed(scan.int())\nroot = None\nfor v in vals:\n    rot = []\n    root = TreeOps.avl_insert(root, v, lambda x: rot.append(x))\n    if rot: print(rot[-1])\n    print(*TreeOps.get_traversals(root)['in'])""",
        "python": """class N:\n    def __init__(s, k):\n        s.k = k; s.h = 1; s.l = s.r = None\n\ndef h(n): return n.h if n else 0\ndef bal(n): return h(n.l) - h(n.r)\ndef upd(n): n.h = 1 + max(h(n.l), h(n.r))\n\ndef rR(y):\n    x = y.l; t = x.r\n    x.r = y; y.l = t\n    upd(y); upd(x)\n    return x\n\ndef rL(x):\n    y = x.r; t = y.l\n    y.l = x; x.r = t\n    upd(x); upd(y)\n    return y\n\ndef ins(n, k, rot):\n    if not n: return N(k)\n    if k < n.k: n.l = ins(n.l, k, rot)\n    elif k > n.k: n.r = ins(n.r, k, rot)\n    else: return n\n\n    upd(n)\n    b = bal(n)\n\n    if b > 1 and k < n.l.k:\n        rot.append("LL"); return rR(n)\n    if b < -1 and k > n.r.k:\n        rot.append("RR"); return rL(n)\n    if b > 1 and k > n.l.k:\n        rot.append("LR"); n.l = rL(n.l); return rR(n)\n    if b < -1 and k < n.r.k:\n        rot.append("RL"); n.r = rR(n.r); return rL(n)\n\n    return n\n\ndef inorder(n):\n    if n:\n        inorder(n.l); print(n.k, end=" "); inorder(n.r)\n\nn = int(input())\narr = list(map(int, input().split()))\nroot = None\n\nfor x in arr:\n    rot = []\n    root = ins(root, x, rot)\n    if rot: print(*rot)\n    inorder(root); print()"""
    },

    "find tree height": {
        "baby": """from networkxx import scan, TreeOps\nscan.int()\nprint(TreeOps.height(TreeOps.from_level_order(scan.list_until())))""",
        "python": """from collections import deque\n\nclass Node:\n    def __init__(self, v):\n        self.v = v; self.l = self.r = None\n\ndef build(vals):\n    if not vals or vals[0] == "null": return None\n    root = Node(int(vals[0]))\n    q = deque([root])\n    i = 1\n    while q and i < len(vals):\n        n = q.popleft()\n        if vals[i] != "null":\n            n.l = Node(int(vals[i])); q.append(n.l)\n        i += 1\n        if i < len(vals) and vals[i] != "null":\n            n.r = Node(int(vals[i])); q.append(n.r)\n        i += 1\n    return root\n\ndef height(n):\n    return 0 if not n else 1 + max(height(n.l), height(n.r))\n\nn = int(input())\nvals = input().split()\nroot = build(vals)\nprint(height(root))"""
    },

    "build tree from preorder inorder": {
        "baby": """from networkxx import scan, TreeOps\nn = scan.int()\nprint(*TreeOps.get_traversals(TreeOps.build_pre_in(scan.list_fixed(n), scan.list_fixed(n)))['post'])""",
        "python": """class Node:\n    def __init__(s, v):\n        s.v = v; s.l = s.r = None\n\ndef build(inorder, preorder, s, e, idx):\n    if s > e: return None\n    val = preorder[idx[0]]; idx[0] += 1\n    root = Node(val)\n    if s == e: return root\n    m = inorder.index(val, s, e + 1)\n    root.l = build(inorder, preorder, s, m - 1, idx)\n    root.r = build(inorder, preorder, m + 1, e, idx)\n    return root\n\ndef post(n):\n    if n:\n        post(n.l); post(n.r)\n        print(n.v, end=" ")\n\nn = int(input())\nino = list(map(int, input().split()))\npre = list(map(int, input().split()))\nroot = build(ino, pre, 0, n - 1, [0])\npost(root)"""
    },

    "find tree diameter": {
        "baby": """from networkxx import scan, TreeOps\nprint(TreeOps.diameter(TreeOps.from_level_order(scan.list_until(sentinel=None)), edges=True))""",
        "python": """import sys\nfrom collections import deque\n\ns = sys.argv[1].split()\n\ndef build(a):\n    if not a or a[0] == "N":\n        return None\n    class N:\n        def __init__(s, v): s.v = v; s.l = s.r = None\n    r = N(a[0])\n    q = deque([r])\n    i = 1\n    while q and i < len(a):\n        n = q.popleft()\n        if a[i] != "N":\n            n.l = N(a[i]); q.append(n.l)\n        i += 1\n        if i < len(a) and a[i] != "N":\n            n.r = N(a[i]); q.append(n.r)\n        i += 1\n    return r\n\ndef diameter(root):\n    dia = 0\n    def dfs(n):\n        nonlocal dia\n        if not n: return 0\n        L = dfs(n.l); R = dfs(n.r)\n        dia = max(dia, L + R)\n        return 1 + max(L, R)\n    dfs(root)\n    return dia\n\nprint(diameter(build(s)))"""
    },

    "find bst lowest common ancestor": {
        "baby": """from networkxx import scan, TreeOps\nn = scan.int()\nvals = scan.list_fixed(n)\nroot = None\nfor v in vals: root = TreeOps.bst_insert(root, v)\nprint(TreeOps.lca(root, scan.int(), scan.int()))""",
        "python": """class Node:\n    def __init__(s, v):\n        s.v = v; s.l = s.r = None\n\ndef insert(r, x):\n    if not r: return Node(x)\n    if x < r.v: r.l = insert(r.l, x)\n    elif x > r.v: r.r = insert(r.r, x)\n    return r\n\ndef lca(r, a, b):\n    while r:\n        if a < r.v and b < r.v: r = r.l\n        elif a > r.v and b > r.v: r = r.r\n        else: return r\n\nn = int(input())\nvals = list(map(int, input().split()))\n\nroot = None\nfor x in vals:\n    root = insert(root, x)\n\na = int(input())\nb = int(input())\n\nprint(lca(root, a, b).v)"""
    },

    "check perfect family tree": {
        "baby": """from networkxx import scan, TreeOps\nscan.int()\nroot = None\nfor v in scan.list_until(sentinel=None): root = TreeOps.bst_insert(root, int(v))\nprint(1 if TreeOps.perfect_family(root) else 0)""",
        "python": """n = int(input().strip())\narr = list(map(int, input().split()))\n\nlast = arr[-1]\nperfect = 1\n\nfor i in range(n - 1):\n    curr = arr[i]\n    nxt = arr[i + 1]\n    if (nxt - curr) * (last - curr) <= 0:\n        perfect = 0\n        break\n\nprint(perfect)"""
    },

    "check if tree symmetric": {
        "baby": """from networkxx import scan, TreeOps\nroot = TreeOps.from_level_order(scan.list_until('-1'))\nprint(1 if TreeOps.is_symmetric(root) else 0)""",
        "python": """from collections import deque\n\ndef build(a):\n    if not a or a[0] in ("null", "-1"): return None\n    r = [int(a[0]), None, None]\n    q = deque([r])\n    i = 1\n    while q and i < len(a):\n        n = q.popleft()\n        if a[i] != "null":\n            n[1] = [int(a[i]), None, None]; q.append(n[1])\n        i += 1\n        if i < len(a) and a[i] != "null":\n            n[2] = [int(a[i]), None, None]; q.append(n[2])\n        i += 1\n    return r\n\ndef mirror(a, b):\n    if not a and not b: return True\n    if not a or not b: return False\n    return a[0] == b[0] and mirror(a[1], b[2]) and mirror(a[2], b[1])\n\nvals = input().split()\nvals = vals[:vals.index("-1")]\n\nroot = build(vals)\nprint(1 if not root or mirror(root[1], root[2]) else 0)"""
    },

    "find kth smallest element": {
        "baby": """from networkxx import scan, TreeOps\nvals = scan.list_until('-1')\nprint(TreeOps.kth_smallest(TreeOps.from_level_order(vals), scan.int()))""",
        "python": """from collections import deque\n\nclass N:\n    def __init__(s, v): s.v = v; s.l = s.r = None\n\ndef build(a):\n    if not a or a[0] in ("null", "-1"): return None\n    r = N(int(a[0])); q = deque([r]); i = 1\n    while q and i < len(a):\n        n = q.popleft()\n        if a[i] != "null": n.l = N(int(a[i])); q.append(n.l)\n        i += 1\n        if i < len(a) and a[i] != "null": n.r = N(int(a[i])); q.append(n.r)\n        i += 1\n    return r\n\ndef inorder(n, k, res):\n    if not n or res[1] != -1: return\n    inorder(n.l, k, res)\n    res[0] += 1\n    if res[0] == k:\n        res[1] = n.v; return\n    inorder(n.r, k, res)\n\nvals = input().split()\nvals = vals[:vals.index("-1")]\nk = int(input())\n\nroot = build(vals)\nres = [0, -1]\ninorder(root, k, res)\nprint(res[1])"""
    },

    "level order traversal": {
        "baby": """from networkxx import scan, TreeOps\nscan.int()\nroot = None\nfor v in scan.list_until(sentinel=None): root = TreeOps.bst_insert(root, int(v))\nprint(*TreeOps.bfs_list(root))""",
        "python": """from collections import deque\n\nclass Node:\n    def __init__(s, v):\n        s.v = v; s.l = s.r = None\n\ndef insert(r, x):\n    if not r: return Node(x)\n    if x < r.v: r.l = insert(r.l, x)\n    else: r.r = insert(r.r, x)\n    return r\n\ndef bfs(r):\n    if not r:\n        print("Empty ")\n        return\n    q = deque([r])\n    out = []\n    while q:\n        n = q.popleft()\n        out.append(str(n.v))\n        if n.l: q.append(n.l)\n        if n.r: q.append(n.r)\n    print(" ".join(out) + " ")\n\nn = int(input())\nvals = list(map(int, input().split()))\n\nroot = None\nfor x in vals:\n    root = insert(root, x)\n\nbfs(root)"""
    },

    "max leaf to leaf sum": {
        "baby": """from networkxx import scan, TreeOps\nprint(TreeOps.max_leaf_to_leaf_sum(TreeOps.from_level_order(scan.list_until('-1'))))""",
        "python": """from collections import deque\n\nclass Node:\n    def __init__(s, v):\n        s.v = v; s.l = s.r = None\n\nans = -10**18\n\ndef build(a):\n    if not a or a[0] == "null": return None\n    r = Node(int(a[0])); q = deque([r]); i = 1\n    while q and i < len(a):\n        n = q.popleft()\n        if a[i] != "null":\n            n.l = Node(int(a[i])); q.append(n.l)\n        i += 1\n        if i < len(a) and a[i] != "null":\n            n.r = Node(int(a[i])); q.append(n.r)\n        i += 1\n    return r\n\ndef maxPath(n):\n    global ans\n    if not n: return -10**18\n    if not n.l and not n.r: return n.v\n    L = maxPath(n.l); R = maxPath(n.r)\n    if n.l and n.r:\n        ans = max(ans, L + R + n.v)\n    return n.v + max(L, R)\n\nvals = input().split()\nvals = vals[:vals.index("-1")]\n\nroot = build(vals)\nmaxPath(root)\nprint(ans)"""
    },

    # ==============================================================================
    # GRAPHS
    # ==============================================================================

    "graph matrix ops": {
        "baby": """from networkxx import scan, GraphOps\nops = scan.int()\ng = GraphOps()\nverts = set()\nfor _ in range(ops):\n    cmd = scan.int()\n    if cmd == 1: verts.add(scan.int())\n    elif cmd == 2: \n        v = scan.int()\n        if v in verts: \n            verts.remove(v)\n            if v in g.g: g.g.remove_node(v)\n    elif cmd == 3: g.add(scan.int(), scan.int())\n    elif cmd == 4: \n        u, v = scan.int(), scan.int()\n        if g.g.has_edge(u, v): g.g.remove_edge(u, v)\n    elif cmd == 5: \n        print("Yes" if g.g.has_edge(scan.int(), scan.int()) else "No")\n\ns_verts = sorted(list(verts))\nfor i in s_verts: print(*[1 if g.g.has_edge(i, j) else 0 for j in s_verts])""",
        "python": """n = int(input())\noperations = [input().split() for _ in range(n)]\n\nvertices = set()\nedges = dict()  # key: (u,v) tuple in sorted order -> value 1/0\n\nfor op in operations:\n    if op[0] == '1':  # Add vertex\n        x = int(op[1])\n        vertices.add(x)\n    elif op[0] == '2':  # Remove vertex\n        x = int(op[1])\n        if x in vertices:\n            vertices.remove(x)\n            # Remove all edges connected to x\n            to_remove = [key for key in edges if x in key]\n            for key in to_remove:\n                del edges[key]\n    elif op[0] == '3':  # Add edge\n        u, v = int(op[1]), int(op[2])\n        if u in vertices and v in vertices:\n            edges[tuple(sorted((u, v)))] = 1\n    elif op[0] == '4':  # Remove edge\n        u, v = int(op[1]), int(op[2])\n        key = tuple(sorted((u, v)))\n        if key in edges:\n            del edges[key]\n    elif op[0] == '5':  # Check edge\n        u, v = int(op[1]), int(op[2])\n        key = tuple(sorted((u, v)))\n        if key in edges:\n            print("Yes")\n        else:\n            print("No")\n\n# Print adjacency matrix in ascending order of vertices\nsorted_vertices = sorted(vertices)\nmatrix = []\n\nfor u in sorted_vertices:\n    row = []\n    for v in sorted_vertices:\n        row.append(1 if tuple(sorted((u, v))) in edges else 0)\n    matrix.append(row)\n\nfor row in matrix:\n    print(*row,end=" ")\n    print()"""
    },

    "graph adjacency list": {
        "baby": """from networkxx import scan, GraphOps\nn, ops = scan.int(), scan.int()\ng = GraphOps()\nfor _ in range(ops):\n    cmd = scan.str()\n    if cmd == 'ADD': g.add(scan.int(), scan.int())\n    elif cmd == 'DEL': \n        u, v = scan.int(), scan.int()\n        if g.g.has_edge(u, v): g.g.remove_edge(u, v)\n    elif cmd == 'NEIGHBORS':\n        u = scan.int()\n        nbrs = sorted(list(g.g.neighbors(u))) if u in g.g else []\n        print(*(nbrs if nbrs else [-1]))\ng.print_adj_list(n)""",
        "python": _PY_INPUT + """from collections import defaultdict\nn, ops = next_int(), next_int()\nadj = defaultdict(set)\nfor _ in range(ops):\n    cmd = next_str()\n    if cmd == 'ADD':\n        u, v = next_int(), next_int(); adj[u].add(v); adj[v].add(u)\n    elif cmd == 'DEL':\n        u, v = next_int(), next_int()\n        if v in adj[u]: adj[u].remove(v)\n        if u in adj[v]: adj[v].remove(u)\n    elif cmd == 'NEIGHBORS':\n        u = next_int(); res = sorted(list(adj[u]))\n        print(*(res if res else [-1]))\nfor i in range(n):\n    print(f"{i}:{' '.join(map(str, sorted(list(adj[i]))))} " if adj[i] else f"{i}:")"""
    },

    "dfs graph traversal": {
        "baby": """from networkxx import scan, GraphOps\nv, e = scan.int(), scan.int()\ng = GraphOps()\nfor _ in range(e): g.add(scan.int(), scan.int())\nprint(*g.dfs(scan.int()))""",
        "python": """def dfs(adj_matrix, visited, v):\n    visited[v] = True\n    print(v, end=" ")\n\n    for i in range(len(adj_matrix)):\n        if adj_matrix[v][i] == 1 and not visited[i]:\n            dfs(adj_matrix, visited, i)\n\n\n# Input\nn = int(input())  # number of vertices\ne = int(input())  # number of edges\n\n# Initialize adjacency matrix\nadj_matrix = [[0 for _ in range(n)] for _ in range(n)]\n\n# Read edges\nfor _ in range(e):\n    a, b = map(int, input().split())\n    adj_matrix[a][b] = 1\n    adj_matrix[b][a] = 1  # undirected graph\n\nstart = int(input())  # starting vertex\n\n# DFS Traversal\nvisited = [False] * n\ndfs(adj_matrix, visited, start)"""
    },

    "bfs graph traversal": {
        "baby": """from networkxx import scan, GraphOps\nv, e = scan.int(), scan.int()\ng = GraphOps()\nfor _ in range(e): g.add(scan.int(), scan.int())\nres = g.bfs(scan.int())\nq = [res[0]]; vis = {res[0]}\nwhile q:\n    print(*q)\n    nq = []\n    for u in q:\n        for v in sorted(g.g.neighbors(u)): \n            if v not in vis: vis.add(v); nq.append(v)\n    q = nq""",
        "python": """from collections import deque\n\ndef bfs(adj, start, n):\n    visited = [False] * n\n    q = deque()\n    q.append(start)\n    visited[start] = True\n\n    while q:\n        size = len(q)\n        level_nodes = []  # to print each level on new line\n\n        for _ in range(size):\n            node = q.popleft()\n            level_nodes.append(node)\n\n            # traverse neighbors in increasing order (as per adjacency matrix)\n            for i in range(n):\n                if adj[node][i] == 1 and not visited[i]:\n                    visited[i] = True\n                    q.append(i)\n\n        print(*level_nodes,end=" ")\n        print()\n\n# ------- Input Handling --------\nn = int(input())\ne = int(input())\n\n# adjacency matrix\nadj = [[0]*n for _ in range(n)]\n\nfor _ in range(e):\n    a,b = map(int, input().split())\n    adj[a][b] = adj[b][a] = 1\n\nstart = int(input())\nbfs(adj, start, n)"""
    },

    "connected components": {
        "baby": """from networkxx import scan, GraphOps\nv, e = scan.int(), scan.int()\ng = GraphOps()\ng.g.add_nodes_from(range(v))\nfor _ in range(e): g.add(scan.int(), scan.int())\nfor c in g.components(): print(*c)""",
        "python": _PY_INPUT + """from collections import defaultdict\nv, e = next_int(), next_int()\nadj = defaultdict(list)\nfor _ in range(e):\n    u, w = next_int(), next_int(); adj[u].append(w); adj[w].append(u)\nvis = set(); comps = []\nfor i in range(v):\n    if i not in vis:\n        q = [i]; vis.add(i); comp = []\n        while q:\n            u = q.pop(0); comp.append(u)\n            for nbr in adj[u]:\n                if nbr not in vis: vis.add(nbr); q.append(nbr)\n        comps.append(sorted(comp))\nfor c in sorted(comps, key=lambda x: x[0]): print(*c)"""
    },

    "topological sort kahn algorithm": {
        "baby": """from networkxx import scan, GraphOps\nv, e = scan.int(), scan.int()\ng = GraphOps(directed=True)\ng.g.add_nodes_from(range(v))\nfor _ in range(e): g.add(scan.int(), scan.int())\nt = g.topo_sort()\nprint(*t if t else ["Cycle detected"])""",
        "python": """import heapq\n\ndef topological_sort_lexico(n, edges):\n    adj = [[] for _ in range(n)]\n    indegree = [0]*n\n\n    # Build graph\n    for u, v in edges:\n        adj[u].append(v)\n        indegree[v] += 1\n\n    # Min-Heap for lexicographic choice\n    heap = []\n\n    for i in range(n):\n        if indegree[i] == 0:\n            heapq.heappush(heap, i)\n\n    topo = []\n\n    while heap:\n        node = heapq.heappop(heap)   # always smallest available node\n        topo.append(node)\n\n        for nbr in adj[node]:\n            indegree[nbr] -= 1\n            if indegree[nbr] == 0:\n                heapq.heappush(heap, nbr)\n\n    # If all nodes not covered → cycle exists\n    if len(topo) != n:\n        print("Cycle detected")\n    else:\n        print(*topo,end=" ")\n        print()\n\n# ---------------- INPUT ----------------\nn, e = map(int, input().split())\nedges = []\n\nfor _ in range(e):\n    u, v = map(int, input().split())\n    edges.append((u, v))\n\ntopological_sort_lexico(n, edges)"""
    },

    "topological sort dfs based": {
        "baby": """from networkxx import scan, GraphOps\nv, e = scan.int(), scan.int()\ng = GraphOps(directed=True)\ng.g.add_nodes_from(range(v))\nfor _ in range(e): g.add(scan.int(), scan.int())\nvis = set()\nrec_stack = set()\nresult = []\ncycle = False\ndef dfs(u):\n    global cycle\n    if cycle: return\n    vis.add(u)\n    rec_stack.add(u)\n    for v in g.g.neighbors(u):\n        if v in rec_stack:\n            cycle = True\n            return\n        if v not in vis:\n            dfs(v)\n    rec_stack.remove(u)\n    result.append(u)\nfor i in range(v):\n    if i not in vis:\n        dfs(i)\nif cycle:\n    print("Cycle detected")\nelse:\n    print(*reversed(result))""",
        "python": _PY_INPUT + """sys.setrecursionlimit(5000)\nv, e = next_int(), next_int()\nadj = {i:[] for i in range(v)}\nfor _ in range(e):\n    u, w = next_int(), next_int()\n    adj[u].append(w)\nvis = set()\nrec_stack = set()\nresult = []\ncycle = False\ndef dfs(u):\n    global cycle\n    if cycle: return\n    vis.add(u)\n    rec_stack.add(u)\n    for v in adj[u]:\n        if v in rec_stack:\n            cycle = True\n            return\n        if v not in vis:\n            dfs(v)\n    rec_stack.remove(u)\n    result.append(u)\nfor i in range(v):\n    if i not in vis:\n        dfs(i)\nif cycle:\n    print("Cycle detected")\nelse:\n    print(*reversed(result))"""
    },

    "topological sort from matrix": {
        "baby": """from networkxx import scan, GraphOps\nn = scan.int()\nmat = scan.matrix(n, n)\ng = GraphOps.from_matrix(mat, directed=True)\nt = g.topo_sort()\nprint(*t)""",
        "python": _PY_INPUT + """import heapq\nn = next_int()\nindeg = {i:0 for i in range(n)}; adj = {i:[] for i in range(n)}\nfor r in range(n):\n    for c in range(n):\n        if next_int() == 1: adj[r].append(c); indeg[c] += 1\npq = [i for i in range(n) if indeg[i]==0]; heapq.heapify(pq)\nres = []\nwhile pq:\n    u = heapq.heappop(pq); res.append(u)\n    for v in adj[u]:\n        indeg[v] -= 1\n        if indeg[v] == 0: heapq.heappush(pq, v)\nprint(*res)"""
    },

    "check if graph bipartite": {
        "baby": """from networkxx import scan, GraphOps\nn = scan.int()\nmat = scan.matrix(n, n)\ng = GraphOps.from_matrix(mat)\nscan.int() # source ignored\nprint("Yes" if g.is_bipartite() else "No")""",
        "python": _PY_INPUT + """n = next_int()\nadj = {i:[] for i in range(n)}\nfor r in range(n):\n    for c in range(n): \n        if next_int(): adj[r].append(c)\nnext_str() # skip source\ncolor = {}; possible = True\nfor i in range(n):\n    if i not in color:\n        color[i] = 0; q = [i]\n        while q:\n            u = q.pop(0)\n            for v in adj[u]:\n                if v not in color: color[v] = 1 - color[u]; q.append(v)\n                elif color[v] == color[u]: possible = False\nprint("Yes" if possible else "No")"""
    },

    "count number of islands": {
        "baby": """from networkxx import scan, GraphOps\nr, c = scan.int(), scan.int()\ngrid = scan.matrix(r, c)\nprint(GraphOps.count_islands(grid))""",
        "python": """def count_islands(grid, rows, cols):\n    visited = [[False]*cols for _ in range(rows)]\n\n    # Only 4-direction\n    directions = [(1,0),(-1,0),(0,1),(0,-1)]\n\n    def dfs(r, c):\n        visited[r][c] = True\n        for dr, dc in directions:\n            nr, nc = r+dr, c+dc\n            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1 and not visited[nr][nc]:\n                dfs(nr, nc)\n\n    islands = 0\n    for i in range(rows):\n        for j in range(cols):\n            if grid[i][j] == 1 and not visited[i][j]:\n                islands += 1\n                dfs(i, j)\n\n    return islands\n\n\n# ----------- INPUT ---------------\nn = int(input())     # total rows\nm = int(input())     # total columns\ngrid = [list(map(int, input().split())) for _ in range(n)]\n\nprint(count_islands(grid, n, m))"""
    },

    "minimum network operations": {
        "baby": """from networkxx import scan, GraphOps\nn = scan.int()\nconns = []\nwhile True: \n    u = scan.int()\n    if u == -1: break\n    conns.append((u, scan.int()))\nif len(conns) < n - 1: print(-1)\nelse:\n    g = GraphOps()\n    g.g.add_nodes_from(range(n))\n    g.g.add_edges_from(conns)\n    print(len(g.components()) - 1)""",
        "python": _PY_INPUT + """n = next_int(); edges = []\nwhile True:\n    try:\n        u = next_int()\n        if u == -1: break\n        edges.append((u, next_int()))\n    except: break\nif len(edges) < n-1: print(-1)\nelse:\n    p = list(range(n))\n    def find(x): \n        if p[x]!=x: p[x]=find(p[x])\n        return p[x]\n    def union(a,b): p[find(a)] = find(b)\n    for u,v in edges: union(u,v)\n    print(len(set(find(i) for i in range(n))) - 1)"""
    },

    "job scheduling": {
        "baby": """from networkxx import scan, GraphOps\nv, e = scan.int(), scan.int()\ng = GraphOps(directed=True)\ng.g.add_nodes_from(range(1, v+1))\nfor _ in range(e): g.add(scan.int(), scan.int())\ntimes = {n: 1 for n in range(1, v+1)}\nfor u in g.topo_sort():\n    for v in g.g.neighbors(u):\n        times[v] = max(times[v], times[u] + 1)\nprint(*[times[i] for i in range(1, v+1)])""",
        "python": """import heapq\n\ndef job_scheduler(operations):\n    heap = []          # priority queue\n    order_counter = 0   # to maintain insertion order\n    output = []         # store all outputs to print later\n\n    for op in operations:\n        parts = op.split()\n\n        if parts[0] == "ADD":\n            priority = int(parts[1])\n            job_name = parts[2]\n            # Python heapq is min-heap → use negative priority for max-heap behavior\n            heapq.heappush(heap, (-priority, order_counter, job_name))\n            order_counter += 1\n\n        elif parts[0] == "EXECUTE":\n            if heap:\n                _, _, job = heapq.heappop(heap)\n                output.append(f"Executed: {job}")\n            else:\n                output.append("No jobs to execute")"""
    },

    "job priority queue": {
        "python": """import heapq\nhp=[]; cnt=0\n# Usage depends on input loop\n# For generic op list:\n# heapq.heappush(hp, (-prio, cnt, name)); cnt+=1\n# heapq.heappop(hp)"""
    },

    "check prerequisites valid": {
        "baby": """from networkxx import scan, GraphOps\nn, e = scan.int(), scan.int()\ng = GraphOps(directed=True)\nfor _ in range(e): g.add(scan.int(), scan.int())\nprint(1 if g.topo_sort() else 0)""",
        "python": _PY_INPUT + """from collections import defaultdict\nn, e = next_int(), next_int()\nadj = defaultdict(list); indeg = {i:0 for i in range(n)}\nfor _ in range(e):\n    u,v = next_int(), next_int(); adj[u].append(v); indeg[v]+=1\nq = [i for i in range(n) if indeg[i]==0]; cnt=0\nwhile q:\n    u=q.pop(0); cnt+=1\n    for v in adj[u]:\n        indeg[v]-=1\n        if indeg[v]==0: q.append(v)\nprint(1 if cnt==n else 0)"""
    },

    "flood fill algorithm": {
        "baby": """from networkxx import scan, GraphOps\nr, c = scan.int(), scan.int()\ngrid = scan.matrix(r, c)\nx, y, col = scan.int(), scan.int(), scan.int()\nres = GraphOps.flood_fill(grid, x, y, col)\nfor row in res: print(*row)""",
        "python": """# Flood Fill - Franky The Painter\n\nfrom collections import deque\n\n# Input\nn, m = map(int, input().split())\nimage = [list(map(int, input().split())) for _ in range(n)]\n\nsr, sc, newColor = map(int, input().split())   # start row, start col, new color\n\noriginalColor = image[sr][sc]\n\n# If starting color is already newColor -> no change needed\nif originalColor != newColor:\n\n    # BFS queue\n    q = deque([(sr, sc)])\n    image[sr][sc] = newColor\n\n    # 4-direction movement\n    directions = [(1,0), (-1,0), (0,1), (0,-1)]\n\n    while q:\n        r, c = q.popleft()\n\n        for dr, dc in directions:\n            nr, nc = r+dr, c+dc\n\n            if 0 <= nr < n and 0 <= nc < m and image[nr][nc] == originalColor:\n                image[nr][nc] = newColor\n                q.append((nr, nc))\n\n# Print final grid\nfor row in image:\n    print(*row,end=" ")\n    print()"""
    },

    "nasa astronaut pairs": {
        "baby": """from networkxx import scan, GraphOps\nn, p = scan.int(), scan.int()\ng = GraphOps()\ng.g.add_nodes_from(range(n))\nfor _ in range(p): g.add(scan.int(), scan.int())\nsizes = [len(c) for c in g.components()]\nrem = sum(sizes); ans = 0\nfor s in sizes: rem -= s; ans += s * rem\nprint(ans)""",
        "python": _PY_INPUT + """n, p = next_int(), next_int()\nparent = list(range(n))\ndef find(x): \n    if parent[x]!=x: parent[x]=find(parent[x])\n    return parent[x]\ndef union(a,b): parent[find(a)] = find(b)\nfor _ in range(p): union(next_int(), next_int())\ncounts = {}; \nfor i in range(n): r = find(i); counts[r] = counts.get(r, 0) + 1\nsizes = list(counts.values())\nans = 0; rem = n\nfor s in sizes: rem -= s; ans += s * rem\nprint(ans)"""
    },

    "create graph from matrix": {
        "baby": """from networkxx import scan, GraphOps\nv = scan.int()\nif not (1 <= v <= 10): print("-1")\nelse:\n    mat = scan.matrix(v, v, transformer=lambda x: int(x))\n    for row in mat: print(*row)""",
        "python": _PY_INPUT + """v = next_int()\nif not (1 <= v <= 10): print("-1")\nelse:\n    for _ in range(v):\n        print(*[next_str() for _ in range(v)])"""
    },

    "find dfs reachable nodes": {
        "baby": """from networkxx import scan, GraphOps\nn = scan.int()\nmat = scan.matrix(n, n)\ng = GraphOps.from_matrix(mat, directed=True)\nstart = scan.int()\nprint(f"Reachable nodes from {start}:", *g.dfs(start))""",
        "python": _PY_INPUT + """from collections import defaultdict\nn = next_int(); adj=defaultdict(list)\nfor r in range(n):\n    for c in range(n):\n        if next_str()=='1': adj[r].append(c)\nstart = next_int()\nvis = set(); res = []; stack=[start]\nwhile stack:\n    u = stack.pop()\n    if u not in vis:\n        vis.add(u); res.append(u)\n        for v in sorted(adj[u], reverse=True): \n            if v not in vis: stack.append(v)\nprint(f"Reachable nodes from {start}:", *res)"""
    },

    "dfs from adjacency list": {
        "baby": """from networkxx import scan, GraphOps\nv, e = scan.int(), scan.int()\ng = GraphOps(directed=True)\nfor _ in range(e): g.add(scan.int(), scan.int())\nprint(*g.dfs(scan.int()))""",
        "python": _PY_INPUT + """from collections import defaultdict\nv, e = next_int(), next_int()\nadj = defaultdict(list)\nfor _ in range(e): \n    u, w = next_int(), next_int()\n    adj[u].append(w); adj[w].append(u)\nstart=next_int(); stack=[start]; vis=set(); res=[]\nwhile stack:\n    u=stack.pop()\n    if u not in vis:\n        vis.add(u); res.append(u)\n        # Stack logic: push Descending to pop Ascending\n        for v in sorted(adj[u], reverse=True):\n            if v not in vis: stack.append(v)\nprint(*res)"""
    },

    "check if nodes connected": {
        "baby": """from networkxx import scan, GraphOps\nv = scan.int()\nmat = scan.matrix(v, v)\ng = GraphOps.from_matrix(mat)\nu, v = scan.int(), scan.int()\nprint(nx.has_path(g.g, u, v))""",
        "python": _PY_INPUT + """v=next_int(); adj={i:[] for i in range(v)}\nfor r in range(v):\n    for c in range(v):\n        if next_str()=='1': adj[r].append(c)\ns, d = next_int(), next_int()\nq=[s]; vis={s}\nfound=False\nwhile q:\n    u=q.pop(0)\n    if u==d: found=True; break\n    for nbr in adj[u]:\n        if nbr not in vis: vis.add(nbr); q.append(nbr)\nprint(found)"""
    },

    "count biconnected components": {
        "baby": """from networkxx import scan, GraphOps\nv, e = scan.int(), scan.int()\ng = GraphOps()\nfor _ in range(e): g.add(scan.int(), scan.int())\nprint(g.biconnected_count())""",
        "python": _PY_INPUT + """sys.setrecursionlimit(2000)\nv, e = next_int(), next_int()\nadj={i:[] for i in range(v)}\nfor _ in range(e): \n    try: u, w = next_int(), next_int(); adj[u].append(w); adj[w].append(u)\n    except: break\ntime=0; disc=[-1]*v; low=[-1]*v; stack=[]; count=0\ndef dfs(u, p=-1):\n    global time, count\n    disc[u]=low[u]=time; time+=1; children=0\n    for v in adj[u]:\n        if v==p: continue\n        if disc[v]!=-1: low[u]=min(low[u], disc[v]); stack.append((u,v))\n        else:\n            stack.append((u,v)); children+=1; dfs(v, u); low[u]=min(low[u], low[v])\n            if (p!=-1 and low[v]>=disc[u]) or (p==-1 and children>1):\n                count+=1\n                while stack[-1]!=(u,v): stack.pop()\n                stack.pop()\n    return\nfor i in range(v): \n    if disc[i]==-1: \n        dfs(i); \n        if stack: count+=1; stack=[]\nprint(count)"""
    },

    "detect cycle in graph": {
        "baby": """from networkxx import scan, GraphOps\nv, e = scan.int(), scan.int()\ng = GraphOps()\nfor _ in range(e): g.add(scan.int(), scan.int())\ntry: \n    nx.find_cycle(g.g)\n    print("Yes")\nexcept: print("No")""",
        "python": """def find(parent, x):\n    if parent[x] != x:\n        parent[x] = find(parent, parent[x])\n    return parent[x]\n\n\ndef union(parent, rank, x, y):\n    rootX = find(parent, x)\n    rootY = find(parent, y)\n\n    if rootX == rootY:\n        return False  # cycle detected\n\n    # union by rank\n    if rank[rootX] < rank[rootY]:\n        parent[rootX] = rootY\n    elif rank[rootX] > rank[rootY]:\n        parent[rootY] = rootX\n    else:\n        parent[rootY] = rootX\n        rank[rootX] += 1\n\n    return True\n\n\n# -------- Main Code --------\nN = int(input().strip())\nadj = [list(map(int, input().split())) for _ in range(N)]\n\nparent = [i for i in range(N)]\nrank = [0] * N\ncycle = False\n\nfor i in range(N):\n    for j in range(i + 1, N):  # only handle upper triangle for undirected graph\n        if adj[i][j] == 1:\n            if not union(parent, rank, i, j):\n                cycle = True\n                break\n    if cycle:\n        break\n\nif cycle:\n    print("Cycle detected")\nelse:\n    print("No cycle detected")"""
    },

    "find all paths between nodes": {
        "baby": """from networkxx import scan, GraphOps\nv, e = scan.int(), scan.int()\ng = GraphOps(directed=True)\nfor _ in range(e): g.add(scan.int(), scan.int())\nsrc, dst = scan.int(), scan.int()\npaths = g.all_paths(src, dst)\nfor p in paths: print(*p)""",
        "python": _PY_INPUT + """v, e = next_int(), next_int(); adj={i:[] for i in range(v)}\nfor _ in range(e): u,w=next_int(),next_int(); adj[u].append(w)\nsrc, dst = next_int(), next_int()\ndef dfs(u, path):\n    if u==dst: print(*path); return\n    for nbr in sorted(adj[u]):\n        if nbr not in path: dfs(nbr, path+[nbr])\ndfs(src, [src])"""
    },

    "check if graph symmetric": {
        "baby": """from networkxx import scan, GraphOps\nv = scan.int()\nmat = scan.matrix(v, v)\nprint("The graph is symmetric" if GraphOps.is_symmetric(mat) else "The graph is not symmetric")""",
        "python": _PY_INPUT + """v=next_int(); mat=[[next_str() for _ in range(v)] for _ in range(v)]\nsym=True\nfor r in range(v):\n    for c in range(v):\n        if mat[r][c] != mat[c][r]: sym=False; break\nprint("The graph is symmetric" if sym else "The graph is not symmetric")"""
    },

    "find mother vertex": {
        "baby": """from networkxx import scan, GraphOps\nn, e = scan.int(), scan.int()\ng = GraphOps(directed=True)\ng.g.add_nodes_from(range(n))\nfor _ in range(e): g.add(scan.int(), scan.int())\nprint(g.mother_vertex(n))""",
        "python": _PY_INPUT + """sys.setrecursionlimit(5000)\nn, e = next_int(), next_int(); adj={i:[] for i in range(n)}\nfor _ in range(e): u,w=next_int(),next_int(); adj[u].append(w)\nvis=set(); last=0\ndef dfs(u): \n    vis.add(u)\n    for v in adj[u]: \n        if v not in vis: dfs(v)\nfor i in range(n): \n    if i not in vis: dfs(i); last=i\nvis=set(); dfs(last)\nprint(last if len(vis)==n else -1)"""
    },

    "check if path exists": {
        "baby": """from networkxx import scan, GraphOps\nn = scan.int()\ne = scan.int()\ng = GraphOps()\nfor _ in range(e): g.add(scan.int(), scan.int())\nsrc, dst = scan.int(), scan.int()\nprint("true" if nx.has_path(g.g, src, dst) else "false")""",
        "python": _PY_INPUT + """n, e = next_int(), next_int(); adj={i:[] for i in range(n)}\nfor _ in range(e): u,w=next_int(),next_int(); adj[u].append(w); adj[w].append(u)\ns, t = next_int(), next_int()\nq=[s]; vis={s}; found=False\nwhile q:\n    u=q.pop(0)\n    if u==t: found=True; break\n    for v in adj[u]:\n        if v not in vis: vis.add(v); q.append(v)\nprint("true" if found else "false")"""
    },

    "find grid path from 1 to 2": {
        "baby": """from networkxx import scan, GraphOps\nn = scan.int()\ngrid = scan.matrix(n, n)\nprint(1 if GraphOps.grid_path(grid, 1, 2, {3}) else 0)""",
        "python": _PY_INPUT + """n = next_int(); grid=[]; start=None\nfor r in range(n): \n    row=[next_int() for _ in range(n)]; grid.append(row)\n    if 1 in row: start=(r, row.index(1))\nq=[start]; vis={start}; found=False\nwhile q:\n    r,c=q.pop(0)\n    if grid[r][c]==2: found=True; break\n    for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)]:\n        nr,nc=r+dr,c+dc\n        if 0<=nr<n and 0<=nc<n and (nr,nc) not in vis and grid[nr][nc] in [2,3]:\n            vis.add((nr,nc)); q.append((nr,nc))\nprint(1 if found else 0)"""
    },

    "transpose graph matrix": {
        "baby": """from networkxx import scan, GraphOps\nv = scan.int()\nmat = scan.matrix(v, v)\nres = GraphOps.transpose_matrix(mat)\nfor row in res: print(*row)""",
        "python": _PY_INPUT + """v = next_int(); mat=[[next_str() for _ in range(v)] for _ in range(v)]\nt = [[mat[j][i] for j in range(v)] for i in range(v)]\nfor row in t: print(*row)"""
    },

    "count islands in grid": {
        "baby": """from networkxx import scan, GraphOps\nn, m = scan.int(), scan.int()\ngrid = [list(scan.str()) for _ in range(n)]\nprint(GraphOps.count_islands(grid))""",
        "python": _PY_INPUT + """sys.setrecursionlimit(5000)\nn, m = next_int(), next_int()\ngrid=[list(next_str()) for _ in range(n)]\nvis=set(); cnt=0\ndef dfs(x,y):\n    if not (0<=x<n and 0<=y<m) or (x,y) in vis or grid[x][y]=='0': return\n    vis.add((x,y))\n    for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]: dfs(x+dx, y+dy)\nfor i in range(n):\n    for j in range(m):\n        if grid[i][j]=='1' and (i,j) not in vis: dfs(i,j); cnt+=1\nprint(cnt)"""
    },

    "find vertex degrees": {
        "baby": """from networkxx import scan, GraphOps\nv = scan.int()\ne = scan.int()\ng = GraphOps(directed=True)\ng.g.add_nodes_from(range(v))\nfor _ in range(e): g.add(scan.int(), scan.int())\ng.print_degrees(v)""",
        "python": _PY_INPUT + """v, e = next_int(), next_int()\nind={i:0 for i in range(v)}; outd={i:0 for i in range(v)}\nfor _ in range(e):\n    u, w = next_int(), next_int()\n    outd[u]+=1; ind[w]+=1\nfor i in range(v): print(f"Vertex {i}: In-degree = {ind[i]}, Out-degree = {outd[i]}")"""
    },

    # ==============================================================================
    # DIVIDE AND CONQUER
    # ==============================================================================

    "binary search with comparisons": {
        "baby": """from networkxx import scan\narr = scan.list_fixed(scan.int())\ntarget = scan.int()\ncomparisons = 0\nleft, right = 0, len(arr) - 1\nfound = False\nwhile left <= right:\n    mid = (left + right) // 2\n    comparisons += 1\n    if arr[mid] == target:\n        found = True\n        break\n    elif arr[mid] < target:\n        left = mid + 1\n    else:\n        right = mid - 1\nprint(comparisons)\nprint("found" if found else "not found")""",
        "python": _PY_INPUT + """arr = [next_int() for _ in range(next_int())]\ntarget = next_int()\ncomparisons = 0\nleft, right = 0, len(arr) - 1\nfound = False\nwhile left <= right:\n    mid = (left + right) // 2\n    comparisons += 1\n    if arr[mid] == target:\n        found = True\n        break\n    elif arr[mid] < target:\n        left = mid + 1\n    else:\n        right = mid - 1\nprint(comparisons)\nprint("found" if found else "not found")"""
    },

    "find first last position": {
        "baby": """from networkxx import scan\narr = scan.list_fixed(scan.int())\ntarget = scan.int()\ndef find_first(arr, target):\n    left, right = 0, len(arr) - 1\n    result = -1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            result = mid\n            right = mid - 1\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return result\ndef find_last(arr, target):\n    left, right = 0, len(arr) - 1\n    result = -1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            result = mid\n            left = mid + 1\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return result\nfirst = find_first(arr, target)\nlast = find_last(arr, target)\nprint(f"[{first}, {last}]")""",
        "python": _PY_INPUT + """arr = [next_int() for _ in range(next_int())]\ntarget = next_int()\ndef find_first(arr, target):\n    left, right = 0, len(arr) - 1\n    result = -1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            result = mid\n            right = mid - 1\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return result\ndef find_last(arr, target):\n    left, right = 0, len(arr) - 1\n    result = -1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            result = mid\n            left = mid + 1\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return result\nfirst = find_first(arr, target)\nlast = find_last(arr, target)\nprint(f"[{first}, {last}]")"""
    },

    "count inversions in array": {
        "baby": """from networkxx import scan\narr = scan.list_fixed(scan.int())\ncount = 0\ndef merge_count(arr, temp, left, mid, right):\n    global count\n    i, j, k = left, mid + 1, left\n    while i <= mid and j <= right:\n        if arr[i] <= arr[j]:\n            temp[k] = arr[i]\n            i += 1\n        else:\n            temp[k] = arr[j]\n            count += (mid - i + 1)\n            j += 1\n        k += 1\n    while i <= mid:\n        temp[k] = arr[i]\n        i += 1\n        k += 1\n    while j <= right:\n        temp[k] = arr[j]\n        j += 1\n        k += 1\n    for i in range(left, right + 1):\n        arr[i] = temp[i]\ndef merge_sort_count(arr, temp, left, right):\n    if left < right:\n        mid = (left + right) // 2\n        merge_sort_count(arr, temp, left, mid)\n        merge_sort_count(arr, temp, mid + 1, right)\n        merge_count(arr, temp, left, mid, right)\ntemp = [0] * len(arr)\nmerge_sort_count(arr, temp, 0, len(arr) - 1)\nprint(count)""",
        "python": _PY_INPUT + """arr = [next_int() for _ in range(next_int())]\ncount = 0\ndef merge_count(arr, temp, left, mid, right):\n    global count\n    i, j, k = left, mid + 1, left\n    while i <= mid and j <= right:\n        if arr[i] <= arr[j]:\n            temp[k] = arr[i]\n            i += 1\n        else:\n            temp[k] = arr[j]\n            count += (mid - i + 1)\n            j += 1\n        k += 1\n    while i <= mid:\n        temp[k] = arr[i]\n        i += 1\n        k += 1\n    while j <= right:\n        temp[k] = arr[j]\n        j += 1\n        k += 1\n    for i in range(left, right + 1):\n        arr[i] = temp[i]\ndef merge_sort_count(arr, temp, left, right):\n    if left < right:\n        mid = (left + right) // 2\n        merge_sort_count(arr, temp, left, mid)\n        merge_sort_count(arr, temp, mid + 1, right)\n        merge_count(arr, temp, left, mid, right)\ntemp = [0] * len(arr)\nmerge_sort_count(arr, temp, 0, len(arr) - 1)\nprint(count)"""
    },

    "randomized quick sort": {
        "baby": """from networkxx import scan\nimport random\narr = scan.list_fixed(scan.int())\ncomparisons = 0\nrecursive_calls = 0\ndef partition(arr, low, high):\n    global comparisons\n    pivot_idx = random.randint(low, high)\n    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]\n    pivot = arr[high]\n    i = low - 1\n    for j in range(low, high):\n        comparisons += 1\n        if arr[j] < pivot:\n            i += 1\n            arr[i], arr[j] = arr[j], arr[i]\n    arr[i + 1], arr[high] = arr[high], arr[i + 1]\n    return i + 1\ndef quick_sort(arr, low, high):\n    global recursive_calls\n    if low < high:\n        recursive_calls += 1\n        pi = partition(arr, low, high)\n        quick_sort(arr, low, pi - 1)\n        quick_sort(arr, pi + 1, high)\nquick_sort(arr, 0, len(arr) - 1)\nprint(*arr)\nprint(comparisons)\nprint(recursive_calls)""",
        "python": _PY_INPUT + """import random\narr = [next_int() for _ in range(next_int())]\ncomparisons = 0\nrecursive_calls = 0\ndef partition(arr, low, high):\n    global comparisons\n    pivot_idx = random.randint(low, high)\n    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]\n    pivot = arr[high]\n    i = low - 1\n    for j in range(low, high):\n        comparisons += 1\n        if arr[j] < pivot:\n            i += 1\n            arr[i], arr[j] = arr[j], arr[i]\n    arr[i + 1], arr[high] = arr[high], arr[i + 1]\n    return i + 1\ndef quick_sort(arr, low, high):\n    global recursive_calls\n    if low < high:\n        recursive_calls += 1\n        pi = partition(arr, low, high)\n        quick_sort(arr, low, pi - 1)\n        quick_sort(arr, pi + 1, high)\nquick_sort(arr, 0, len(arr) - 1)\nprint(*arr)\nprint(comparisons)\nprint(recursive_calls)"""
    },

    "maximum subarray sum divide conquer": {
        "baby": """from networkxx import scan\narr = scan.list_fixed(scan.int())\ndef max_crossing_sum(arr, left, mid, right):\n    left_sum = float('-inf')\n    total = 0\n    for i in range(mid, left - 1, -1):\n        total += arr[i]\n        left_sum = max(left_sum, total)\n    right_sum = float('-inf')\n    total = 0\n    for i in range(mid + 1, right + 1):\n        total += arr[i]\n        right_sum = max(right_sum, total)\n    return left_sum + right_sum\ndef max_subarray_sum(arr, left, right):\n    if left == right:\n        return arr[left]\n    mid = (left + right) // 2\n    return max(max_subarray_sum(arr, left, mid),\n               max_subarray_sum(arr, mid + 1, right),\n               max_crossing_sum(arr, left, mid, right))\nprint(max_subarray_sum(arr, 0, len(arr) - 1))""",
        "python": _PY_INPUT + """arr = [next_int() for _ in range(next_int())]\ndef max_crossing_sum(arr, left, mid, right):\n    left_sum = float('-inf')\n    total = 0\n    for i in range(mid, left - 1, -1):\n        total += arr[i]\n        left_sum = max(left_sum, total)\n    right_sum = float('-inf')\n    total = 0\n    for i in range(mid + 1, right + 1):\n        total += arr[i]\n        right_sum = max(right_sum, total)\n    return left_sum + right_sum\ndef max_subarray_sum(arr, left, right):\n    if left == right:\n        return arr[left]\n    mid = (left + right) // 2\n    return max(max_subarray_sum(arr, left, mid),\n               max_subarray_sum(arr, mid + 1, right),\n               max_crossing_sum(arr, left, mid, right))\nprint(max_subarray_sum(arr, 0, len(arr) - 1))"""
    },

    "find kth largest element": {
        "baby": """from networkxx import scan\narr = scan.list_fixed(scan.int())\nk = scan.int()\ndef partition(arr, low, high):\n    pivot = arr[high]\n    i = low - 1\n    for j in range(low, high):\n        if arr[j] >= pivot:\n            i += 1\n            arr[i], arr[j] = arr[j], arr[i]\n    arr[i + 1], arr[high] = arr[high], arr[i + 1]\n    return i + 1\ndef quick_select(arr, low, high, k):\n    if low <= high:\n        pi = partition(arr, low, high)\n        if pi == k - 1:\n            return arr[pi]\n        elif pi > k - 1:\n            return quick_select(arr, low, pi - 1, k)\n        else:\n            return quick_select(arr, pi + 1, high, k)\nprint(quick_select(arr, 0, len(arr) - 1, k))""",
        "python": _PY_INPUT + """arr = [next_int() for _ in range(next_int())]\nk = next_int()\ndef partition(arr, low, high):\n    pivot = arr[high]\n    i = low - 1\n    for j in range(low, high):\n        if arr[j] >= pivot:\n            i += 1\n            arr[i], arr[j] = arr[j], arr[i]\n    arr[i + 1], arr[high] = arr[high], arr[i + 1]\n    return i + 1\ndef quick_select(arr, low, high, k):\n    if low <= high:\n        pi = partition(arr, low, high)\n        if pi == k - 1:\n            return arr[pi]\n        elif pi > k - 1:\n            return quick_select(arr, low, pi - 1, k)\n        else:\n            return quick_select(arr, pi + 1, high, k)\nprint(quick_select(arr, 0, len(arr) - 1, k))"""
    },

    # ==============================================================================
    # HASHING
    # ==============================================================================

    "hash table separate chaining": {
        "baby": """from networkxx import scan\nfrom collections import defaultdict\nclass HashTable:\n    def __init__(self, size):\n        self.size = size\n        self.table = defaultdict(list)\n    def hash(self, key):\n        return key % self.size\n    def insert(self, key):\n        idx = self.hash(key)\n        if key not in self.table[idx]:\n            self.table[idx].append(key)\n    def delete(self, key):\n        idx = self.hash(key)\n        if key in self.table[idx]:\n            self.table[idx].remove(key)\n    def search(self, key):\n        idx = self.hash(key)\n        return key in self.table[idx]\n    def display(self):\n        for i in range(self.size):\n            if self.table[i]:\n                print(f"{i}: {' -> '.join(map(str, self.table[i]))}")\n            else:\n                print(f"{i}: Empty")\nm = scan.int()\nht = HashTable(m)\nn = scan.int()\nfor _ in range(n):\n    op = scan.str()\n    if op == 'insert':\n        ht.insert(scan.int())\n    elif op == 'delete':\n        ht.delete(scan.int())\n    elif op == 'search':\n        print("found" if ht.search(scan.int()) else "not found")\nht.display()""",
        "python": _PY_INPUT + """from collections import defaultdict\nclass HashTable:\n    def __init__(self, size):\n        self.size = size\n        self.table = defaultdict(list)\n    def hash(self, key):\n        return key % self.size\n    def insert(self, key):\n        idx = self.hash(key)\n        if key not in self.table[idx]:\n            self.table[idx].append(key)\n    def delete(self, key):\n        idx = self.hash(key)\n        if key in self.table[idx]:\n            self.table[idx].remove(key)\n    def search(self, key):\n        idx = self.hash(key)\n        return key in self.table[idx]\n    def display(self):\n        for i in range(self.size):\n            if self.table[i]:\n                print(f"{i}: {' -> '.join(map(str, self.table[i]))}")\n            else:\n                print(f"{i}: Empty")\nm = next_int()\nht = HashTable(m)\nn = next_int()\nfor _ in range(n):\n    op = next_str()\n    if op == 'insert':\n        ht.insert(next_int())\n    elif op == 'delete':\n        ht.delete(next_int())\n    elif op == 'search':\n        print("found" if ht.search(next_int()) else "not found")\nht.display()"""
    },

    "find frequency of elements": {
        "baby": """from networkxx import scan\nfrom collections import Counter\narr = scan.list_fixed(scan.int())\nfreq = Counter(arr)\nfor key in sorted(freq.keys()):\n    print(f"{key}: {freq[key]}")""",
        "python": _PY_INPUT + """from collections import Counter\narr = [next_int() for _ in range(next_int())]\nfreq = Counter(arr)\nfor key in sorted(freq.keys()):\n    print(f"{key}: {freq[key]}")"""
    },

    "duplicate within distance k": {
        "baby": """from networkxx import scan\narr = scan.list_fixed(scan.int())\nk = scan.int()\nseen = {}\nfound = False\nfor i, num in enumerate(arr):\n    if num in seen and i - seen[num] <= k:\n        found = True\n        break\n    seen[num] = i\nprint("Yes" if found else "No")""",
        "python": _PY_INPUT + """arr = [next_int() for _ in range(next_int())]\nk = next_int()\nseen = {}\nfound = False\nfor i, num in enumerate(arr):\n    if num in seen and i - seen[num] <= k:\n        found = True\n        break\n    seen[num] = i\nprint("Yes" if found else "No")"""
    },

    "two sum check exists": {
        "baby": """from networkxx import scan\narr = scan.list_fixed(scan.int())\ntarget = scan.int()\nseen = set()\nfound = False\nfor num in arr:\n    if target - num in seen:\n        found = True\n        break\n    seen.add(num)\nprint("Yes" if found else "No")""",
        "python": _PY_INPUT + """arr = [next_int() for _ in range(next_int())]\ntarget = next_int()\nseen = set()\nfound = False\nfor num in arr:\n    if target - num in seen:\n        found = True\n        break\n    seen.add(num)\nprint("Yes" if found else "No")"""
    },

    "two sum return indices": {
        "baby": """from networkxx import scan\narr = scan.list_fixed(scan.int())\ntarget = scan.int()\nseen = {}\nfor i, num in enumerate(arr):\n    complement = target - num\n    if complement in seen:\n        print(f"[{seen[complement]}, {i}]")\n        break\n    seen[num] = i\nelse:\n    print("[-1, -1]")""",
        "python": _PY_INPUT + """arr = [next_int() for _ in range(next_int())]\ntarget = next_int()\nseen = {}\nfor i, num in enumerate(arr):\n    complement = target - num\n    if complement in seen:\n        print(f"[{seen[complement]}, {i}]")\n        break\n    seen[num] = i\nelse:\n    print("[-1, -1]")"""
    },

    # ==============================================================================
    # ALGO & MISC
    # ==============================================================================

    "merge sort": {
        "python": """recursive = 0\ncomparison = 0\n\ndef merge(arr, start, mid, end):\n    global comparison\n    temp = []\n    s, e = start, mid + 1\n\n    while s <= mid and e <= end:\n        comparison += 1\n        if arr[s] <= arr[e]:\n            temp.append(arr[s])\n            s += 1\n        else:\n            temp.append(arr[e])\n            e += 1\n\n    while s <= mid:\n        temp.append(arr[s])\n        s += 1\n\n    while e <= end:\n        temp.append(arr[e])\n        e += 1\n\n    for i in range(start, end + 1):\n        arr[i] = temp[i - start]\n\n\ndef merge_sort(arr, start, end):\n    global recursive\n    recursive += 1\n    if start >= end:\n        return\n    mid = (start + end) // 2\n    merge_sort(arr, start, mid)\n    merge_sort(arr, mid + 1, end)\n    merge(arr, start, mid, end)\n\nn = int(input())\narr = list(map(int, input().split()))\n\nmerge_sort(arr, 0, n - 1)\n\nprint(*arr,end=" ")\nprint()\nprint(recursive)\nprint(comparison)"""
    },

    "quick sort": {
        "python": """comparisons = 0\nrecursiveCalls = 0\n\ndef partition(arr, low, high):\n    global comparisons\n    pivot = arr[high]\n    i = low - 1\n\n    for j in range(low, high):\n        comparisons += 1\n        if arr[j] < pivot:\n            i += 1\n            arr[i], arr[j] = arr[j], arr[i]\n\n    arr[i + 1], arr[high] = arr[high], arr[i + 1]\n    return i + 1\n\n\ndef quickSort(arr, low, high):\n    global recursiveCalls\n    if low < high:\n        recursiveCalls += 1\n\n        pi = partition(arr, low, high)\n\n        quickSort(arr, low, pi - 1)\n        quickSort(arr, pi + 1, high)\n\n\n# Main Program\nn = int(input())\narr = list(map(int, input().split()))\n\nquickSort(arr, 0, n - 1)\n\n# Output\nprint(*arr,end=" ")\nprint()\nprint(comparisons)\nprint(recursiveCalls)"""
    },

    "merge two sorted arrays": {
        "python": """lst1=list(map(int,input().split()))\nm=int(input())\nlst2=list(map(int,input().split()))\nn=int(input())\nmerge=sorted(lst1[:m]+lst2[:n])\nprint(merge)"""
    },

    "sort by bit count": {
        "python": """n = int(input())\narr = list(map(int, input().split()))\n\n# Sort by bit count (descending), Python sort is stable automatically\narr.sort(key=lambda x: -x.bit_count())\n\nprint("[" + ", ".join(map(str, arr)) + "]")"""
    },

    "distinct elements in window": {
        "python": """n = int(input())\narr = list(map(int, input().split()))\nk = int(input())\nfreq = {}\nd = 0\nfor i in range(k):\n    if freq.get(arr[i], 0) == 0:\n        d += 1\n    freq[arr[i]] = freq.get(arr[i], 0) + 1\nprint(d)\n\nfor i in range(k, n):\n    out = arr[i - k]\n    freq[out] -= 1\n    if freq[out] == 0:\n        d -= 1\n    if freq.get(arr[i], 0) == 0:\n        d += 1\n    freq[arr[i]] = freq.get(arr[i], 0) + 1\n    print(d)"""
    },

    "group words by anagrams": {
        "python": """n = int(input())\nwords = input().split()\ngroups = {}\nfor s in words:\n    key = ''.join(sorted(s))\n    if key not in groups:\n        groups[key] = []\n    groups[key].append(s)\nres = list(groups.values())\nres.sort(key=lambda x: x[0])\nfor g in res:\n    print(" ".join(g),end=" ")\n    print()"""
    },

    "find least k unique elements": {
        "python": """n = int(input())\nnums = list(map(int, input().split()))\nk = int(input())\n\ntemp = []\n\n# Keep numbers that appear only once (no duplicates ahead)\nfor i in range(n):\n    c = 0\n    for j in range(i + 1, n):\n        if nums[i] == nums[j]:\n            c += 1\n    if c == 0:\n        temp.append(nums[i])\n\ntemp.sort()\n\nprint("[", end="")\nfor i in range(k - 1, -1, -1):\n    print(temp[i], end="")\n    if i != 0:\n        print(", ", end="")\nprint("]", end="")"""
    },

    "find top k frequent elements": {
        "baby": """from networkxx import scan\nfrom collections import Counter\nn = scan.int()\narr = scan.list_fixed(n)\nk = scan.int()\nfor x, _ in Counter(arr).most_common(k):\n    print(x, end=" ")""",
        "python": """from collections import Counter\nn = int(input())\narr = list(map(int, input().split()))\nk = int(input())\nfor x, _ in Counter(arr).most_common(k):\n    print(x, end=" ")"""
    },

    "quadratic probing": {
        "python": """def main():\n    n, m = map(int, input().split())\n    if n == 0:\n        print("Hash Table is empty")\n        return\n    keys = list(map(int, input().split()))\n    HT = [-1] * m\n    for key in keys:\n        index = key % m\n        if HT[index] == -1:\n            HT[index] = key\n        else:\n            inserted = False\n            for i in range(1, m):\n                new_index = (index + i * i) % m\n                if HT[new_index] == -1:\n                    HT[new_index] = key\n                    inserted = True\n                    break\n            if not inserted:\n                print(f"Hash table is full. Cannot insert records from key {key}")\n                break\n    for i in range(m):\n        print(f"T[{i}] -> {HT[i]}")\nif __name__ == "__main__":\n    main()"""
    },

    "linear probing": {
        "python": """def main():\n    n, m = map(int, input().split())\n    if n == 0:\n        print("Hash Table is empty")\n        return\n    keys = list(map(int, input().split()))\n    HT = [-1] * m\n    for key in keys:\n        index = key % m\n        if HT[index] == -1:\n            HT[index] = key\n        else:\n            inserted = False\n            for i in range(1, m):\n                new_index = (index + i) % m\n                if HT[new_index] == -1:\n                    HT[new_index] = key\n                    inserted = True\n                    break\n            if not inserted:\n                print(f"Hash table is full. Cannot insert records from key {key}")\n                break\n    for i in range(m):\n        print(f"T[{i}] -> {HT[i]}")\nif __name__ == "__main__":\n    main()"""
    },
    
    "convert bst to minheap": {
        "baby": """from networkxx import scan, TreeOps\nfrom collections import deque\nclass Node:\n    def __init__(s,v): s.data=v; s.left=None; s.right=None\ndef build_tree(levels):\n    if not levels or levels[0]==-1: return None\n    root=Node(levels[0]); q=deque([root]); i=1\n    while q and i<len(levels):\n        n=q.popleft()\n        if i<len(levels) and levels[i]!=-1: n.left=Node(levels[i]); q.append(n.left)\n        i+=1\n        if i<len(levels) and levels[i]!=-1: n.right=Node(levels[i]); q.append(n.right)\n        i+=1\n    return root\ndef inorder(r,res):\n    if r: inorder(r.left,res); res.append(r.data); inorder(r.right,res)\ndef preorder_assign(r,s,idx):\n    if not r: return idx\n    r.data=s[idx]; idx+=1\n    idx=preorder_assign(r.left,s,idx)\n    idx=preorder_assign(r.right,s,idx)\n    return idx\ndef preorder_print(r):\n    if r: print(r.data,end=' '); preorder_print(r.left); preorder_print(r.right)\nlevels=scan.list_until(sentinel=None)\nroot=build_tree(levels)\nsorted_vals=[]\ninorder(root,sorted_vals)\npreorder_assign(root,sorted_vals,0)\npreorder_print(root)""",
        "python": """from collections import deque\n\n# Node class\nclass Node:\n    def __init__(self, val):\n        self.data = val\n        self.left = None\n        self.right = None\n\n# Build BST from level-order input\ndef build_tree(levels):\n    if not levels or levels[0] == -1:\n        return None\n    root = Node(levels[0])\n    q = deque([root])\n    i = 1\n    while q and i < len(levels):\n        node = q.popleft()\n        if i < len(levels) and levels[i] != -1:\n            node.left = Node(levels[i])\n            q.append(node.left)\n        i += 1\n        if i < len(levels) and levels[i] != -1:\n            node.right = Node(levels[i])\n            q.append(node.right)\n        i += 1\n    return root\n\n# Inorder traversal to collect BST nodes in sorted order\ndef inorder(root, res):\n    if not root:\n        return\n    inorder(root.left, res)\n    res.append(root.data)\n    inorder(root.right, res)\n\n# Preorder traversal to assign values from sorted array\ndef preorder_assign(root, sorted_vals, index):\n    if not root:\n        return index\n    root.data = sorted_vals[index]\n    index += 1\n    index = preorder_assign(root.left, sorted_vals, index)\n    index = preorder_assign(root.right, sorted_vals, index)\n    return index\n\n# Preorder traversal to print final heap\ndef preorder_print(root):\n    if not root:\n        return\n    print(root.data, end=' ')\n    preorder_print(root.left)\n    preorder_print(root.right)\n\n# ---- MAIN ----\nlevels = list(map(int, input().split()))\nroot = build_tree(levels)\n\nsorted_vals = []\ninorder(root, sorted_vals)\n\npreorder_assign(root, sorted_vals, 0)\npreorder_print(root)"""
    },

    "make min heap from array": {
        "baby": """from networkxx import scan\nimport heapq\nn = scan.int()\narr = scan.list_fixed(n)\nheapq.heapify(arr)\nprint(*arr)""",
        "python": """import heapq\nn = int(input())\narr = list(map(int, input().split()))\nheapq.heapify(arr)\nprint(*arr)"""
    },

    "make max heap from array": {
        "baby": """from networkxx import scan\nimport heapq\nn = scan.int()\narr = scan.list_fixed(n)\narr = [-x for x in arr]\nheapq.heapify(arr)\narr = [-x for x in arr]\nprint(*arr)""",
        "python": """import heapq\nn = int(input())\narr = list(map(int, input().split()))\narr = [-x for x in arr]\nheapq.heapify(arr)\narr = [-x for x in arr]\nprint(*arr)"""
    },

    "check if bt is heap": {
        "baby": """from networkxx import scan, TreeOps\nroot = TreeOps.from_level_order(scan.list_until(sentinel=None))\ndef is_complete(root):\n    if not root: return True\n    q = [root]; found_null = False\n    while q:\n        node = q.pop(0)\n        if not node:\n            found_null = True\n        else:\n            if found_null: return False\n            q.append(node.left)\n            q.append(node.right)\n    return True\ndef is_heap(root):\n    if not root: return True\n    if root.left and root.data > root.left.data: return False\n    if root.right and root.data > root.right.data: return False\n    return is_heap(root.left) and is_heap(root.right)\nif not root: print(1)\nelif is_complete(root) and is_heap(root): print(1)\nelse: print(0)""",
        "python": """from collections import deque\nclass Node:\n    def __init__(s,v): s.data=v; s.left=None; s.right=None\ndef build_tree(levels):\n    if not levels: return None\n    nodes=[Node(int(x)) if x!='null' and x!='-1' else None for x in levels]\n    if not nodes or not nodes[0]: return None\n    root=nodes[0]; q=deque([root]); i=1\n    while q and i<len(nodes):\n        n=q.popleft()\n        if i<len(nodes) and nodes[i]: n.left=nodes[i]; q.append(n.left)\n        i+=1\n        if i<len(nodes) and nodes[i]: n.right=nodes[i]; q.append(n.right)\n        i+=1\n    return root\ndef is_complete(root):\n    if not root: return True\n    q=deque([root]); found_null=False\n    while q:\n        n=q.popleft()\n        if not n: found_null=True\n        else:\n            if found_null: return False\n            q.append(n.left); q.append(n.right)\n    return True\ndef is_heap(root):\n    if not root: return True\n    if root.left and root.data>root.left.data: return False\n    if root.right and root.data>root.right.data: return False\n    return is_heap(root.left) and is_heap(root.right)\nlevels=input().split()\nroot=build_tree(levels)\nif not root: print(1)\nelif is_complete(root) and is_heap(root): print(1)\nelse: print(0)"""
    },

    # ==============================================================================
    # ADVANCED DATA STRUCTURES
    # ==============================================================================

    "binomial heap merge": {
        "baby": """from networkxx import scan\n# Note: Full binomial heap implementation is complex\n# This is a simplified version using heapq for demonstration\nimport heapq\nn1 = scan.int()\nheap1 = scan.list_fixed(n1)\nn2 = scan.int()\nheap2 = scan.list_fixed(n2)\nmerged = list(heapq.merge(heap1, heap2))\nprint(*merged)""",
        "python": _PY_INPUT + """import heapq\nn1 = next_int()\nheap1 = [next_int() for _ in range(n1)]\nn2 = next_int()\nheap2 = [next_int() for _ in range(n2)]\nheapq.heapify(heap1)\nheapq.heapify(heap2)\nmerged = list(heapq.merge(heap1, heap2))\nprint(*merged)"""
    },

    "binomial heap extract min": {
        "baby": """from networkxx import scan\nimport heapq\nn = scan.int()\nheap = scan.list_fixed(n)\nheapq.heapify(heap)\nif heap:\n    min_val = heapq.heappop(heap)\n    print(f"Minimum: {min_val}")\n    print(f"Remaining heap: {heap}")\nelse:\n    print("Heap is empty")""",
        "python": _PY_INPUT + """import heapq\nn = next_int()\nheap = [next_int() for _ in range(n)]\nheapq.heapify(heap)\nif heap:\n    min_val = heapq.heappop(heap)\n    print(f"Minimum: {min_val}")\n    print(f"Remaining heap: {heap}")\nelse:\n    print("Heap is empty")"""
    },

    "detect cycle union find": {
        "baby": """from networkxx import scan\nn = scan.int()\ne = scan.int()\nparent = list(range(n))\nrank = [0] * n\ndef find(x):\n    if parent[x] != x:\n        parent[x] = find(parent[x])\n    return parent[x]\ndef union(x, y):\n    px, py = find(x), find(y)\n    if px == py:\n        return True  # Cycle detected\n    if rank[px] < rank[py]:\n        parent[px] = py\n    elif rank[px] > rank[py]:\n        parent[py] = px\n    else:\n        parent[py] = px\n        rank[px] += 1\n    return False\ncycle = False\nfor _ in range(e):\n    u, v = scan.int(), scan.int()\n    if union(u, v):\n        cycle = True\n        break\nprint("Cycle detected" if cycle else "No cycle detected")""",
        "python": _PY_INPUT + """n = next_int()\ne = next_int()\nparent = list(range(n))\nrank = [0] * n\ndef find(x):\n    if parent[x] != x:\n        parent[x] = find(parent[x])\n    return parent[x]\ndef union(x, y):\n    px, py = find(x), find(y)\n    if px == py:\n        return True  # Cycle detected\n    if rank[px] < rank[py]:\n        parent[px] = py\n    elif rank[px] > rank[py]:\n        parent[py] = px\n    else:\n        parent[py] = px\n        rank[px] += 1\n    return False\ncycle = False\nfor _ in range(e):\n    u, v = next_int(), next_int()\n    if union(u, v):\n        cycle = True\n        break\nprint("Cycle detected" if cycle else "No cycle detected")"""
    },

    "trie data structure": {
        "baby": """from networkxx import scan\nclass TrieNode:\n    def __init__(self):\n        self.children = {}\n        self.is_end = False\n\nclass Trie:\n    def __init__(self):\n        self.root = TrieNode()\n    \n    def insert(self, word):\n        node = self.root\n        for char in word:\n            if char not in node.children:\n                node.children[char] = TrieNode()\n            node = node.children[char]\n        node.is_end = True\n    \n    def search(self, word):\n        node = self.root\n        for char in word:\n            if char not in node.children:\n                return False\n            node = node.children[char]\n        return node.is_end\n\ntrie = Trie()\nn = scan.int()\nfor _ in range(n):\n    op = scan.str()\n    if op == 'insert':\n        trie.insert(scan.str())\n    elif op == 'search':\n        print("True" if trie.search(scan.str()) else "False")""",
        "python": _PY_INPUT + """class TrieNode:\n    def __init__(self):\n        self.children = {}\n        self.is_end = False\n\nclass Trie:\n    def __init__(self):\n        self.root = TrieNode()\n    \n    def insert(self, word):\n        node = self.root\n        for char in word:\n            if char not in node.children:\n                node.children[char] = TrieNode()\n            node = node.children[char]\n        node.is_end = True\n    \n    def search(self, word):\n        node = self.root\n        for char in word:\n            if char not in node.children:\n                return False\n            node = node.children[char]\n        return node.is_end\n\ntrie = Trie()\nn = next_int()\nfor _ in range(n):\n    op = next_str()\n    if op == 'insert':\n        trie.insert(next_str())\n    elif op == 'search':\n        print("True" if trie.search(next_str()) else "False")"""
    }
}

# ------------------------------------------------------------------------------ 
# Aliases for fuzzy/short queries (map alias -> canonical _DOCS key)
# ------------------------------------------------------------------------------ 
_ALIASES = {
    # Hashing lab style names
    "hash table using open hashing": "hash table separate chaining",
    "separate chaining": "hash table separate chaining",
    "open hashing": "hash table separate chaining",
    "count frequencies": "find frequency of elements",
    "frequency count": "find frequency of elements",
    "nearby duplicates": "duplicate within distance k",
    "duplicates": "duplicate within distance k",
    "pair with given sum": "two sum check exists",
    "pair sum": "two sum check exists",
    "distinct window": "distinct elements in window",
    "distinct elements window": "distinct elements in window",
    # Anagram variants
    "anagram": "group words by anagrams",
    "anagrams": "group words by anagrams",
    "group anagrams": "group words by anagrams",
}

# ------------------------------------------------------------------------------ 
# Unit grouping for nicer listing
# ------------------------------------------------------------------------------ 
_UNIT_MAP = {
    "1. DSA intro & sorting": [
        "binary search with comparisons",
        "find first last position",
        "merge sort",
        "merge two sorted arrays",
        "quick sort",
        "randomized quick sort",
        "count inversions in array",
        "maximum subarray sum divide conquer",
        "find kth largest element",
        "sort by bit count",
        "find least k unique elements",
    ],
    "2. Hashing": [
        "hash table separate chaining",
        "find frequency of elements",
        "duplicate within distance k",
        "two sum check exists",
        "two sum return indices",
        "distinct elements in window",
        "find top k frequent elements",
        "group words by anagrams",
        "linear probing",
        "quadratic probing",
    ],
    "3. Trees": [
        "tree traversals",
        "binary search tree operations",
        "huffman encoding tree",
        "avl tree insert",
        "find tree height",
        "build tree from preorder inorder",
        "find tree diameter",
        "find bst lowest common ancestor",
        "check perfect family tree",
        "check if tree symmetric",
        "find kth smallest element",
        "level order traversal",
        "max leaf to leaf sum",
        "convert bst to minheap",
        "make min heap from array",
        "make max heap from array",
        "check if bt is heap",
    ],
    "4. Graphs": [
        "graph matrix ops",
        "graph adjacency list",
        "dfs graph traversal",
        "bfs graph traversal",
        "connected components",
        "topological sort kahn algorithm",
        "topological sort dfs based",
        "topological sort from matrix",
        "check if graph bipartite",
        "flood fill algorithm",
        "minimum network operations",
        "nasa astronaut pairs",
        "create graph from matrix",
        "find dfs reachable nodes",
        "dfs from adjacency list",
        "check if nodes connected",
        "count biconnected components",
        "detect cycle in graph",
        "find all paths between nodes",
        "check if graph symmetric",
        "find mother vertex",
        "check if path exists",
        "find grid path from 1 to 2",
        "transpose graph matrix",
        "count number of islands",
        "count islands in grid",
    ],
    "5. Advanced DSA concepts": [
        "binomial heap merge",
        "binomial heap extract min",
        "detect cycle union find",
        "trie data structure",
        "job scheduling",
        "job priority queue",
        "trie implementation",
        "priority queue basic",
        "priority queue full",
        "bst to min heap",
    ],
}


def _print_grouped_available():
    """Print available problems grouped by unit headings."""
    # Only include keys that actually exist
    for unit, keys in _UNIT_MAP.items():
        existing = [k for k in keys if k in _DOCS]
        if not existing:
            continue
        print(f"# {unit}:")
        for k in sorted(existing):
            print(f"#  - {k}")
        print("#")

def doc(key: str, language="baby", theory=False):
    """
    Prints solution code or theoretical content for MCQ preparation.
    Args:
        key: The problem key (e.g., 'huffman', 'flood fill') or theory topic (e.g., 'unit 1', 'hashing').
        language: 'baby' for babygrad library code, 'python' for pure standard python. If 'theory', returns theoretical content.
        theory: If True, returns theoretical content instead of code. Use topics like 'unit 1', 'unit 2', 'hashing', 'trees', etc.
    """
    # Check if language parameter is "theory" - treat as theory request
    # This MUST be checked first before any other processing
    is_theory_request = False
    if isinstance(language, str):
        lang_lower = language.lower().strip()
        if lang_lower == "theory":
            is_theory_request = True
            theory = True
            language = "baby"  # Reset to default since it's not a language
    
    # Normalize key (strip spaces, lowercase)
    k = key.lower().strip() if key else ""

    # Resolve known aliases early (helps short queries like "anagram")
    if k in _ALIASES:
        k = _ALIASES[k].lower()
    
    # Handle theory requests - MUST check this first and return early
    # Check theory flag OR theory request OR key starts with theory/unit
    if theory or is_theory_request or k.startswith("theory") or k.startswith("unit"):
        # Handle empty key - show all available theory topics
        if not k:
            print("# Available theory topics:\n# " + "\n# ".join(sorted(THEORY_.keys())))
            return
        
        # Remove "theory" prefix if present
        if k.startswith("theory"):
            k = k[6:].strip()
        
        # Normalize theory keys for matching (lowercase)
        theory_keys_lower = {key.lower(): key for key in THEORY_.keys()}
        
        # Check exact match (case-insensitive)
        if k in theory_keys_lower:
            actual_key = theory_keys_lower[k]
            for item in THEORY_[actual_key]:
                print(item)
            return
        
        # Check if query is a prefix/substring of any key (for short forms like "avl" -> "AVL Tree")
        prefix_matches = []
        for key_lower, original_key in theory_keys_lower.items():
            # Check if query is prefix of key or key contains query as a word
            words = key_lower.split()
            if key_lower.startswith(k) or any(word.startswith(k) for word in words):
                prefix_matches.append((key_lower, original_key))
        
        if prefix_matches:
            # Use the best match (shortest key that starts with query, or first word match)
            best_match = min(prefix_matches, key=lambda x: (not x[0].startswith(k), len(x[0])))
            actual_key = best_match[1]
            print(f"# Did you mean '{actual_key}'?\n")
            for item in THEORY_[actual_key]:
                print(item)
            return
        
        # Fuzzy matching for theory topics with lower cutoff for short forms
        cutoff = 0.3 if len(k) < 4 else (0.4 if len(k) < 6 else 0.6)  # Very low cutoff for very short queries
        theory_matches = difflib.get_close_matches(k, [key.lower() for key in THEORY_.keys()], n=1, cutoff=cutoff)
        
        if theory_matches:
            # Find the original key (case-sensitive)
            matched_lower = theory_matches[0]
            actual_key = theory_keys_lower[matched_lower]
            print(f"# Did you mean '{actual_key}'?\n")
            for item in THEORY_[actual_key]:
                print(item)
        else:
            # Show available theory topics, not problem names
            print(f"# No theory found for '{key}'. Available theory topics:\n# " + "\n# ".join(sorted(THEORY_.keys())))
        return  # CRITICAL: Must return here to prevent falling through to code section
    
    # Handle code requests (original functionality) - only reached if NOT theory request
    # Normalize doc keys for matching
    doc_keys_lower = {key.lower(): key for key in _DOCS.keys()}
    
    # Check exact match (case-insensitive)
    if k in doc_keys_lower:
        actual_key = doc_keys_lower[k]
        print(_DOCS[actual_key].get(language, "# Language not found"))
        return
    
    # Fuzzy matching for code problems (include aliases in the search space)
    search_space = set(doc_keys_lower.keys()) | set(_ALIASES.keys())
    cutoff = 0.4 if len(k) < 5 else 0.6  # Lower cutoff for short queries
    matches = difflib.get_close_matches(k, list(search_space), n=1, cutoff=cutoff)
    
    if matches:
        # Resolve match through aliases if needed, then find original key (case-sensitive)
        matched_lower = matches[0]
        if matched_lower in _ALIASES:
            matched_lower = _ALIASES[matched_lower].lower()
        actual_key = doc_keys_lower.get(matched_lower)
        if not actual_key:
            # Fallback: list available grouped if somehow missing
            _print_grouped_available()
            return
        print(f"# Did you mean '{actual_key}'?\n")
        print(_DOCS[actual_key].get(language, "# Language not found"))
    else:
        # Show grouped listing for readability
        print(f"# No docs found for '{key}'. Available (grouped):")
        _print_grouped_available()