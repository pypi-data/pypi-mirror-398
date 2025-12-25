from cooptools.sectors import RectGrid
from cooptools.geometry_utils import rect_utils as rect
from cooptools.geometry_utils import polygon_utils as poly
from cooptools.geometry_utils import vector_utils as vec
from typing import Dict, Any, Tuple, List, Callable, Iterable, Self
import cooptools.sectors.sect_utils as sec_u
from cooptools.coopEnum import CardinalPosition
import logging
import matplotlib.patches as patches
import random as rnd
import matplotlib.pyplot as plt
from cooptools.colors import Color
from cooptools.plotting import plot_series
from cooptools.protocols import UniqueIdentifier
from cooptools.geometry_utils import rect_utils as rect
from cooptools import common as comm
from cooptools.common import is_non_string_iterable
import time
from pprint import pprint

logger = logging.getLogger(__name__)

ObjInSectorComparer = Callable[[rect.Rect, UniqueIdentifier], bool]


class SectorTree:
    def __init__(self,
                 area_rect: rect.Rect,
                 capacity: int,
                 shape: Tuple[int, int],
                 obj_collider_provider: Callable[[UniqueIdentifier], vec.IterVec | vec.FloatVec],
                 sector_comparer: ObjInSectorComparer = None,
                 parent=None,
                 lvl: int = None,
                 max_lvls: int = None):
        self.parent = parent
        self.children: Dict[Tuple[int, int], (rect.Rect, SectorTree)] = {}
        self.capacity = capacity
        self.grid = RectGrid(shape[0], shape[1])
        self._area = area_rect
        self._client_mapping = {}
        self._last_mapped_pos = {}
        self.lvl = lvl if lvl else 0
        self.max_lvls = max_lvls
        self._object_collider_provider = obj_collider_provider
        self._client_type_map: Dict[str, str] = {}

        comm.verify_val(val=self.capacity, gt=0, error_msg=f"Invalid value for capacity: {self.capacity}")

        lam_default_poly_in_sector_comparer = lambda x, to_check: poly.do_convex_polygons_intersect(
            list(rect.rect_corners(x).values()),
            self._object_collider_provider(to_check))
        self._obj_in_sector_comparer = sector_comparer or lam_default_poly_in_sector_comparer

        self._init_children()

    def _init_children(self):
        areas = {
            grid_pos:
                sec_u.sector_rect(sector_dims=sec_u.sector_dims(self._area[2:4],
                                                                sector_def=self.grid.Shape),
                                  sector=grid_pos,
                                  area_origin=self._area[0:2])
            for grid_pos, _ in self.grid.grid_enumerator
        }

        self.children = {grid_pos: (areas[grid_pos], None) for grid_pos, _ in self.grid.grid_enumerator}

    def _obj_in_sector(self, sector, id):
        obj_points = self._object_collider_provider(id)
        self._last_mapped_pos[id] = obj_points

        if len(obj_points) == 1:
            return rect.rect_contains_point(sector, obj_points[0])
        elif type(obj_points[0]) in [int, float]:
            return rect.rect_contains_point(sector, obj_points)
        elif not is_non_string_iterable(obj_points[0]):
            return rect.rect_contains_point(sector, obj_points)
        elif len(obj_points) > 1:
            return poly.do_convex_polygons_intersect(
                list(rect.rect_corners(sector).values()),
                obj_points)
        else:
            raise ValueError(f"object needs at least one point")

    def __str__(self):
        return f"{self.DeepMappings}, \n{self.children}"

    def _add_child_layer(self, grid_pos: Tuple[int, int]):
        # child_rect = sec_u.sector_rect(
        #     sector_dims=sec_u.sector_dims(area_dims=(self._area[2], self._area[3]),
        #                                   sector_def=self.grid.Shape
        #                                   ),
        #     sector=grid_pos,
        #     area_origin=(self._area[0], self._area[1])
        # )

        # add a new SectorTree as a child to the grid pos
        child_rect = self.children[grid_pos][0]
        new_sector = SectorTree(area_rect=child_rect,
                                capacity=self.capacity,
                                obj_collider_provider=self._object_collider_provider,
                                sector_comparer=self._obj_in_sector_comparer,
                                shape=self.grid.Shape,
                                parent=self,
                                lvl=self.lvl + 1,
                                max_lvls=self.max_lvls)

        self.children[grid_pos] = (child_rect, new_sector)

        # update clients in child at grid pos. This should happen whenever you add a child. it should iterate the
        # clients at the grid pos and add them to the child layer appropriately
        clients = self._client_mapping.get(grid_pos, None)
        self.children[grid_pos][1].add_update_clients({x: self._client_type_map[x] for x in clients})

        logger.info(f"child layer added at Lvl {self.lvl}: {grid_pos} with area rect: {child_rect}")

    def _handle_child_layer(self, grid_pos: Tuple[int, int]):

        # capacity has not been reached (mult clients at shared pos are treated as 1). Therefore, we choose not
        # to add a child (or handle). We can return early bc there is not a reason to handle children in this case.
        # Additionally, we do not want to continue if we have reached our max-level depth
        clients = self.ClientMappings.get(grid_pos, None)

        if clients is None \
                or len(clients) <= self.capacity \
                or (self.max_lvls is not None and self.lvl >= self.max_lvls - 1) \
                or self.children.get(grid_pos, None)[1] is not None:
            return False

        # there is no child but capacity is reached. we need to add a child layer to the tree
        if self.children.get(grid_pos, None)[1] is None and len(clients) > self.capacity:
            self._add_child_layer(grid_pos)
            return True

        raise ValueError(f"Coding error... Outside the expected two conditions")

    def add_update_clients(self, clients: Dict[UniqueIdentifier, UniqueIdentifier]):

        self._client_type_map.update(clients)

        areas = {
            grid_pos:
                sec_u.sector_rect(sector_dims=sec_u.sector_dims(self._area[2:4],
                                                                sector_def=self.grid.Shape),
                                  sector=grid_pos,
                                  area_origin=self._area[0:2])
            for grid_pos, _ in self.grid.grid_enumerator
        }

        for client, type in clients.items():
            if self.lvl == 0:
                if client in self.Clients:
                    logger.info(f"User requests updating [{client}]")
                else:
                    logger.info(f"User requests adding [{client}]")

                if not client.__hash__:
                    raise Exception(f"Client {client} must be hashable, but type {type(client)} is not")

            # check if can skip since already up to date
            # TODO: This was implemented w. pos, harder in abstract sense

            # check if already have client in but at a different location
            # TODO: This was implemented w. pos, harder in abstract sense

            # Check which grid_pos client belongs to
            for grid_pos, _ in self.grid.grid_enumerator:
                area = areas[grid_pos]
                self._client_mapping.setdefault(grid_pos, set())

                # Check if the client is in the sector, and not in any other sectors (handling on-line case)
                if self._obj_in_sector(area,
                                       client):  # and not any(client in v for k, v in self._client_mapping.items()):
                    self._client_mapping[grid_pos].add(client)
                    logger.info(f"client [{client}] added to Lvl {self.lvl}: {grid_pos}")

                    # handle child lvl
                    layer_added = self._handle_child_layer(grid_pos)

                    if not layer_added and self.children.get(grid_pos, None)[1] is not None:
                        self.children[grid_pos][1].add_update_clients({client: self._client_type_map[client]})
        return self

    def remove_clients(self, clients: Iterable):
        for client in clients:
            # if not a member, early out
            if client not in self._last_mapped_pos.keys():
                return

            logger.info(f"removing client [{client}] from {self.lvl}: {self._last_mapped_pos[client]}")

            # delete from last mapped
            del self._last_mapped_pos[client]

            # delete from client mappings
            for grid_pos, clients in self._client_mapping.items():
                if client in clients:
                    clients.remove(client)

            # handle children
            to_remove = []
            for pos, child in self.children.items():
                child_sector, child_rect = child
                # remove client from child
                child_sector.remove_clients(client)

                # remove child if empty
                positions = set([pos for client, pos in child_sector.ClientsPos.items()])
                if len(positions) <= self.capacity:
                    to_remove.append(pos)

            for child in to_remove:
                del self.children[child]
        return self

    def nearby_clients(self,
                       radius: float, pt: Tuple[float, float],
                       client_types: Iterable[str] = None) -> Dict[Any, Tuple[float, float]]:
        t0 = time.perf_counter()

        sectors_nearby = self._sectors_potentially_overlaps_radius(radius, pt)
        corners_nearby = self._sector_corners_nearby(radius, pt)

        clients = {}
        for sector, nearby in sectors_nearby.items():
            # if sector is not nearby, continue
            if not nearby:
                continue

            # if sector is determined to be nearby, check if all 4 corners are nearby. If so, easily assume that all
            # its member clients are also nearby and early out.
            # For case when it is nearby, but no clients, also early out
            if corners_nearby[sector] == 4 and self._client_mapping.get(sector, None) is not None:
                sec_clients = self._client_mapping.get(sector, [])
                clients.update({client: self._last_mapped_pos[client] for client in sec_clients})
                continue

            # if there is a child, find nearby in child
            if self.children.get(sector, None)[1] is not None:
                nearby_in_child = self.children[sector][1].nearby_clients(radius, pt)
                clients.update(nearby_in_child)
            # sector is nearby, no child but there are mapped clients
            elif self._client_mapping.get(sector, None) is not None:
                nearby_in_sector = self._nearby_in_my_sector(sector, radius, pt)
                clients.update(nearby_in_sector)

        t1 = time.perf_counter()
        if self.lvl == 0:
            logger.info(
                f"Time to calculate Nearby time: {round(t1 - t0, 7)}s for {len(self.Clients)} registered clients")

        if client_types is not None:
            clients = [x for x in clients if self._client_type_map[x] in client_types]

        return clients

    def _nearby_in_my_sector(self,
                             sector: Tuple[int, int],
                             radius: float,
                             pt: Tuple[float, float]) -> Dict[Any, Tuple[float, float]]:
        # collect clients in sector
        # sector_clients = list(self._client_mapping[sector])
        nearby_in_sector = {client: self._last_mapped_pos[client] for client in self._client_mapping[sector]}

        # prune clients in sector that arent actually nearby by enumerating against the convex_qualifier
        to_prune = []
        for client, pos in nearby_in_sector.items():
            # handle if the pos of the client is a polygon rather than a point

            if len(pos) == 1 and not self._within_radius_of_point(pos[0], radius, pt):
                to_prune.append(client)
            elif not is_non_string_iterable(pos[0]) and not self._within_radius_of_point(pos, radius, pt):
                to_prune.append(client)
            elif len(pos) > 1 and is_non_string_iterable(pos[0]):
                bound_rect = rect.bounding_rect(pos)
                if not rect.check_overlaps_circle(bound_rect, (pt, radius)):
                    to_prune.append(client)

        for client in to_prune:
            del nearby_in_sector[client]

        # TODO: Should probably inject a formal comparison of the direct polygon to circle. However, that requires a
        # custom implementation OR a shapely dependency that im not ready to include. Therefore, satisfied with the
        # bounding rect/circ comparison approximation

        # for client, pos in nearby_in_sector.items():
        #     self._obj_in_sector_comparer

        return nearby_in_sector

    def _sector_corners_nearby(self, radius: float, pt: Tuple[float, float]):
        ret = {}
        for pos, sector in self.MySectors.items():
            sector_rect, layer = sector
            corners = rect.rect_corners(sector_rect)

            tl = self._within_radius_of_point(corners[CardinalPosition.TOP_LEFT], radius=radius, pt=pt)
            tr = self._within_radius_of_point(corners[CardinalPosition.TOP_RIGHT], radius, pt)
            bl = self._within_radius_of_point(corners[CardinalPosition.BOTTOM_LEFT], radius, pt)
            br = self._within_radius_of_point(corners[CardinalPosition.BOTTOM_RIGHT], radius, pt)
            ret[pos] = sum([tl, tr, bl, br])

        return ret

    def _within_radius_of_point(self, check: Tuple[float, float], radius: float, pt: Tuple[float, float]):
        return vec.distance_between(check, pt) <= radius

    def _sectors_potentially_overlaps_radius(self, radius: float, pt: Tuple[float, float]):
        ret = {}
        for pos, sector in self.MySectors.items():
            sector_area, layer = sector
            ret[pos] = False

            # determine if the bounding circle of my area plus the radius given to check is more than the distance
            # between the center of my area and the point to be checked. If the combined distance of the two radius's is
            # smaller than the distance between center and pt, we can safely assume that the area of the sector does NOT
            # intersect with the area being checked. However if it is larger, there is a potential that the area falls
            # within the checked area
            if rect.bounding_circle_radius(sector_area) + radius >= vec.distance_between(pt,
                                                                                         rect.rect_center(sector_area)):
                ret[pos] = True
        return ret

    @property
    def ClientMappings(self) -> Dict[Tuple[int, int], set[Any]]:
        return self._client_mapping

    @property
    def Clients(self) -> List[UniqueIdentifier]:
        return list(set(comm.flattened_list_of_lists(v for v in self.ClientMappings.values())))

    @property
    def DeepMappings(self) -> Dict[Tuple[int, int], set[Any]]:
        # Will include a dict of:
        #   - list of clients
        #   - the boundary area of the sector
        #   - the nested deep mappings of the children (dict)

        return {
            k: (list(v),
                self.children[k][1].Area,
                self.children[k][1].DeepMappings) if self.children[k][1] is not None
            else (list(v), self.children[k][0], {})
            for k, v in self.ClientMappings.items()
        }

    @property
    def JsonableDeepMappings(self) -> Dict[str, Dict]:
        return {
            str(k): (list(v),
                     self.children[k][0].Area,
                     self.children[k][0].JsonableDeepMappings) if self.children[k][1] is not None
            else (list(v), self.children[k][1], {})
            for k, v in self.ClientMappings.items()
        }

    @property
    def MySectors(self) -> Dict[Tuple[float, float], rect.Rect]:
        mine = {}
        sec_def = sec_u.rect_sector_attributes((self._area[2], self._area[3]), self.grid.Shape)
        for pos, _ in self.grid.grid_enumerator:
            _rect = (
                pos[0] * sec_def[0] + self._area[0],
                pos[1] * sec_def[1] + self._area[1],
                sec_def[0],
                sec_def[1]
            )

            mine[pos] = (_rect, self.lvl)

        return mine

    @property
    def Sectors(self) -> Dict[Tuple[float, float], Tuple[rect.Rect, int]]:
        """
        This returns a Dict of the grid_pos of the sector, and the defining rect/level
        :return:
        """

        childrens = {}
        for pos, child in self.children.items():
            child_area, child_sector = child
            childrens.update(
                {f"{pos}/{k}": v for k, v in child_sector.Sectors.items()} if child_sector is not None else {})

        return {**self.MySectors, **childrens}

    @property
    def Area(self) -> rect.Rect:
        return self._area

    def plot(self,
             ax,
             fig,
             nearby_pt: Tuple[float, float] = None,
             radius: float = None,
             pt_color: Color = None):

        point_clients = [point for client, point in self.ClientsPos.items() if not is_non_string_iterable(point[0])]
        boundary_clients = [point for client, point in self.ClientsPos.items() if is_non_string_iterable(point[0])]

        plot_series(point_clients,
                    ax=ax,
                    color=pt_color,
                    fig=fig,
                    series_type='scatter',
                    zOrder=4)

        for x in boundary_clients:
            plot_series(x + [x[0]],
                        ax=ax,
                        color=pt_color,
                        fig=fig,
                        series_type='line',
                        zOrder=4)

        if nearby_pt is not None and radius is not None:
            nearbys = self.nearby_clients(pt=nearby_pt, radius=radius)
            plot_series([point for client, point in nearbys.items()], fig=fig, ax=ax, color=pt_color,
                        series_type='scatter', zOrder=4)

        sectors_to_draw = [(pos, sector[0], sector[1]) for pos, sector in self.Sectors.items()]
        sectors_to_draw.sort(key=lambda x: x[2], reverse=True)
        for pos, sect_rect, layer in sectors_to_draw:
            color_map = {
                0: (Color.DARK_BLUE, 2),
                1: (Color.DODGER_BLUE, 1),
                2: (Color.LIGHT_BLUE, 0.5)
            }

            rect = patches.Rectangle((sect_rect[0], sect_rect[1]),
                                     sect_rect[2],
                                     sect_rect[3],
                                     linewidth=color_map.get(layer, (0, 0.25))[1],
                                     edgecolor=color_map.get(layer, (Color.LIGHT_GRAY,))[0].as_hex(),
                                     facecolor='none')
            if layer < 2:
                ax.text(sect_rect[0], sect_rect[1], pos)

            ax.add_patch(rect, )

    @property
    def ClientsPos(self) -> Dict[Any, Tuple[float, float]]:
        return self._last_mapped_pos

    @property
    def CoLocatedClients(self) -> Dict:
        ret = {}

        for grid_pos, clients in self.ClientMappings.items():
            gpcc = None

            for client in clients:
                ret.setdefault(client, set())

                if (grid_pos in self.children
                        and self.children[grid_pos][1] is not None
                        and client in self.children[grid_pos][1].Clients
                ):
                    if gpcc is None:
                        gpcc = self.children[grid_pos][1].CoLocatedClients

                    ret[client] = ret[client].union(gpcc[client])

                else:
                    ret[client] = ret[client].union(set([x for x in clients if x != client]))
        return ret


class SectorTreeUnitTests():
    @staticmethod
    def assemble(shape: Tuple = (2, 2),
                 area: Tuple = (0, 0, 400, 400)):
        _rect = area

        obj_areas = {
            "1": list(rect.rect_corners((100, 100, 99, 10)).values()),
            "2": list(rect.rect_corners((100, 100, 10, 99)).values()),
            "3": list(rect.rect_corners((150, 150, 100, 100)).values()),
            # "4": list(rect.rect_corners((10, 150, 100, 100)).values()),
        }

        qt = SectorTree(area_rect=_rect,
                        shape=shape,
                        obj_collider_provider=lambda x: obj_areas[x],
                        capacity=1,
                        max_lvls=3).add_update_clients(clients={x: "NA" for x in obj_areas.keys()})

        return qt

    @staticmethod
    def test_2x2_3clients(plot: bool = False):
        qt = SectorTreeUnitTests.assemble((2, 2))

        assert len(qt.Clients) == 3
        dms = qt.DeepMappings

        if plot:
            fig, ax = plt.subplots()
            qt.plot(ax=ax, fig=fig)
            pprint(dms)
            plt.show(block=True)

        assert '3' in dms[(0, 0)][0]
        assert '3' in dms[(1, 1)][0]
        assert '3' in dms[(1, 0)][0]
        assert '3' in dms[(0, 1)][0]

        l00 = dms[(0, 0)][2]
        assert len(l00) == 4
        assert set(l00[(0, 0)][0]) == set(['1', '2'])

        assert set(l00[(0, 1)][0]) == set(['1', '2'])
        assert set(l00[(1, 0)][0]) == set(['1', '2'])
        assert set(l00[(1, 1)][0]) == set(['1', '2', '3'])

        l00_00 = l00[(0, 0)]
        l00_01 = l00[(0, 1)]
        l00_10 = l00[(1, 0)]
        l00_11 = l00[(1, 1)]

        assert set(l00_00[2][(1, 1)][0]) == set(['1', '2'])
        assert set(l00_01[2][(1, 0)][0]) == set(['1', '2'])
        assert set(l00_01[2][(1, 1)][0]) == set(['2'])
        assert set(l00_10[2][(0, 1)][0]) == set(['1', '2'])
        assert set(l00_10[2][(1, 1)][0]) == set(['1'])
        assert set(l00_11[2][(0, 0)][0]) == set(['1', '2', '3'])
        assert set(l00_11[2][(0, 1)][0]) == set(['2', '3'])
        assert set(l00_11[2][(1, 0)][0]) == set(['1', '3'])
        assert set(l00_11[2][(1, 1)][0]) == set(['3'])

    @staticmethod
    def test_3x3_3clients(plot: bool = False):
        qt = SectorTreeUnitTests.assemble((3, 3),
                                          area=(0, 0, 400, 400))

        dms = qt.DeepMappings

        if plot:
            fig, ax = plt.subplots()
            qt.plot(ax=ax, fig=fig)
            pprint(dms)
            plt.show(block=True)

        l00 = dms[(0, 0)]
        l10 = dms[(1, 0)]
        l01 = dms[(0, 1)]
        l11 = dms[(1, 1)]
        l12 = dms[(1, 2)]
        l21 = dms[(2, 1)]
        l22 = dms[(2, 2)]
        assert set(l11[0]) == set(['3'])

        l00_22 = l00[2][(2, 2)]

        assert set(l00_22[0]) == set(['1', '2'])
        assert set(l10[0]) == set(['1'])
        assert set(l01[0]) == set(['2'])

        l00_22_00 = l00_22[2][(0, 0)]
        l00_22_01 = l00_22[2][(0, 1)]
        l00_22_02 = l00_22[2][(0, 2)]
        l00_22_10 = l00_22[2][(1, 0)]
        l00_22_11 = l00_22[2][(1, 1)]
        l00_22_12 = l00_22[2][(1, 2)]
        l00_22_20 = l00_22[2][(2, 0)]
        l00_22_21 = l00_22[2][(2, 1)]
        l00_22_22 = l00_22[2][(2, 2)]

        assert set(l00_22_00[0]) == set(['1', '2'])
        assert set(l00_22_01[0]) == set(['1', '2'])
        assert set(l00_22_02[0]) == set(['2'])
        assert set(l00_22_10[0]) == set(['1', '2'])
        assert set(l00_22_11[0]) == set(['1', '2'])
        assert set(l00_22_12[0]) == set(['2'])
        assert set(l00_22_20[0]) == set(['1'])
        assert set(l00_22_21[0]) == set(['1'])
        assert set(l00_22_22[0]) == set()

        assert set(l12[0]) == set()
        assert set(l21[0]) == set()
        assert set(l22[0]) == set()

        # pprint(dms)

        clc = qt.CoLocatedClients

        assert clc['1'] == set(['2'])
        assert clc['2'] == set(['1'])
        assert clc['3'] == set()
        # pprint(clc)

    @staticmethod
    def test2(plot: bool = False):
        _rect = (0, 0, 400, 400)
        t0 = time.perf_counter()

        obj_areas = {
            ii: list(rect.rect_corners(rect.rect_gen(_rect, max_w=100, max_h=100)).values()) for ii in range(10)
        }
        sc = lambda x, to_check: poly.do_convex_polygons_intersect(list(rect.rect_corners(x).values()),
                                                                   obj_areas[to_check])
        qt = SectorTree(area_rect=_rect,
                        # sector_comparer=sc,
                        obj_collider_provider=lambda id: obj_areas[id],
                        shape=(3, 3),
                        capacity=1,
                        max_lvls=2).add_update_clients(
            {ii: 'NA' for ii, check in obj_areas.items()}
        )

        dm = qt.DeepMappings
        pprint(dm)

        pprint(qt.CoLocatedClients)

        if plot:
            fig, ax = plt.subplots()
            qt.plot(ax=ax, fig=fig)
            plt.show(block=True)

    @staticmethod
    def test_nearbys(plot: bool = False):
        _rect = (0, 0, 400, 400)

        point_gen = lambda: (rnd.randint(0, _rect[2] - 1), rnd.randint(0, _rect[3] - 1))

        client_pos = {
            ii: point_gen() for ii in range(1000)
        }

        t0 = time.perf_counter()

        qt = SectorTree(area_rect=_rect,
                        shape=(3, 3),
                        capacity=1,
                        max_lvls=3,
                        obj_collider_provider=lambda id: client_pos[id]).add_update_clients(
            {ii: "NA" for ii, check in client_pos.items()}
        )
        t1 = time.perf_counter()
        print(f"Setup time: {t1 - t0}")

        radius = 100
        check = (50, 75)

        # PLOT
        if plot:
            fig, ax = plt.subplots()
            qt.plot(ax=ax,
                    nearby_pt=check,
                    radius=radius,
                    fig=fig)

            plt.show(block=True)

    @staticmethod
    def test_tree_viz(plot: bool = False):
        _rect = (0, 0, 400, 400)
        t0 = time.perf_counter()

        point_gen = lambda: (rnd.randint(0, _rect[2] - 1), rnd.randint(0, _rect[3] - 1))

        client_pos = {
            ii: point_gen() for ii in range(1000)
        }

        qt = SectorTree(area_rect=_rect,
                        shape=(3, 3),
                        capacity=1,
                        max_lvls=4,
                        obj_collider_provider=lambda id: client_pos[id]).add_update_clients(
            {ii: 'NA' for ii, check in client_pos.items()}
        )

        t1 = time.perf_counter()
        print(f"Create time: {t1 - t0}")

        if plot:
            fig, ax = plt.subplots()

            qt.plot(ax=ax, fig=fig)
            plt.show(block=True)


if __name__ == "__main__":
    # from cooptools.randoms import a_string
    # from cooptools.common import flattened_list_of_lists
    from cooptools.loggingHelpers import BASE_LOG_FORMAT

    logging.basicConfig(format=BASE_LOG_FORMAT, level=logging.INFO)

    rnd.seed(0)

    uts = SectorTreeUnitTests()

    deb = True
    uts.test_2x2_3clients(plot=deb)
    uts.test_3x3_3clients(plot=deb)
    uts.test_tree_viz(plot=deb)
    uts.test_nearbys(plot=deb)
