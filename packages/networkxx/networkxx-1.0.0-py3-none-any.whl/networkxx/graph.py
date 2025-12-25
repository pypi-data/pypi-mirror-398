import networkx as nx


class MatrixGraph:
    """Helper for matrix-based graph problems."""

    def __init__(self, matrix):
        self.matrix = matrix

    def print_matrix(self):
        for row in self.matrix:
            print(*row)


class GraphOps:
    def __init__(self, directed=False):
        self.g = nx.DiGraph() if directed else nx.Graph()
        self.directed = directed

    # --- Basic mutations ---
    def add(self, u, v, w=None):
        if w is not None:
            self.g.add_edge(u, v, weight=w)
        else:
            self.g.add_edge(u, v)

    def remove(self, u, v):
        if self.g.has_edge(u, v):
            self.g.remove_edge(u, v)

    # --- Printers ---
    def print_adj_list(self, n):
        """Prints adjacency list in 'u: v1 v2 ...' format."""
        for i in range(n):
            nbrs = sorted(list(self.g.neighbors(i))) if i in self.g else []
            print(f"{i}:{' '.join(map(str, nbrs))} " if nbrs else f"{i}:")

    def print_adj_matrix(self, n):
        """Prints adjacency matrix."""
        for r in range(n):
            row = [1 if self.g.has_edge(r, c) else 0 for c in range(n)]
            print(*row)

    def print_degrees(self, n):
        for i in range(n):
            ind = self.g.in_degree(i) if self.directed else self.g.degree(i)
            out = self.g.out_degree(i) if self.directed else self.g.degree(i)
            print(f"Vertex {i}: In-degree = {ind}, Out-degree = {out}")

    # --- Traversals ---
    def bfs(self, start):
        if start not in self.g:
            return []
        res, visited, q = [], {start}, [start]
        while q:
            u = q.pop(0)
            res.append(u)
            for v in sorted(self.g.neighbors(u)):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        return res

    def dfs(self, start):
        if start not in self.g:
            return []
        res, visited, stack = [], set(), [start]
        while stack:
            u = stack.pop()
            if u not in visited:
                visited.add(u)
                res.append(u)
                for v in sorted(self.g.neighbors(u), reverse=True):
                    if v not in visited:
                        stack.append(v)
        return res

    def all_paths(self, src, dst):
        """Returns list of all simple paths from src to dst."""
        try:
            return list(nx.all_simple_paths(self.g, src, dst))
        except Exception:
            return []

    # --- Algorithms ---
    def components(self):
        if self.directed:
            comps = nx.weakly_connected_components(self.g)
        else:
            comps = nx.connected_components(self.g)
        res = [sorted(list(c)) for c in comps]
        res.sort(key=lambda x: x[0])
        return res

    def topo_sort(self):
        try:
            return list(nx.lexicographical_topological_sort(self.g))
        except Exception:
            return None

    def is_bipartite(self):
        return nx.is_bipartite(self.g)

    def biconnected_count(self):
        return len(list(nx.biconnected_components(self.g))) if not self.directed else 0

    def mother_vertex(self, n):
        """Return minimal index mother vertex or -1."""
        visited = set()
        last = -1
        for i in range(n):
            if i not in visited:
                self._dfs_visit(i, visited)
                last = i
        visited = set()
        self._dfs_visit(last, visited)
        return last if len(visited) == n else -1

    def _dfs_visit(self, u, visited):
        visited.add(u)
        for v in self.g.neighbors(u):
            if v not in visited:
                self._dfs_visit(v, visited)

    # --- Matrix helpers ---
    @staticmethod
    def from_matrix(matrix, directed=False):
        g = GraphOps(directed)
        rows = len(matrix)
        for r in range(rows):
            for c in range(len(matrix[r])):
                if matrix[r][c] != 0:
                    g.add(r, c)
        return g

    @staticmethod
    def is_symmetric(matrix):
        rows = len(matrix)
        for r in range(rows):
            for c in range(rows):
                if matrix[r][c] != matrix[c][r]:
                    return False
        return True

    @staticmethod
    def transpose_matrix(matrix):
        return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0]))]

    # --- Grid helpers ---
    @staticmethod
    def count_islands(grid):
        rows, cols = len(grid), len(grid[0])
        visited = set()
        count = 0

        def bfs(r, c):
            q = [(r, c)]
            visited.add((r, c))
            while q:
                cr, cc = q.pop(0)
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and str(grid[nr][nc]) == "1"
                        and (nr, nc) not in visited
                    ):
                        visited.add((nr, nc))
                        q.append((nr, nc))

        for r in range(rows):
            for c in range(cols):
                if str(grid[r][c]) == "1" and (r, c) not in visited:
                    bfs(r, c)
                    count += 1
        return count

    @staticmethod
    def flood_fill(grid, r, c, new_col):
        rows, cols = len(grid), len(grid[0])
        old_col = grid[r][c]
        if old_col == new_col:
            return grid

        def dfs(x, y):
            if not (0 <= x < rows and 0 <= y < cols) or grid[x][y] != old_col:
                return
            grid[x][y] = new_col
            dfs(x + 1, y)
            dfs(x - 1, y)
            dfs(x, y + 1)
            dfs(x, y - 1)

        dfs(r, c)
        return grid

    @staticmethod
    def grid_path(grid, start_val, end_val, pass_vals):
        rows, cols = len(grid), len(grid[0])
        start_node = None
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == start_val:
                    start_node = (r, c)
                    break
            if start_node:
                break
        if not start_node:
            return False

        q = [start_node]
        visited = {start_node}
        while q:
            r, c = q.pop(0)
            if grid[r][c] == end_val:
                return True
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                    val = grid[nr][nc]
                    if val == end_val or val in pass_vals:
                        visited.add((nr, nc))
                        q.append((nr, nc))
        return False

