import unittest
from cooptools.graphs import Graph, Node
from cooptools.common import flattened_list_of_lists
import cooptools.geometry_utils.vector_utils as vec

class TestGraph(unittest.TestCase):

    def init_a_test_graph(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c, f],
             f: []
             }

        return Graph(g)

    def test_init_graph(self):
        graph = self.init_a_test_graph()

        assert len(graph.Nodes), 6
        assert len(graph.Edges), 9

    def test__generate_node_edge_map(self):
        pass

    def test__generate_pos_edge_map(self):
        pass

    def test__generate_position_node_map(self):
        pass

    def test__generate_graph_dict(self):
        pass

    def test__generate_node_by_name_map(self):
        pass

    def test_nodes(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)

        assert len(graph.Nodes) == 6
        assert list(graph.Nodes.values()) == [a, b, c, d, e, f]


    def test_edges(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)

        assert len(graph.Edges) == 9
        assert list(graph.Edges.values()) == flattened_list_of_lists([graph.edges_between(a, d),
                                                       graph.edges_between(b, c),
                                                       graph.edges_between(c, b),
                                                       graph.edges_between(c, d),
                                                       graph.edges_between(c, e),
                                                       graph.edges_between(d, a),
                                                       graph.edges_between(d, c),
                                                       graph.edges_between(e, c),
                                                       graph.edges_between(e, f)])

    def test_add_node(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)

        assert len(graph.Nodes) == 6
        assert list(graph.Nodes.values()) == [a, b, c, d, e, f]

        h = Node(name='H', pos=(6, 5))
        graph.add_node(h)

        assert len(graph.Nodes) == 7
        assert list(graph.Nodes.values()) == [a, b, c, d, e, f, h]

    def test_add_edges(self):
        pass

    def test_remove_edges(self):
        pass

    def test_enable_edges(self):
        pass

    def test_disable_edges(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, b, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)
        graph.disable_edges(graph.edges_between(d, c), "BLOCK")
        assert graph.edges_between(d, c)[0].disablers() == {"BLOCK"}


    def test_edges_to_node(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)

        assert set(graph.edges_to_node(c)) == {graph.edges_between(b, c)[0],
                                               graph.edges_between(d, c)[0],
                                               graph.edges_between(e, c)[0]}

    def test_edges_from_node(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)

        assert set(graph.edges_from_node(c)) == {graph.edges_between(c, b)[0],
                                                 graph.edges_between(c, d)[0],
                                                 graph.edges_between(c, e)[0]}

    def test_edges_including_node(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)

        assert set(graph.edges_including_node(c)) == {graph.edges_between(c, b)[0],
                                                      graph.edges_between(c, d)[0],
                                                      graph.edges_between(c, e)[0],
                                                      graph.edges_between(b, c)[0],
                                                      graph.edges_between(d, c)[0],
                                                      graph.edges_between(e, c)[0]}

    def test_disable_edges_to_node(self):
        pass

    def test_enable_edges_to_node(self):
        pass

    def test_adjacent_nodes(self):
        pass

    def test__remove_edge(self):
        pass

    def test__add_edge(self):
        pass

    def test_nodes_at__none(self):
        a = Node(name='A', pos=(1, 1))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c],
             f: []
             }

        graph = Graph(g)

        nodes = graph.nodes_at_point((0, 0))

        assert nodes == []

    def test_nodes_at__single(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c],
             f: []
             }

        graph = Graph(g)

        nodes = graph.nodes_at_point((0, 0))

        assert nodes == [a]

    def test_nodes_at__multiple(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))
        h = Node(name='H', pos=(0, 0))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c],
             f: [],
             h: []
             }

        graph = Graph(g)

        nodes = graph.nodes_at_point((0, 0))

        assert nodes == [a, h]


    def test__edge_at(self):
        pass

    def test_find_isolated_vertices(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c],
             f: []
             }

        graph = Graph(g)
        assert graph.find_isolated_vertices() == [f]

    def test_find_path(self):
        pass

    def test_find_all_paths(self):
        pass

    def test_vertex_degree(self):
        pass

    def test_degree_sequence(self):
        pass

    def test_is_degree_sequence(self):
        pass

    def test_delta(self):
        pass

    def test_Delta(self):
        pass

    def test_density(self):
        pass

    def test_diameter(self):
        pass

    def test_erdoes_gallai(self):
        pass

    def test_astar(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)
        path = graph.astar(a, e)


        assert path.nodes == [a, d, c, e]

    def test__path_length(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)
        path = [a, d, c, e]
        length = graph.path_length(path)

        assert length == vec.distance_between(d.pos, a.pos) + vec.distance_between(c.pos, d.pos) + vec.distance_between(e.pos, c.pos)

    def test__astar_with_disablers(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, b, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)
        graph.disable_edges(graph.edges_between(d, c), "BLOCK")

        path = graph.astar(a, e)

        assert path.nodes == [a, d, b, c, e]

    def test_astar_with_ignored_disablers(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, b, c],
             e: [c, f],
             f: []
             }

        graph = Graph(g)
        edge = graph.edges_between(d, c)[0]
        graph.disable_edges(edge, "BLOCK")

        path = graph.astar(a, e, ignored_disablers=frozenset(["BLOCK"]))

        assert path.nodes == [a, d, c, e]

    def test_astar_no_valid_path(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, b, c],
             e: [c],
             f: []
             }

        graph = Graph(g)
        path = graph.astar(a, f)

        assert path.nodes is None


    def test_node_by_name(self):
        pass

    def test_verify_edge_configuration(self):
        pass

    def test_APUtil(self):
        pass

    def test_AP(self):
        pass


    def test_add_node_with_connnections__base(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, b, c],
             e: [c],
             f: []
             }

        graph = Graph(g)


        h = Node('H', (100, 100))

        graph.add_nodes_with_connections(
            {a: [h],
             h: [b, c],
             c: [h]})


        assert h in graph.Nodes.values()

        assert graph.edges_between(a, h) is not None
        assert graph.edges_between(h, a) is None
        assert graph.edges_between(b, h) is None
        assert graph.edges_between(h, b) is not None
        assert graph.edges_between(c, h) is not None
        assert graph.edges_between(h, c) is not None

    def test_closest_node__base(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, b, c],
             e: [c],
             f: []
             }

        graph = Graph(g)

        test = (0, 1)
        closest = graph.closest_nodes(test)[0]
        assert closest == a; f"{closest}"

    def test_copy__base(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, b, c],
             e: [c],
             f: []
             }

        graph = Graph(g)

        copy = graph.copy()

        assert len(copy.Nodes) == len(graph.Nodes)
        assert len(copy.Edges) == len(graph.Edges)
        assert (edge.disablers() == graph.edges_between(edge.start, edge.end).disablers() for edge in copy.Edges.values())

    def test__edge_by_id(self):
        a = Node(name='A', pos=(0, 0))
        b = Node(name='B', pos=(3, 3))
        c = Node(name='C', pos=(2, 0))
        d = Node(name='D', pos=(2, 1))
        e = Node(name='E', pos=(3, 4))
        f = Node(name='F', pos=(5, 5))

        g = {a: [d],
             b: [c],
             c: [b, d, e],
             d: [a, b, c],
             e: [c],
             f: []
             }

        graph = Graph(g)

        edge = graph.edges_between(a, d)[0]

        self.assertIsNotNone(edge, "Edge was returned none when expected value")

        edge_ret = graph.edges_by_id([edge.id])[0]

        self.assertEqual(edge, edge_ret, f"returned edge {edge_ret} [{edge_ret.id}] does not match {edge} [{edge.id}]")


if __name__ == "__main__":
    tester = TestGraph()
    tester.test_closest_node__base()