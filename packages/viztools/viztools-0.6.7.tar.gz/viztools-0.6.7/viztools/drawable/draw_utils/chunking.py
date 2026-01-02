from typing import Self, Tuple, Optional, Dict

import numpy as np
import pygame as pg


class ChunkGrid:
    def __init__(
            self, surfaces: np.ndarray, points: np.ndarray, sizes: np.ndarray, point_chunk_indices: np.ndarray,
            chunk_point_indices: np.ndarray, left_bot: np.ndarray, chunk_size: float, chunk_frames: np.ndarray,
    ):
        """
        Creates a new ChunkGrid object. This groups the given points into a grid of chunks with size (w, h).
        Each chunk consists of a pg.Surface, a rect in world coordinates defining which points are in the chunk and
        points-indices of the points in the chunk.

        :param surfaces: A numpy array with shape (w, h) of type pg.Surface.
        :param points: The center positions of points in the coordinate system with shape (n, 2).
        :param sizes: The sizes of the points in the coordinate system with shape n.
        :param point_chunk_indices: A numpy array with shape n of type int. Accessing point_indices[i] gives the
        chunk_index of the ith point. Left bottom chunk has index 0, the next chunk to the top has index 1.
        The top right chunk as index h*w-1.
        :param chunk_point_indices: A numpy array with shape (w, h).
        Accessing chunk_point_indices[x, y] gives a numpy array of indices for points in the chunk at (x, y).
        :param left_bot: The world coordinates of the bottom left corner of the bottom left chunk as a numpy array with
        shape 2 of type float.
        :param chunk_size: The size of the chunks in world coordinates.
        :param chunk_frames: A numpy array with shape (w, h, 5). Each entry[x, y] contains the
        (init, left, top, right, bottom) world coordinates of the surrounding frame. If init is 0.0, the frame is not
        initialized. The surrounding frame is the area, in which all contained points can be fully rendered.
        If no points are contained in the chunk, the frame should be zeros.
        """
        self.surfaces = surfaces
        self.points = points
        self.sizes = sizes
        self.point_chunk_indices = point_chunk_indices
        self.chunk_point_indices = chunk_point_indices
        self.left_bot = left_bot
        self.chunk_size = chunk_size
        # meaning of status:
        # - 0: not rendered
        # - 1: has to rescale
        # - 2: has to update
        # - 3: ok
        self.status = np.zeros(surfaces.shape, dtype=np.int32)
        self.chunk_frames = chunk_frames

    def shape(self) -> Tuple[int, int]:
        """
        The number of chunks in the grid as tuple (w, h).
        """
        return self.surfaces.shape

    @classmethod
    def from_points(cls, points: np.ndarray, sizes: np.ndarray, chunk_size: float) -> Self:
        """
        Create a grid of chunks from the given points. Each point is in exactly one chunk.
        Chunks are created in scanline order.

        :param points: The center positions of points in the coordinate system with shape (n, 2).
        Accessing points[i] gives the (x, y) position of point i.
        :param sizes: The sizes of the points in the coordinate system with shape n.
        :param chunk_size: The maximum size of a chunk in world size.
        :return: A ChunkGrid object.
        """
        if points.ndim != 2 or points.shape[1] != 2:
            raise ValueError(f'points must be a numpy array with shape (n, 2), not {points.shape}.')
        if not np.issubdtype(points.dtype, np.floating):
            raise ValueError(f'points must be a numpy array with floating point values, not {points.dtype}.')

        most_left_bot = np.min(points, axis=0)
        most_right_top = np.max(points, axis=0)

        world_size = most_right_top - most_left_bot
        chunks_shape = np.trunc(world_size / chunk_size).astype(np.int32) + 1

        surfaces = np.full(chunks_shape, None, dtype=object)  # numpy array of pg.Surface

        points_rel_to_bot_left = points - most_left_bot.reshape(1, 2)
        chunk_indices_per_axis = np.trunc(points_rel_to_bot_left / chunk_size)
        for dim in range(2):
            chunk_indices_per_axis[:, dim] = np.clip(chunk_indices_per_axis[:, dim], 0, chunks_shape[dim]-1)

        # index = x * h + y
        point_chunk_indices: np.ndarray = chunk_indices_per_axis[:, 1] + chunk_indices_per_axis[:, 0] * chunks_shape[1]

        chunk_point_indices = np.full(chunks_shape, None, dtype=object)

        # building chunk frames
        chunk_frames = np.zeros((*chunks_shape, 5))

        return ChunkGrid(
            surfaces, points, sizes, point_chunk_indices, chunk_point_indices, most_left_bot, chunk_size, chunk_frames
        )
    
    def get_in_viewport_chunk_indices(self, viewport: np.ndarray) -> np.ndarray:
        """
        Get chunk indices in the viewport.

        :param viewport: Numpy array of shape (2, 2) with the viewport coordinates in world coordinates.
        Accessing viewport[0] gives the top left corner of the viewport in world coordinates. Accessing viewport[1]
        gives the bottom right corner of the viewport in world coordinates.
        """
        # Convert viewport coordinates to chunk indices
        rel_viewport = (viewport - self.left_bot.reshape(1, 2)) / self.chunk_size
        left = np.trunc(rel_viewport[0, 0]).astype(np.int32)
        top = np.ceil(rel_viewport[0, 1]).astype(np.int32) - 1
        right = np.ceil(rel_viewport[1, 0]).astype(np.int32) - 1
        bot = np.trunc(rel_viewport[1, 1]).astype(np.int32)

        left_right = np.clip([left, right], 0, self.shape()[0]-1)
        bot_top = np.clip([bot, top], 0, self.shape()[1]-1)

        # Create grid of all chunk positions between top-left and bottom-right
        x = np.arange(left_right[0], left_right[1] + 1)
        y = np.arange(bot_top[0], bot_top[1] + 1)
        x_axis, y_axis = np.meshgrid(x, y)

        # Convert to linear indices (x * h + y)
        return x_axis.flatten() * self.shape()[1] + y_axis.flatten()

    def get_next_update_chunk(self, viewport: np.ndarray) -> Optional[int]:
        """
        Calculates the chunk index of the next chunk to draw.
        
        :param viewport: Numpy array of shape (2, 2) with the viewport coordinates in world coordinates.
        Accessing viewport[0] gives the left top corner of the viewport in world coordinates. Accessing viewport[1]
        gives the right bottom corner of the viewport in world coordinates.
        """
        update_chunk = self._get_next_update_chunk_impl(viewport)
        if update_chunk is not None:
            return update_chunk
        else:
            width = abs(viewport[1, 0] - viewport[0, 0])
            height = abs(viewport[1, 1] - viewport[0, 1])
            viewport_extension = 1.0
            extended_viewport = np.array([
                [viewport[0, 0] - width * viewport_extension, viewport[0, 1] + height * viewport_extension],
                [viewport[1, 0] + width * viewport_extension, viewport[1, 1] - height * viewport_extension]
            ])
            return self._get_next_update_chunk_impl(extended_viewport)

    def _get_next_update_chunk_impl(self, viewport: np.ndarray) -> Optional[int]:
        """
        Calculates the chunk index of the next chunk to draw.

        :param viewport: Numpy array of shape (2, 2) with the viewport coordinates in world coordinates.
        Accessing viewport[0] gives the top left corner of the viewport in world coordinates. Accessing viewport[1]
        gives the bottom right corner of the viewport in world coordinates.
        """
        chunk_indices = self.get_in_viewport_chunk_indices(viewport)
        chunk_status = self.status.flat[chunk_indices]
        most_needed_index = np.argmin(chunk_status)
        if chunk_status[most_needed_index] == 3:
            return None
        return int(chunk_indices[most_needed_index])

    def set_status(self, chunk_index: int, status: int):
        self.status[self.chunk_index_tuple(chunk_index)] = status

    def chunk_index_tuple(self, chunk_index: int) -> Tuple[int, int]:
        s = self.shape()
        return chunk_index // s[1], chunk_index % s[1]

    def chunk_frame_size(self, chunk_index: int) -> Tuple[float, float]:
        frame = self.get_chunk_frame(self.chunk_index_tuple(chunk_index))
        return abs(float(frame[2] - frame[0])), abs(float(frame[3] - frame[1]))

    def get_chunk_point_indices(self, chunk_index_tuple: Tuple[int, int]) -> np.ndarray:
        chunk_x, chunk_y = chunk_index_tuple
        if self.chunk_point_indices[chunk_index_tuple] is None:
            chunk_index: int = chunk_index_tuple[0] * self.shape()[1] + chunk_index_tuple[1]
            cur_chunk = np.nonzero(np.equal(self.point_chunk_indices, chunk_index))[0]
            self.chunk_point_indices[chunk_x, chunk_y] = cur_chunk
        return self.chunk_point_indices[chunk_index_tuple]

    def get_chunk_frame(self, chunk_index_tuple: Tuple[int, int]) -> np.ndarray:
        frame = self.chunk_frames[chunk_index_tuple]
        if frame[0] < 0.5:
            point_indices = self.get_chunk_point_indices(chunk_index_tuple)
            if point_indices.shape[0] != 0:
                point_positions = self.points[point_indices]
                point_sizes = self.sizes[point_indices].reshape(-1, 1)

                left_bot = np.min(point_positions - point_sizes, axis=0)
                right_top = np.max(point_positions + point_sizes, axis=0)
                self.chunk_frames[chunk_index_tuple] = (1.0, left_bot[0], right_top[1], right_top[0], left_bot[1])
        return self.chunk_frames[chunk_index_tuple][1:]

    def invalidate_chunks(self):
        shape = self.shape()
        self.surfaces = np.full(shape, None, dtype=object)  # numpy array of pg.Surface
        self.status = np.zeros(shape, dtype=np.int32)

    def get_surface(self, chunk_index_tuple: Tuple[int, int]) -> Optional[pg.Surface]:
        # noinspection PyTypeChecker
        return self.surfaces[chunk_index_tuple]

    def resize_chunks(self, zoom_factor: float, viewport: np.ndarray, point_sizes: np.ndarray):
        self.status[:] = 1  # everything has to be rescaled
        self.chunk_frames[:, :, 0] = 0.0  # frames have to be recalculated
        self.sizes = point_sizes
        for chunk_index in self.get_in_viewport_chunk_indices(viewport):
            chunk_index = self.chunk_index_tuple(chunk_index)
            self.resize_chunk(chunk_index, zoom_factor)

    def resize_chunk(self, chunk_index_tuple: Tuple[int, int], zoom_factor: float):
        chunk_x, chunk_y = chunk_index_tuple
        _frame, render_size = self._get_render_frame_size(chunk_index_tuple, zoom_factor)
        # don't render chunks with too many pixels
        if np.prod(render_size) > 4000 ** 2:
            return
        current_surface = self.get_surface((chunk_x, chunk_y))
        # we can't scale if the surface has not been rendered yet
        if current_surface is None:
            return
        new_surface = pg.transform.scale(current_surface, render_size)
        self.surfaces[chunk_x, chunk_y] = new_surface
        self.status[chunk_x, chunk_y] = 2

    def render_chunk(
            self, chunk_index: int, points: np.ndarray, sizes: np.ndarray, surf_params: np.ndarray,
            zoom_factor: float, point_surfaces: Dict[bytes, pg.Surface]
    ):
        """
        Creates a surface for the given chunk
        :param chunk_index:
        """
        chunk_index = self.chunk_index_tuple(chunk_index)

        frame, render_size = self._get_render_frame_size(chunk_index, zoom_factor)
        # don't render chunks with too many pixels
        if np.prod(render_size) > 4000 ** 2:
            return
        surface = pg.Surface(render_size, pg.SRCALPHA)

        point_indices = self.chunk_point_indices[chunk_index]
        points = points[point_indices]
        sizes = sizes[point_indices]
        surf_params = surf_params[point_indices]

        left_bot = np.array([frame[0], frame[3]])
        render_positions = points - left_bot.reshape(1, 2)
        render_positions[:, 0] -= sizes
        render_positions[:, 1] += sizes
        render_positions *= zoom_factor
        render_positions[:, 1] = render_size[1] - render_positions[:, 1]  # flip y-axis
        render_positions = render_positions.round().astype(int)

        for pos, surf_params in zip(render_positions, surf_params):
            point_surface = point_surfaces[surf_params.tobytes()]
            surface.blit(point_surface, pos)

        self.status[chunk_index] = 3
        self.surfaces[chunk_index] = surface

    def get_pixel_approx(self, zoom_factor) -> int:
        return int(self.chunk_size * zoom_factor)

    def _get_render_frame_size(self, chunk_index, zoom_factor):
        frame = self.get_chunk_frame(chunk_index)
        frame_size = abs(float(frame[2] - frame[0])), abs(float(frame[3] - frame[1]))
        render_size = tuple(int(round(s * zoom_factor)) for s in frame_size)
        return frame, render_size
