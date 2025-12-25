from collections import Counter


class DAGraph:
    """A directed acyclic graph of objects and their dependencies.

    Supports a robust topological sort
    to detect the order in which they must be handled.

    Takes an optional iterator of ``(obj, dependencies)``
    tuples to build the graph from.

    Warning:
        Does not support cycle detection.
    """

    def __init__(self, it=None):
        self.adjacent = {}
        if it is not None:
            self.update(it)

    def add_edge(self, A, B):
        """Add an edge from object ``A`` to object ``B``.

        I.e. ``A`` depends on ``B``.
        """
        self.adjacent.setdefault(A, []).append(B)

    def connect(self, graph):
        """Add nodes from another graph."""
        self.adjacent.update(graph.adjacent)

    def valency_of(self, vertex):
        """Return the valency (degree) of a vertex in the graph."""
        if vertex not in self:
            return 0

        adj_len = [len(self[vertex])]
        for node in self[vertex]:
            adj_len.append(self.valency_of(node))
        return sum(adj_len)

    def update(self, edges):
        """Update graph with data from a list of ``(obj, deps)`` tuples."""
        for vertex, successors in edges:
            for succ in successors:
                self.add_edge(vertex, succ)

    def edges(self):
        """Return generator that yields for all edges in the graph."""
        return (obj for obj, adj in self.items() if adj)

    def topsort(self):
        """Sort the graph topologically.

        Perform Khan's simple topological sort algorithm from '62.

        See https://en.wikipedia.org/wiki/Topological_sorting
        """
        count = Counter()
        result = []
        getter = self.adjacent.get

        for node in self:
            for successor in self[node]:
                count[successor] += 1
        ready = [node for node in self if not count[node]]

        while ready:
            node = ready.pop()
            result.append(node)

            for successor in getter(node, []):
                count[successor] -= 1
                if count[successor] == 0:
                    ready.append(successor)

        return result

    def _tarjan72(self):
        """Perform Tarjan's algorithm to find strongly connected components.

        See Also:
            :wikipedia:`Tarjan%27s_strongly_connected_components_algorithm`
        """
        result, stack, low = [], [], {}
        getter = self.adjacent.get

        def visit(node):
            if node in low:
                return
            num = len(low)
            low[node] = num
            stack_pos = len(stack)
            stack.append(node)

            for successor in getter(node, []):
                visit(successor)
                low[node] = min(low[node], low[successor])

            if num == low[node]:
                component = tuple(stack[stack_pos:])
                stack[stack_pos:] = []
                result.append(component)
                for item in component:
                    low[item] = len(self)

        for n in self:
            visit(n)

        return result

    def __iter__(self):
        return self.adjacent.__iter__()

    def __getitem__(self, node):
        return self.adjacent.__getitem__(node)

    def __len__(self):
        return self.adjacent.__len__()

    def __contains__(self, obj):
        return self.adjacent.__contains__(obj)

    def _iterate_items(self):
        return self.adjacent.items()

    items = iteritems = _iterate_items

    @property
    def is_acyclic(self):
        scc = self._tarjan72()
        return all(len(item) == 1 for item in scc)

    def __repr__(self):
        return '\n'.join(self.repr_node(N) for N in self)

    def repr_node(self, obj, level=1, fmt='{0}({1})'):
        output = [fmt.format(obj, self.valency_of(obj))]
        if obj in self:
            for other in self[obj]:
                d = fmt.format(other, self.valency_of(other))
                output.append('     ' * level + d)
                output.extend(self.repr_node(other, level + 1).split('\n')[1:])
        return '\n'.join(output)

    def topsort_ori(self):
        """Sort the graph topologically.

        Returns:
            List: of objects in the order in which they must be handled.
        """
        graph = self.__class__()
        components = self._tarjan72()

        NC = {
            node: component for component in components for node in component
        }
        for component in components:
            graph.add_arc(component)
        for node in self:
            node_c = NC[node]
            for successor in self[node]:
                successor_c = NC[successor]
                if node_c != successor_c:
                    graph.add_edge(node_c, successor_c)
        return [t[0] for t in graph.topsort()]

    def add_arc(self, obj):
        """Add an object to the graph."""
        self.adjacent.setdefault(obj, [])
