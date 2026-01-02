from itertools import pairwise
from typing import Tuple

import numpy as np
import pygame as pg

from viztools.coordinate_system import CoordinateSystem
from viztools.drawable.base_drawable import Drawable
from viztools.utils import RenderContext


class Lines(Drawable):
    def __init__(self, points: np.ndarray, color: np.ndarray = None, visible: bool = True):
        """
        Initializes a list of lines.

        :param points: Numpy array of shape [N, 2] where N is the number of points.
        :param color: The color of the lines as numpy array of shape [3] or [4] (with alpha).
        :param visible: Whether the lines are visible.
        """
        super().__init__(visible)
        self.points = points
        self.color = color

    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext):
        screen_points = coordinate_system.space_to_screen_t(self.points)
        for p1, p2 in pairwise(screen_points):
            pg.draw.line(screen, self.color, p1, p2)

    def clicked_points(
            self, event: pg.event.Event, coordinate_system: CoordinateSystem, max_distance: float = 10.0
    ) -> np.ndarray:
        """
        Returns the indices of the points clicked by the mouse. Returns an empty array if no point was clicked.

        :param event: The event to check.
        :param coordinate_system: The coordinate system to use.
        """
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            return self.hovered_points(np.array(event.pos, dtype=np.int32), coordinate_system, max_distance)
        return np.array([])

    def hovered_points(
            self, mouse_pos: np.ndarray, coordinate_system: CoordinateSystem, max_distance: float = 10.0
    ) -> np.ndarray:
        screen_pos = mouse_pos.reshape(1, 2)
        screen_points = coordinate_system.space_to_screen_t(self.points)
        distances = np.linalg.norm(screen_points - screen_pos, axis=1)
        return np.nonzero(distances < max_distance)[0]

    def closest_point(self, pos: np.ndarray, coordinate_system: CoordinateSystem) -> Tuple[int, float]:
        """
        Finds the closest point to the given position.

        This function calculates the closest point to a specified 2D position on
        the screen.

        :param pos: The 2D position in screen coordinates to calculate the distance from.
        :param coordinate_system: The coordinate system used for transforming space
                                  coordinates to screen coordinates.
        :return: A tuple containing the index of the closest point and the distance
                 to that closest point.
        :rtype: Tuple[int, float]
        """
        screen_pos = pos.reshape(1, 2)
        screen_points = coordinate_system.space_to_screen_t(self.points)
        distances = np.linalg.norm(screen_points - screen_pos, axis=1)
        closest_index = np.argmin(distances)
        return int(closest_index), max(float(distances[closest_index]), 0.0)

    def handle_event(
            self, event: pg.event.Event, screen: pg.Surface, coordinate_system: CoordinateSystem,
            render_context: RenderContext
    ):
        pass

    def update(self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext):
        pass
