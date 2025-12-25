import logging
from cooptools import graphs as grf
from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
import time
from matplotlib.animation import FuncAnimation
from collections import defaultdict
from matplotlib.patches import FancyArrowPatch

def plot_astar_steps(
    results: grf.AStarResults,
    graph: grf.Graph,
    pause=1.0,
    interactive=False,
    fade_factor=0.15,
    show_node_names=True,
    show_costs=True,
    directed_edges=True,
    save_path=None,
    fps=2,
    near_dist: float = 5
):
    """
    Visualize A* execution over a graph.

    Controls (interactive=True):
      → / d : forward
      ← / a : backward
      q     : quit

    | Element        | Visual            |
    | -------------- | ----------------- |
    | Graph edges    | Grey → Blue → Red |
    | Edge thickness | Scales by weight  |
    | Open nodes     | Blue              |
    | Closed nodes   | Red, fading       |
    | Current node   | Green             |
    | Final path     | Thick gold line   |

    Video Export Notes (Important)
    - Uses matplotlib.animation.FuncAnimation
    - MP4 → requires ffmpeg
    - GIF → requires pillow
    - Export works in non-interactive autoplay mode

    Highlighting
    - Hovered node → larger yellow circle drawn on top
    - Hovered edge → thicker yellow line/arrow drawn on top
    - Highlight follows the mouse and disappears when not hovering
    """

    steps = results.steps
    step_keys = sorted(steps.keys())
    max_step = len(step_keys) - 1
    step_index = 0

    # ---- Precompute edge weight scaling ----
    weights = [e.cost or 1.0 for e in graph.Edges.values()]
    min_w, max_w = min(weights), max(weights)

    def edge_width(w):
        if max_w == min_w:
            return 1.5
        return 1.0 + 3.0 * (w - min_w) / (max_w - min_w)

    # ---- Track closed-node age for fading ----
    closed_age = defaultdict(int)

    fig, ax = plt.subplots()

    # ---- Hover state ----
    hovered_node = {"node": None}
    hovered_edge = {"edge": None}

    # ---- Hover annotation ----
    hover_annot = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(10, 10),
        textcoords="offset points",
        bbox=dict(boxstyle="round", fc="w"),
        arrowprops=dict(arrowstyle="->"),
        color='red'
    )
    hover_annot.set_visible(False)

    def draw_edges(open_nodes, closed_nodes):
        for edge in graph.Edges.values():
            a, b = edge.start, edge.end

            if a in closed_nodes or b in closed_nodes:
                color = "red"
            elif a in open_nodes or b in open_nodes:
                color = "blue"
            else:
                color = "lightgrey"

            lw = edge_width(edge.cost)
            z = 1

            # ---- Highlight hovered edge ----
            if hovered_edge["edge"] is edge:
                color = "yellow"
                lw *= 2.5
                z = 10

            if directed_edges:
                arrow = FancyArrowPatch(
                    a.pos[:2],
                    b.pos[:2],
                    arrowstyle="-|>",
                    linewidth=lw,
                    color=color,
                    alpha=0.8,
                    zorder=z,
                )
                ax.add_patch(arrow)
            else:
                ax.plot(
                    [a.pos[0], b.pos[0]],
                    [a.pos[1], b.pos[1]],
                    color=color,
                    linewidth=lw,
                    alpha=0.8,
                    zorder=z,
                )

            # ---- Edge cost label ----
            if edge.cost is not None:
                mx = (a.pos[0] + b.pos[0]) / 2
                my = (a.pos[1] + b.pos[1]) / 2
                ax.text(
                    mx,
                    my,
                    f"{edge.cost:.2f}",
                    fontsize=7,
                    color="black",
                    alpha=0.6,
                    ha="center",
                    va="center",
                    zorder=2,
                )

    def draw(step_idx):
        ax.clear()
        step = steps[step_keys[step_idx]]

        open_nodes = {m.graph_node for m in step["open_set"]}
        closed_nodes = {m.graph_node for m in step["closed_set"]}

        for n in closed_nodes:
            closed_age[n] += 1

        draw_edges(open_nodes, closed_nodes)

        # ---- Draw nodes ----
        for node in graph.Nodes.values():
            size = 30
            color = "grey"
            alpha = 1.0
            z = 2

            if node in closed_nodes:
                color = "red"
                size = 60
                alpha = max(0.2, 1 - fade_factor * closed_age[node])
                z = 3
            elif node in open_nodes:
                color = "blue"
                size = 60
                z = 4

            # ---- Highlight hovered node ----
            if hovered_node["node"] is node:
                color = "yellow"
                size = 160
                alpha = 1.0
                z = 10

            ax.scatter(*node.pos[:2], c=color, s=size, alpha=alpha, zorder=z)

            if show_node_names:
                ax.text(node.pos[0], node.pos[1] + 0.05, node.name, fontsize=8)

        # ---- Current node ----
        if step["current_item"]:
            m = step["current_item"]
            x, y = m.graph_node.pos[:2]
            ax.scatter(x, y, c="green", s=150, zorder=6)

            if show_costs:
                ax.text(
                    x,
                    y - 0.08,
                    f"g={m.g:.2f}\nh={m.h:.2f}\nf={m.f:.2f}",
                    fontsize=7,
                    ha="center",
                )

        # ---- Source / Destination ----
        ax.scatter(*results.source.pos[:2], c="purple", s=150, marker="s", zorder=7)
        ax.scatter(*results.dest.pos[:2], c="orange", s=180, marker="*", zorder=7)

        # ---- Final path animation ----
        if step_idx == max_step:
            px = [n.pos[0] for n in results.path]
            py = [n.pos[1] for n in results.path]
            ax.plot(px, py, c="gold", linewidth=4, zorder=8)

        ax.set_title(f"A* Step {step_idx}")
        ax.set_aspect("equal")
        ax.legend(loc="upper right")
        # ax.grid(False)

        fig.canvas.draw_idle()

    # ---- Keyboard handler ----
    def on_key(event):
        nonlocal step_index
        if event.key in ("right", "d"):
            step_index = min(step_index + 1, max_step)
        elif event.key in ("left", "a"):
            step_index = max(step_index - 1, 0)
        elif event.key == "q":
            plt.close(fig)
            return
        draw(step_index)

    def on_hover(event):
        hovered_node["node"] = None
        hovered_edge["edge"] = None

        if not event.inaxes:
            hover_annot.set_visible(False)
            fig.canvas.draw_idle()
            return

        x, y = event.xdata, event.ydata

        # ---- Check nodes ----
        nearbys = graph.SectorTree.nearby_clients(radius=near_dist,
                                                 pt=(x, y))
        logging.debug(nearbys)
        for node in [v for k, v in graph.Nodes.items() if k in nearbys]:
            hovered_node["node"] = node
            hover_annot.xy = node.pos[:2]
            hover_annot.set_text(
                f"Node: {node.name}\nPos: {node.pos}"
            )
            hover_annot.set_visible(True)
            draw(step_index)
            return

        # ---- Check edges ----
        # for edge in graph.Edges.values():
        #     mx = (edge.start.pos[0] + edge.end.pos[0]) / 2
        #     my = (edge.start.pos[1] + edge.end.pos[1]) / 2
        #
        #     if dist2((x, y), (mx, my)) < near_dist:
        #         hovered_edge["edge"] = edge
        #         hover_annot.xy = (mx, my)
        #         hover_annot.set_text(
        #             f"Edge\n"
        #             f"{edge.start.name} → {edge.end.name}\n"
        #             f"Weight: {edge.weight}\n"
        #             f"Length: {edge.length:.2f}"
        #         )
        #         hover_annot.set_visible(True)
        #         draw(step_index)
        #         return
        #
        # hover_annot.set_visible(False)
        # draw(step_index)

    fig.canvas.mpl_connect("key_press_event", on_key)
    fig.canvas.mpl_connect("motion_notify_event", on_hover)

    # ---- Save animation ----
    if save_path:
        anim = FuncAnimation(
            fig,
            lambda i: draw(i),
            frames=len(step_keys),
            interval=1000 / fps,
            repeat=False,
        )

        if save_path.endswith(".gif"):
            anim.save(save_path, writer="pillow", fps=fps)
        else:
            anim.save(save_path, writer="ffmpeg", fps=fps)

        plt.close(fig)
        return

    # ---- Run ----
    draw(step_index)

    if interactive:
        plt.show()
    else:
        for i in range(len(step_keys)):
            draw(i)
            plt.pause(pause)
        plt.show()


if __name__ == "__main__":
    import random as rnd
    from cooptools.loggingHelpers import BASE_LOG_FORMAT
    logging.basicConfig(format=BASE_LOG_FORMAT,level=logging.DEBUG)

    def tst_001():
        rnd.seed(0)
        g = grf.Graph(grf.large_circuit(
            (0, 100),
            (0, 100),
            n_pts=100
        ))

        strt = g.node_by_name(rnd.choice(list(g.Nodes.keys())))
        end = g.node_by_name(rnd.choice([x for x in g.Nodes.keys() if x != strt]))

        astr = g.astar(
            start=strt,
            end=end
        )

        plot_astar_steps(
            astr,
            graph=g,
            interactive=True,
        )

    tst_001()
