import matplotlib.pyplot as plt

import cooptools.plotting as cplt
from cooptools.graphs.graph import Graph, Node, AStarResults, Edge
from cooptools.colors import Color
from cooptools.geometry_utils import vector_utils as vec
from typing import Iterable

def _plot_nodes(nodes: Iterable[Node],
                ax,
                fig,
                color,
                point_size: int = None):
    if point_size is None:
        point_size = 1

    pts = [x.pos for x in nodes]
    cplt.plot_series(
        pts,
        ax=ax,
        fig=fig,
        series_type='scatter',
        color=color,
        point_size=point_size,
        labels=[x.name for x in nodes],
        show_all_labels=True
    )


def _plot_edges(
        edges: Iterable[Edge],
        line_width: int = None,
        color: Color = None
):
    if edges is None or len(edges) == 0:
        return

    if color is None:
        color = Color.BLACK

    deltas = {
        edge: vec.vector_between(start=edge.start.pos, end=edge.end.pos) for edge in edges
    }

    min_l = min(vec.vector_len(x) for _, x in deltas.items())

    for edge in edges:
        delta = deltas[edge]

        if line_width is None:
            line_width = max(min(edge.length // 10, 5), 1)

        plt.arrow(
            x=edge.start.pos[0],
            y=edge.start.pos[1],
            dx=delta[0],
            dy=delta[1],
            head_width=min_l / 12,
            head_length=min_l / 6,
            length_includes_head=True,
            linewidth=line_width,
            fc=color.normalized(),
            ec=color.normalized()
        )


def plot_graph(
        graph: Graph,
        ax,
        fig,
        routes: Iterable[AStarResults] = None,
        color: Color = None,
        point_size: int = 5,
        edge_width: int = 1,
        exclude_sector_tree: bool = False
):
    #plot Graph
    _plot_nodes(
        nodes=graph.Nodes.values(),
        ax=ax,
        fig=fig,
        color=color,
        point_size=point_size
    )

    _plot_edges(
        edges=graph.Edges.values(),
        line_width=edge_width,
        color=color
    )

    #plot routes
    if routes:
        for route in routes:
            color = Color.random()
            _plot_nodes(
                nodes=[x for x in route.path],
                ax=ax,
                fig=fig,
                color=color,
                point_size=point_size+3,
            )

            _plot_edges(
                edges=[x for x in route.edges if x is not None],
                color=color
            )

    if not exclude_sector_tree:
        graph._sec_tree.plot(
            ax=ax,
            fig=fig
        )