from abc import ABC, abstractmethod
from typing import List, final

import pygame as pg

from viztools.coordinate_system import CoordinateSystem
from viztools.utils import RenderContext


class Drawable(ABC):
    def __init__(self, visible: bool = True):
        self.visible = visible

    @final
    def handle_events(
            self, events: List[pg.event.Event], screen: pg.Surface, coordinate_system: CoordinateSystem,
            render_context: RenderContext
    ):
        """
        Handles the given events and updates the element, if needed.

        :param events: The events to handle.
        :param screen: The screen that will be used for drawing.
        :param coordinate_system: The coordinate system, this drawable is rendered in.
        """
        if self.visible:
            for event in events:
                self.handle_event(event, screen, coordinate_system, render_context)
            self.update(screen, coordinate_system, render_context)

    @abstractmethod
    def handle_event(
            self, event: pg.event.Event, screen: pg.Surface, coordinate_system: CoordinateSystem,
            render_context: RenderContext
    ):
        """
        Handles the given events and updates the element.
        :param event: The event to handle.
        :param screen: The screen that will be used for drawing.
        :param coordinate_system: The coordinate system, this drawable is rendered in.
        :param render_context: The render context used for drawing.
        """
        pass

    @abstractmethod
    def update(self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext):
        """
        Updates the element.

        :param screen: The screen that will be used for drawing.
        :param coordinate_system: The coordinate system, this drawable is rendered in.
        """
        pass

    @final
    def render(self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext):
        """
        Draws the element to the screen.

        :param screen: The screen that will be used for drawing.
        :param coordinate_system: The coordinate system, this drawable is rendered in.
        :param render_context: The render context used for drawing.
        """
        if self.visible:
            self.draw(screen, coordinate_system, render_context)
        self.finalize()

    @abstractmethod
    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext):
        """
        Draws the element to the screen.

        :param screen: The screen that will be used for drawing.
        :param coordinate_system: The coordinate system, this drawable is rendered in.
        :param render_context: The render context used for drawing.
        """
        pass

    def finalize(self):
        """
        Finalize this drawable.
        """
        pass
