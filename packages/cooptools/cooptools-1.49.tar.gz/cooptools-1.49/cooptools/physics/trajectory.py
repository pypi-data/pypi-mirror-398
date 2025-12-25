import logging
import math
import time

from cooptools.geometry_utils import vector_utils as vec
from cooptools.geometry_utils import circle_utils as circ
from cooptools.geometry_utils import line_utils as lin
import matplotlib.pyplot as plt
from cooptools import plotting as cplot
from cooptools import typeProviders as tp
import numpy as np

logger = logging.getLogger(__name__)

def circ_arc_trajectory_planner(
    init_pos: vec.FloatVec,
    init_heading: vec.FloatVec,
    target_pos: vec.FloatVec,
    target_heading: vec.FloatVec,
    l: float,
    show_plot: bool=False,
    save_plot_filename_provider: tp.FilePathProvider = None
):
    x0x, x0y = init_pos
    xTx, xTy = target_pos

    x1 = vec.add_vectors([init_pos, vec.scaled_to_length(init_heading, l)])


    # We want to find the distance D that is the sum of straight line movement, followed by arc, and final straight line

    # The intersection point O of the lines [(x0, x0+v0), (xT, xT+vT)]
    O = lin.line_intersection_2d((init_pos, vec.add_vectors([init_pos, init_heading])),
                                 (target_pos, vec.add_vectors([target_pos, target_heading])),
                                 extend=True)
    logger.info(f"O: {O}")

    # Capture a few important lengths
    OX0_len = vec.distance_between(init_pos, O)
    OXT_len = vec.distance_between(target_pos, O)
    OX1_len = vec.distance_between(x1, O)

    scale = max(OXT_len, OX0_len, OX1_len)

    # The bisecting line between the two points and their intersection O is OG
    bisecting_vector = vec.bisecting_vector_2d(
        a = vec.vector_between(O, init_pos),
        b = vec.vector_between(O, target_pos)
    )

    bis_lin_1 = lin.slope_intercept_form_from_points((O, vec.add_vectors([O, bisecting_vector])))
    perp_vec = vec.perpendicular_vector_2d(bisecting_vector)
    bis_line_2 = lin.slope_intercept_form_from_points((O, vec.add_vectors([O, perp_vec])))


    # vOGx = (x0x - O[0]) / OX0_len + (xTx - O[0]) / OXT_len
    # vOGy = (x0y - O[1]) / OX0_len + (xTy - O[1]) / OXT_len
    # vOG1 = (vOGx, vOGy)

    # vOG1 = vec.scaled_to_length(vOG1, 1.5*scale)
    vOG1 = vec.scaled_to_length((1, bis_lin_1[0]), 1.5 * scale)
    vOG2 = vec.scaled_to_length((1, bis_line_2[0]), 1.5 * scale)

    lOG1 = (O, vec.add_vectors([O, vOG1]))
    lOG2 = (O, vec.add_vectors([O, vOG2]))
    logger.info(f"Line OG: {lOG1}")

    # Calculate perp line to OX1 @ X1
    perp_line_at_x1 = lin.perp_line_to_line_at_point(x1, slope_int=lin.slope_intercept_form_from_points((O, init_pos)))
    perp_line_vector = vec.scaled_to_length((1, perp_line_at_x1[0]), scale)
    perp_line_pts = (x1, vec.add_vectors([x1, perp_line_vector]))

    # Center of circle, C1, is the intersection of OG1 and perp(OX1@X1)
    C1 = lin.line_intersection_2d(perp_line_pts,
                                 lOG1,
                                 extend=True)

    # Center of circle, C2, is the intersection of OG2 and perp(OX1@X1)
    C2 = lin.line_intersection_2d(perp_line_pts,
                                 lOG2,
                                 extend=True)

    r1 = vec.distance_between(C1, x1)
    circC1 = (C1,
             r1)

    r2 = vec.distance_between(C2, x1)
    circC2 = (C2,
             r2)


    # Define the angle between the initial and target vector, omega
    omega = vec.rads_between(target_pos, init_pos, O)

    # The traversed arc_angle is pi + the angle between the initial and target vector, omega
    traversed_arc_angle = omega + math.pi
    x2_1 = circ.rotated_point(
        x1,
        center=C1,
        rads=math.pi * 2 - traversed_arc_angle
    )

    logger.info(f"Traversed arc angle: {traversed_arc_angle}")


    # The traversed arc_angle is pi + the angle between the initial and target vector, omega
    traversed_arc_angle = 2 * math.pi - omega
    x2_2 = circ.rotated_point(
        x1,
        center=C2,
        rads=traversed_arc_angle
    )

    logger.info(f"Traversed arc angle: {traversed_arc_angle}")



    if show_plot or save_plot_filename_provider is not None:
        fig, axes = plt.subplots(2, 2)

        ax1 = axes[0][0]
        ax2 = axes[0][1]
        ax3 = axes[1][0]
        ax4 = axes[1][1]

        plot_trajectory(
            fig=fig,
            ax=ax1,
            init_pos=init_pos,
            init_heading=init_heading,
            target_pos=target_pos,
            target_heading=target_heading,
            O=O,
            x1=x1,
            circ=circC1,
            x2=x2_1,
            # lOG=lOG1,
            # x1_perp_line_pts=perp_line_pts,
            circ_forward=True
        )

        plot_trajectory(
            fig=fig,
            ax=ax2,
            init_pos=init_pos,
            init_heading=init_heading,
            target_pos=target_pos,
            target_heading=target_heading,
            O=O,
            x1=x1,
            circ=circC1,
            x2=x2_1,
            # lOG=lOG1,
            # x1_perp_line_pts=perp_line_pts,
            circ_forward=False
        )

        plot_trajectory(
            fig=fig,
            ax=ax3,
            init_pos=init_pos,
            init_heading=init_heading,
            target_pos=target_pos,
            target_heading=target_heading,
            O=O,
            x1=x1,
            circ=circC2,
            x2=x2_2,
            # lOG=lOG2,
            # x1_perp_line_pts=perp_line_pts,
            circ_forward=True
        )

        plot_trajectory(
            fig=fig,
            ax=ax4,
            init_pos=init_pos,
            init_heading=init_heading,
            target_pos=target_pos,
            target_heading=target_heading,
            O=O,
            x1=x1,
            circ=circC2,
            x2=x2_2,
            # lOG=lOG2,
            # x1_perp_line_pts=perp_line_pts,
            circ_forward=False
        )

        if save_plot_filename_provider is not None:
            fp = tp.resolve(save_plot_filename_provider)
            plt.savefig(fp)

        if show_plot:
            plt.show(block=True)


def plot_trajectory(
        fig,
        ax,
        init_pos,
        init_heading,
        target_pos,
        target_heading,
        O,
        x1,
        circ,
        x2,
        # lOG,
        # x1_perp_line_pts,
        circ_forward
):
    if circ_forward:
        arc =  (circ[0], circ[1], vec.rads(x2, circ[0]), vec.rads(x1, circ[0]))
    else:
        arc = (circ[0], circ[1], vec.rads(x1, circ[0]), vec.rads(x2, circ[0]))


    crs = np.cross(init_heading, target_heading)
    dt = np.dot(init_heading, target_heading)
    cplot._plot(
        fig=fig,
        ax=ax,
        pts={init_pos: (('r+',), {}),
             target_pos: (('g*',), {}),
             O: (('m.',), {}),
             x1: (('c+',), {}),
             circ[0]: (('b+',), {}),
             x2: (('c+',), {}),
             },
        lines={
            (init_pos, O): ((), {'linestyle': 'dotted', 'color': 'grey'}),
            (init_pos, x1): ((), {'color': 'blue', 'linewidth': 0.75}),
            (target_pos, O): ((), {'linestyle': 'dotted', 'color': 'grey'}),
            # lOG: ((), {'linestyle': 'dotted', 'color': 'orange', 'linewidth': .5}),
            # x1_perp_line_pts: ((), {'linestyle': 'dotted', 'color': 'green', 'linewidth': .5}),
            (x1, circ[0]): ((), {'linestyle': 'dotted', 'color': 'green', 'linewidth': .5}),
            (circ[0], O): ((), {'linestyle': 'dotted', 'color': 'orange', 'linewidth': .5}),
            (x2, target_pos): ((), {'color': 'blue', 'linewidth': 0.75}),
        },
        circles={
            circ: ((), {'linestyle': 'dotted', 'edgecolor': 'blue', 'facecolor': 'none', 'linewidth': .5}),
        },
        arrows={
            (target_pos, vec.scaled_to_length(target_heading, 10)): (
            (), {'color': 'black', 'length_includes_head': True, 'head_width': .3, 'linewidth': 1.5}),
            (init_pos, vec.scaled_to_length(init_heading, 10)): (
            (), {'color': 'black', 'length_includes_head': True, 'head_width': .3, 'linewidth': 1.5})
        },
        arcs={
            arc: ((), {'linewidth': 0.75})
        }
    )
    # ax.set_title(f"cross: {round(float(crs), 1)}, dot: {round(float(dt), 1)}")
    # ax.set_aspect('equal', adjustable='box')  # Ensures the circle appears circular


if __name__ == "__main__":
    from cooptools.loggingHelpers import BASE_LOG_FORMAT
    import random as rnd
    from cooptools import os_manip as osm

    logging.basicConfig(format=BASE_LOG_FORMAT, level=logging.INFO)

    def t01(
            init_pos,
            init_heading,
            target_pos,
            target_heading,
            l: float,
            show_plot: bool,
    ):
        circ_arc_trajectory_planner(
            init_pos=init_pos,
            init_heading=init_heading,
            target_pos=target_pos,
            target_heading=target_heading,
            show_plot=show_plot,
            l=l
        )


    def t02(test_count: int):
        boundary = 400, 400
        run_id = time.perf_counter()



        dir = fr"C:\Users\Tj Burns\Downloads\tst_trajectory"
        dir = fr"{dir}\{run_id}"
        osm.check_and_make_dirs(dir)

        l = rnd.uniform(0, 20)

        for ii in range(test_count):
            circ_arc_trajectory_planner(
                init_pos=(rnd.uniform(0, boundary[0]), rnd.uniform(0, boundary[0])),
                init_heading=vec.random_radial(len_boundary=(30, 50)),
                target_pos=(rnd.uniform(0, boundary[0]), rnd.uniform(0, boundary[0])),
                target_heading=vec.random_radial(len_boundary=(30, 50)),
                save_plot_filename_provider=fr"{dir}\{ii}.png",
                l=l
            )



    # t01(
    #     init_pos=(10, 20),
    #     init_heading=(1, 2),
    #     target_pos=(30, 1),
    #     target_heading=(-1, 0),
    #     plot=True,
    #     l=10
    # )
    #
    # t01(
    #     init_pos=(10, 20),
    #     init_heading=(-3, 2),
    #     target_pos=(30, 1),
    #     target_heading=(-1, 0),
    #     plot=True,
    #     l=10
    # )

    # t01(
    #     init_pos=(10, 20),
    #     init_heading=(-3, 2),
    #     target_pos=(30, 1),
    #     target_heading=(-1, -8),
    #     show_plot=True,
    #     l=0
    # )

    # t01(
    #     init_pos=(10, 20),
    #     init_heading=(1, 2),
    #     target_pos=(30, 1),
    #     target_heading=(-1, 0),
    #     show_plot=True,
    #     l=-30
    # )

    t02(10)