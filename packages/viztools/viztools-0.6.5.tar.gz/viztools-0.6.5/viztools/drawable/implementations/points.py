import time
from typing import Iterable, Tuple, Dict, Optional, Union

import pygame as pg
import numpy as np

from viztools.coordinate_system import CoordinateSystem
from viztools.drawable.base_drawable import Drawable
from viztools.drawable.draw_utils.chunking import ChunkGrid
from viztools.utils import RenderContext, normalize_color


class Points(Drawable):
    def __init__(
            self, points: np.ndarray, size: int | float | Iterable[int | float] = 3,
            color: Optional[np.ndarray] = None, chunk_size: float = 200.0, visible: bool = True,
    ):
        """
        Drawable to display a set of points.
        :param points: A list of points with the shape [N, 2] where N is the number of points.
        :param size: The radius of the points. If set to an integer, this is the radius on the screen in pixels. If set
                     to a float, this is the radius on the screen in units of the coordinate system. If set to a list,
                     it contains the sizes for each point.
        :param color: The color of the points.
        :param chunk_size: The size of the chunks in world coordinates used for rendering.
            Bigger chunks are faster for render, but can lead to lag.
        :param visible: If False, the points are not rendered.
        """
        super().__init__(visible)

        # points
        if not isinstance(points, np.ndarray):
            raise TypeError(f'points must be a numpy array, not {type(points)}.')
        if points.ndim != 2 or points.shape[1] != 2:
            raise ValueError(f'points must be numpy array with shape (N, 2), not {points.shape}.')
        n_points = len(points)
        self._points = points

        # size
        if isinstance(size, (int, float)):
            is_relative_size = isinstance(size, float)
            size = np.repeat(np.array([[size, float(is_relative_size)]], dtype=np.float32), n_points, axis=0)
        elif isinstance(size, np.ndarray):
            if size.shape != (n_points,):
                raise ValueError(f'size must be a numpy array with shape ({n_points},), not {size.shape}.')
            is_relative_size = np.full(n_points, np.issubdtype(size.dtype, np.floating), dtype=np.float32)
            size = np.stack([size.astype(np.float32), is_relative_size], axis=1)
        elif isinstance(size, list):
            if len(size) != n_points:
                raise ValueError(f'size must be a list of length {n_points}, not {len(size)}.')
            size = [[s, isinstance(s, float)] for s in size]
            size = np.array(size, dtype=np.float32)
        else:
            raise TypeError(f'size must be an integer, float or iterable, not {type(size)}.')
        self._size = size

        # colors
        if color is None:
            color = np.array([77, 178, 11])
        if isinstance(color, np.ndarray):
            if color.shape == (3,):
                color = np.array([*color, 255], dtype=np.float32)
            if color.shape == (4,):
                color = np.repeat(color.reshape(1, -1), n_points, axis=0).astype(np.float32)
        else:
            color = np.array(color, dtype=np.float32)
        if color.shape != (n_points, 4):
            raise ValueError(f'colors must be a numpy array with shape ({n_points}, 4), not {color.shape}.')
        self._colors = color

        self._surface_parameters = {}
        for surf_params in self._get_surf_params():
            self._surface_parameters[surf_params.tobytes()] = surf_params

        self.current_chunks: ChunkGrid = self._build_chunk_grid(100.0, chunk_size=chunk_size)
        self.last_zoom_factor = None

    def __len__(self):
        return len(self._points)

    def _build_chunk_grid(self, zoom_factor: float, chunk_size: float = 200.0) -> ChunkGrid:
        sizes = _get_world_sizes(self._size[:, 0], self._size[:, 1], zoom_factor)
        return ChunkGrid.from_points(self._points, sizes, chunk_size / zoom_factor)

    def _get_surf_params(self) -> np.ndarray:
        return np.concatenate([self._size, self._colors], axis=1)

    def _get_surf_param(self, index: int) -> np.ndarray:
        return np.concatenate([self._size[index, :], self._colors[index, :]], axis=0)

    def set_color(self, color: Union[np.ndarray, Tuple[int, int, int, int]], index: int):
        self._colors[index, :] = normalize_color(color)
        self._update_surf_params(index)

        # mark chunk to render new
        chunk_index = int(self.current_chunks.point_chunk_indices[index])
        self.current_chunks.set_status(chunk_index, 2)

    def _update_surf_params(self, index: int):
        surf_params = self._get_surf_param(index)
        self._surface_parameters[surf_params.tobytes()] = surf_params

    def set_size(self, size: int | float, index: int):
        self._size[index, 0] = size
        self._size[index, 1] = isinstance(size, float)
        self._update_surf_params(index)

    def _create_point_surfaces(self, zoom_factor: float) -> Dict[bytes, pg.Surface]:
        surfaces = {}
        for k, surf_params in self._surface_parameters.items():
            draw_size = _get_draw_size(surf_params[0], zoom_factor, bool(surf_params[1]))
            color = surf_params[2:]

            # old version with per pixel alpha
            point_surface = pg.Surface((draw_size * 2, draw_size * 2), pg.SRCALPHA)
            pg.draw.circle(point_surface, color, (draw_size, draw_size), draw_size)

            surfaces[k] = point_surface
        return surfaces

    def _get_draw_sizes(self, zoom_factor: float, sizes: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Computes the draw sizes for the given sizes and coordinate system.
        :param zoom_factor: A float defining the scale factor for relative sizes.
        size[i] must be multiplied with zoom_factor.
        :return: numpy array of integers of shape [N,] where N is the number of sizes.
        """
        if sizes is None:
            sizes = self._size
        draw_sizes = sizes[:, 0].copy()
        is_relative_size = sizes[:, 1] > 0.5
        draw_sizes[is_relative_size] *= zoom_factor
        return np.maximum(draw_sizes.astype(int), 1)

    def update_chunks(self, coordinate_system: CoordinateSystem, screen_size: Tuple[int, int]) -> bool:
        point_surfaces = self._create_point_surfaces(coordinate_system.zoom_factor)

        if self.last_zoom_factor is None or self.last_zoom_factor != coordinate_system.zoom_factor:
            self.last_zoom_factor = coordinate_system.zoom_factor
            viewport = coordinate_system.get_viewport(screen_size)
            new_sizes = _get_world_sizes(self._size[:, 0], self._size[:, 1], coordinate_system.zoom_factor)
            self.current_chunks.resize_chunks(coordinate_system.zoom_factor, viewport, new_sizes)

        start_time = time.perf_counter()
        while True:
            update_needed = self.render_next_chunk(coordinate_system, point_surfaces, screen_size)
            if not update_needed:
                return False
            if time.perf_counter() - start_time > 1 / 60:
                break
        return True

    def render_next_chunk(self, coordinate_system, point_surfaces, screen_size):
        viewport = coordinate_system.get_viewport(screen_size)
        update_index = self.current_chunks.get_next_update_chunk(viewport)
        if update_index is not None:
            sizes = _get_world_sizes(self._size[:, 0], self._size[:, 1], coordinate_system.zoom_factor)
            self.current_chunks.render_chunk(
                update_index, self._points, sizes, self._get_surf_params(), coordinate_system.zoom_factor,
                point_surfaces
            )
            return True
        return False

    def update(self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext) -> bool:
        return self.update_chunks(coordinate_system, screen.get_size())

    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext):
        # draw points in chunks
        viewport = coordinate_system.get_viewport(screen.get_size())
        chunk_indices = self.current_chunks.get_in_viewport_chunk_indices(viewport)
        if self.current_chunks.get_pixel_approx(coordinate_system.zoom_factor) > 4000:
            # too many pixels: immediate mode

            # create blit surfaces
            surfaces = self._create_point_surfaces(coordinate_system.zoom_factor)

            # draw points in chunks
            for chunk_index in chunk_indices:
                chunk_index_tuple = self.current_chunks.chunk_index_tuple(chunk_index)
                point_indices = self.current_chunks.chunk_point_indices[chunk_index_tuple]
                screen_size = np.array(screen.get_size(), dtype=np.int32)

                # only consider points in chunk
                chunk_points = self._points[point_indices]
                chunk_sizes = self._size[point_indices]
                chunk_draw_sizes = self._get_draw_sizes(coordinate_system.zoom_factor, chunk_sizes)
                chunk_surf_params = self._get_surf_params()[point_indices]

                # filter out points outside of screen
                screen_points = coordinate_system.space_to_screen_t(chunk_points)
                valid_positions = _get_valid_positions(screen_points, chunk_draw_sizes, screen_size)
                screen_points = screen_points[valid_positions]
                valid_sizes = chunk_draw_sizes[valid_positions]
                screen_points -= valid_sizes.reshape(-1, 1)
                valid_surf_params = chunk_surf_params[valid_positions]

                # draw
                for pos, surf_params in zip(screen_points, valid_surf_params):
                    surface = surfaces[surf_params.tobytes()]
                    screen.blit(surface, pos)
        else:
            for chunk_index in chunk_indices:
                chunk_x, chunk_y = self.current_chunks.chunk_index_tuple(chunk_index)
                if self.current_chunks.status[chunk_x, chunk_y] == 1:
                    self.current_chunks.resize_chunk((chunk_x, chunk_y), coordinate_system.zoom_factor)
                chunk_surface = self.current_chunks.get_surface((chunk_x, chunk_y))
                if chunk_surface is not None:
                    chunk_frame = self.current_chunks.get_chunk_frame((chunk_x, chunk_y))
                    left_top = np.array([[chunk_frame[0], chunk_frame[1]]])
                    left_top_screen = coordinate_system.space_to_screen_t(left_top)
                    left_top_screen = (int(left_top_screen[0, 0]), int(left_top_screen[0, 1]))
                    screen.blit(chunk_surface, left_top_screen)

    def handle_event(
            self, event: pg.event.Event, screen: pg.Surface, coordinate_system: CoordinateSystem,
            render_context: RenderContext
    ):
        pass

    def clicked_points(self, event: pg.event.Event, coordinate_system: CoordinateSystem) -> np.ndarray:
        """
        Returns the indices of the points clicked by the mouse. Returns an empty array if no point was clicked.

        :param event: The event to check.
        :param coordinate_system: The coordinate system to use.
        """
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            return self.hovered_points(np.array(event.pos, dtype=np.int32), coordinate_system)
        return np.array([])

    def hovered_points(self, mouse_pos: np.ndarray, coordinate_system: CoordinateSystem) -> np.ndarray:
        draw_sizes = self._get_draw_sizes(coordinate_system.zoom_factor)

        screen_pos = mouse_pos.reshape(1, 2)
        screen_points = coordinate_system.space_to_screen_t(self._points)
        distances = np.linalg.norm(screen_points - screen_pos, axis=1)
        return np.nonzero(distances < draw_sizes)[0]

    def closest_point(
            self, pos: np.ndarray, coordinate_system: CoordinateSystem, dist_to_center: bool = False
    ) -> Tuple[int, float]:
        """
        Finds the closest point to the given position.

        This function calculates the closest point to a specified 2D position on
        the screen.

        :param pos: The 2D position in screen coordinates to calculate the distance from.
        :param coordinate_system: The coordinate system used for transforming space
                                  coordinates to screen coordinates.
        :param dist_to_center: If False, the distance is calculated as the distance between the edge of point and <pos>.
            If True, the distance is calculated as the distance between the center of the point and <pos>.
        :return: A tuple containing the index of the closest point and the distance
                 to that closest point.
        :rtype: Tuple[int, float]
        """
        screen_pos = pos.reshape(1, 2)
        screen_points = coordinate_system.space_to_screen_t(self._points)
        distances = np.linalg.norm(screen_points - screen_pos, axis=1)
        if not dist_to_center:
            distances -= self._get_draw_sizes(coordinate_system.zoom_factor)
        closest_index = np.argmin(distances)
        return int(closest_index), max(float(distances[closest_index]), 0.0)


def _get_draw_size(
        size: float, zoom_factor: float, is_relative_size: bool
) -> int:
    if is_relative_size:
        size = max(int(size * zoom_factor), 1)
    return int(size)


def _get_world_sizes(sizes: np.ndarray, is_relative: np.ndarray, zoom_factor: float) -> np.ndarray:
    """
    Converts sizes from screen or world sizes to world sizes.
    :param sizes: Float array with shape [N,] where N is the number of sizes.
    :param is_relative: Float array with shape [N,] where N is the number of sizes. 1.0 means relative size, 0.0 means
    absolute size.
    :param zoom_factor: The zoom factor. world_size = draw_size / zoom_factor
    :return: For each index i, returns the world size for size[i]
    """
    is_absolute = is_relative < 0.5
    world_sizes = sizes.copy()
    world_sizes[is_absolute] /= zoom_factor
    return world_sizes


def _get_valid_positions(screen_points: np.ndarray, draw_sizes: np.ndarray, screen_size: np.ndarray) -> np.ndarray:
    return np.where(np.logical_and(
        np.logical_and(screen_points[:, 0] > -draw_sizes, (screen_points[:, 0] < screen_size[0] + draw_sizes)),
        np.logical_and(screen_points[:, 1] > -draw_sizes, (screen_points[:, 1] < screen_size[1] + draw_sizes))
    ))[0]
