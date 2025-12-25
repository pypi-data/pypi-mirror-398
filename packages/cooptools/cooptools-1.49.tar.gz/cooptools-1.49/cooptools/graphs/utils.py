from cooptools.graphs.graph_dcs import *
import logging
from functools import lru_cache
from cooptools.protocols import UniqueIdentifier

logger = logging.getLogger(__name__)

# helper function to perform dfs and find the articulation points
def findPoints(adj, u, visited, disc, low, time, parent, isAP):
    # Mark the current node as visited
    visited[u] = 1

    # Initialize discovery time and low value
    time[0] += 1
    disc[u] = time[0]
    low[u] = time[0]

    # Go through all vertices adjacent to this
    for v in adj.get(u, []):
        # If v is not visited yet, then make it a child of u
        # in DFS tree and recur for it
        if visited.get(v, 0) == 0:
            findPoints(adj, v, visited, disc, low, time, u, isAP)

            # u is an articulation point in following cases
            # (1) u is root of DFS tree and has two or more chilren.
            # (2) If u is not root and low value of one of its child is more
            # than discovery value of u.

            # Check if the subtree rooted with v has
            # a connection to one of the ancestors of u
            low[u] = min(low[u], low[v])

            # If u is not root and low value of one of
            # its child is more than discovery value of u.
            if parent != -1 and low[v] > disc[u]:
                isAP[u] = 1

        # Update low value of u for parent function calls.
        elif visited[v]== 1:
            low[u] = min(low[u], disc[v])




    # # If u is root of DFS tree and has two or more children.
    if parent == -1 and len(adj[u]) >= 1:
        isAP[u] = 1


# Function to find Articulation Points in the graph
def articulationPoints(adj):
    V = len(adj)

    # to store the articulation points
    res = []

    # to stores discovery times of visited vertices
    disc = {}

    # to store earliest visited vertex (the vertex with minimum
    # discovery time) that can be reached from subtree
    low = {}

    # to keep track of visited vertices
    visited = {}

    # to mark the articulation points
    isAP = {}

    # to store time and parent node
    time = [0]
    par = -1

    # Adding this loop so that the code works
    # even if we are given disconnected graph
    for u in adj:
        if visited.get(u, 0) == 0:
            findPoints(adj, u, visited, disc, low, time, par, isAP)

    # storing the articulation points
    for u in adj:
        if isAP.get(u, 0) == 1:
            res.append(u)

    logger.debug(f"Articulation points evaluation:"
                  f"\n\tVisited: {visited}"
                  f"\n\tdisc: {disc}"
                  f"\n\tlow: {low}"
                  f"\nAPs: [{[res]}]")

    return res


# Python program to find strongly connected components in a given
# directed graph using Tarjan's algorithm (single DFS)
# Complexity : O(V+E)

from collections import defaultdict


# This class represents an directed graph
# using adjacency list representation


class Graph2:

    def __init__(self, vertices):
        # No. of vertices
        self.V = vertices

        # default dictionary to store graph
        self.graph = defaultdict(list)

        self.Time = 0

    # function to add an edge to graph
    def addEdge(self, u, v):
        self.graph[u].append(v)

    '''A recursive function that find finds and prints strongly connected
    components using DFS traversal
    u --> The vertex to be visited next
    disc[] --> Stores discovery times of visited vertices
    low[] -- >> earliest visited vertex (the vertex with minimum
                discovery time) that can be reached from subtree
                rooted with current vertex
     st -- >> To store all the connected ancestors (could be part
           of SCC)
     stackMember[] --> bit/index array for faster check whether
                  a node is in stack
    '''

    def SCCUtil(self, u, low, disc, stackMember, st):

        # Initialize discovery time and low value
        disc[u] = self.Time
        low[u] = self.Time
        self.Time += 1
        stackMember[u] = True
        st.append(u)

        # Go through all vertices adjacent to this
        for v in self.graph[u]:

            # If v is not visited yet, then recur for it
            if disc[v] == -1:

                self.SCCUtil(v, low, disc, stackMember, st)

                # Check if the subtree rooted with v has a connection to
                # one of the ancestors of u
                # Case 1 (per above discussion on Disc and Low value)
                low[u] = min(low[u], low[v])

            elif stackMember[v] == True:

                '''Update low value of 'u' only if 'v' is still in stack
                (i.e. it's a back edge, not cross edge).
                Case 2 (per above discussion on Disc and Low value) '''
                low[u] = min(low[u], disc[v])

        # head node found, pop the stack and print an SCC
        w = -1  # To store stack extracted vertices
        if low[u] == disc[u]:
            while w != u:
                w = st.pop()
                print(w, end=" ")
                stackMember[w] = False

            print()

    # The function to do DFS traversal.
    # It uses recursive SCCUtil()

    def SCC(self):

        # Mark all the vertices as not visited
        # and Initialize parent and visited,
        # and ap(articulation point) arrays
        disc = [-1] * (self.V)
        low = [-1] * (self.V)
        stackMember = [False] * (self.V)
        st = []

        # Call the recursive helper function
        # to find articulation points
        # in DFS tree rooted with vertex 'i'
        for i in range(self.V):
            if disc[i] == -1:
                self.SCCUtil(i, low, disc, stackMember, st)



_at_leasts = {}

@lru_cache
def astar(
        edges: frozenset[Tuple[UniqueIdentifier, UniqueIdentifier, UniqueIdentifier, float]],
        start: UniqueIdentifier,
        end: UniqueIdentifier,
) -> AStarResults:
    #TODO: Does not work as expected

    if start == end:
        return AStarResults(
            node_ids=[start],
            edge_ids=[],
            steps={},
            start_node_id=start,
            end_node_id=end,
            cost=0
        )


    _edge_id_lookup = {tuple([s, e]): id for id, s, e, c in edges}
    _edge_dst_lookup = {id: c for id, s, e, c in edges}

    # create a quick lookup of all edges that end at a given node
    _node_edge_lookup = {}

    for edge in edges:
        _node_edge_lookup.setdefault(edge[2], []).append(edge)

    min_cost_to_node_lam = lambda x: min(c for e_id, e_s, e_e, c in _node_edge_lookup[x]) if x != start else 0

    # min distance from start -> end == min((dist from cnxn -> end) + (dist from start -> cnxn))
    min_cost = None
    edge_chain = None
    path = None

    # look through the edges that connect to the destination
    for e_id, e_s, e_e, c in _node_edge_lookup[end]:
        est_to_edge_strt = min_cost_to_node_lam(e_s)
        at_least_est = c + est_to_edge_strt
        print(f"Checking {e_s} -> {e_e} [{est_to_edge_strt}, {at_least_est}]")
        if min_cost is not None and at_least_est > min_cost:
            continue

        path_to_edge_start = astar(
            edges=edges,
            start=start,
            end=e_s
        )
            # memo[(start, edge.start)] = path_to_edge_start

        cost = c + path_to_edge_start.cost
        if min_cost is None or cost < min_cost:
            min_cost = cost
            edge_chain = list(path_to_edge_start.edge_ids)
            edge_chain.append(e_id)
            path = list(path_to_edge_start.node_ids)
            path.append(e_e)

    return AStarResults(
        node_ids=path,
        edge_ids=edge_chain,
        start_node_id=start,
        end_node_id=end,
        cost=min_cost,
        steps={}
    )













if __name__ == "__main__":
    from cooptools.graphs.graph import Graph, Node
    from cooptools.graphs.draw import plot_graph
    from matplotlib import pyplot as plt
    import random as rnd
    from cooptools.graphs import graph_definitions as gd
    from pprint import pprint

    # Utility function to add an edge
    # def addEdge(adj, u, v):
    #     adj[u].append(v)
    #     adj[v].append(v)  # Correction: This line should add u to adj[v]
    #     # However, to match the C++ logic, we add:
    #     adj[v].append(u)
    #
    # # create adjacency list
    # adj = [[] for _ in range(5)]
    # addEdge(adj, 0, 1)
    # addEdge(adj, 1, 4)
    # addEdge(adj, 2, 4)
    # addEdge(adj, 3, 4)
    # addEdge(adj, 2, 3)
    # print(adj)
    # ans = articulationPoints(adj)

    def test_g_SCC():
        g4 = Graph2(11)
        g4.addEdge(0, 1)
        g4.addEdge(0, 3)
        g4.addEdge(1, 2)
        g4.addEdge(1, 4)
        g4.addEdge(2, 0)
        g4.addEdge(2, 6)
        g4.addEdge(3, 2)
        g4.addEdge(4, 5)
        g4.addEdge(4, 6)
        g4.addEdge(5, 6)
        g4.addEdge(5, 7)
        g4.addEdge(5, 8)
        g4.addEdge(5, 9)
        g4.addEdge(6, 4)
        g4.addEdge(7, 9)
        g4.addEdge(8, 9)
        g4.addEdge(9, 8)
        print("\nSSC in fourth graph ")
        g4.SCC()


    def test_articulation():


        nodes = {ii: Node(ii, (rnd.randint(0, 100), rnd.randint(0, 100))) for ii in range(8)}

        g_dict = {
            nodes[0]: [],
            nodes[2]: [nodes[1]],
            nodes[1]: [nodes[3]],
            nodes[3]: [nodes[4]],
            nodes[4]: [nodes[5], nodes[6], nodes[7]]
        }

        # g_dict = {
        #     nodes[0]: [nodes[1]],
        #     nodes[1]: [nodes[2]],
        #     nodes[2]: [nodes[0], nodes[3]],
        #     nodes[3]: [nodes[4]],
        #     nodes[4]: [nodes[5]],
        #     nodes[5]: [nodes[3]],
        # }
        # g_dict = {
        #     nodes[0]: [nodes[1], nodes[3]],
        #     nodes[1]: [nodes[2], nodes[4]],
        #     nodes[2]: [nodes[0], nodes[6]],
        #     nodes[3]: [nodes[2]],
        #     nodes[4]: [nodes[5], nodes[6]],
        #     nodes[5]: [nodes[6],nodes[7], nodes[8], nodes[9]],
        #     nodes[6]: [nodes[4]],
        #     nodes[7]: [nodes[9]],
        #     nodes[8]: [nodes[9]],
        #     nodes[9]: [nodes[8]]
        # }
        # g_dict = articulated()

        ans = articulationPoints(g_dict)
        for i in ans:
            print(i, end=" ")

        fig, ax = plt.subplots()

        g = Graph(graph_dict=g_dict)
        plot_graph(g,
                   ax=ax,
                   fig=fig)
        plt.show()


    def test_astar():
        # rnd.seed(0)
        # g = Graph(gd.large_circuit(
        #     (0, 100),
        #     (0, 100),
        #     n_pts=100
        # ))

        n_0 = Node('0', (0, 0))
        n_1 = Node('1', (0, 0))
        n_2 = Node('2', (0, 0))
        n_3 = Node('3', (0, 0))
        n_4 = Node('4', (0, 0))
        n_5 = Node('5', (0, 0))
        n_6 = Node('6', (0, 0))
        n_7 = Node('7', (0, 0))
        n_8 = Node('8', (0, 0))
        n_9 = Node('9', (0, 0))
        n_10 = Node('10', (0, 0))

        g = Graph(
            graph_dict={
                n_0: [n_6, n_1],
                n_1: [n_7, n_2],
                n_2: [n_3, n_8],
                n_3: [n_9],
                n_4: [n_5],
                n_5: [n_6, n_0],
                n_6: [n_2, n_7],
                n_7: [n_2, n_8],
                n_8: [n_3],
                n_9: [n_4, n_10],
                n_10: [n_5, n_0]
            },
            edge_costs={
                (n_0, n_1): 5,
                (n_0, n_6): 4,
                (n_1, n_7): 2,
                (n_1, n_2): 1,
                (n_2, n_3): 4,
                (n_2, n_8): 5,
                (n_3, n_9): 2,
                (n_4, n_5): 3,
                (n_5, n_0): 4,
                (n_5, n_6): 3,
                (n_6, n_7): 3,
                (n_6, n_2): 2,
                (n_7, n_2): 3,
                (n_7, n_8): 4,
                (n_8, n_3): 3,
                (n_9, n_4): 1,
                (n_9, n_10): 2,
                (n_10, n_5): 4,
                (n_10, n_0): 5,
            }
        )

        # strt = g.node_by_name(rnd.choice(list(g.Nodes.keys())))
        # end = g.node_by_name(rnd.choice([x for x in g.Nodes.keys() if x != strt]))
        strt = g.node_by_name('0')
        end = g.node_by_name('3')

        import time
        tic = time.perf_counter()
        path = astar(
            edges=frozenset(tuple([e.id, e.start.name, e.end.name, e.cost])
                            for e in g.Edges.values() if e.enabled()),
            start=strt.name,
            end=end.name
        )

        toc = time.perf_counter()
        print(f"TIME: {toc - tic}")

        pprint(path)


    # test_g_SCC()
    # test_articulation()
    test_astar()