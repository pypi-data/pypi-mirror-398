from abc import ABC
from typing import Tuple, Optional, List, Union, Iterable, Container

import numpy as np
import pygame as pg

from viztools.controller.coordinate_system_controller import CoordinateSystemController
from viztools.coordinate_system import CoordinateSystem, draw_coordinate_system
from viztools.drawable import Drawable
from viztools.ui.container.base_container import UIContainer
from viztools.ui.elements.base_element import UIElement
from viztools.utils import RenderContext, DEFAULT_FONT_SIZE


class Viewer(ABC):
    def __init__(
            self, screen_size: Optional[Tuple[int, int]] = None, title: str = "Visualization", framerate: float = 60.0,
            font_size: int = DEFAULT_FONT_SIZE, drag_mouse_button: Union[int, Container[int]] = (2, 3)
    ):
        pg.init()
        pg.scrap.init()
        pg.key.set_repeat(130, 25)
        mode = pg.RESIZABLE
        if screen_size is None:
            screen_size = (0, 0)
        if screen_size == (0, 0):
            mode = mode | pg.FULLSCREEN
        self.screen = pg.display.set_mode(screen_size, mode)
        pg.display.set_caption(title)

        self.running = True
        self.clock = pg.time.Clock()
        self.framerate = framerate
        self.mouse_pos = np.array(pg.mouse.get_pos(), dtype=np.int32)

        self.coordinate_system = CoordinateSystem(screen_size)
        self.coordinate_system_controller = CoordinateSystemController(
            self.coordinate_system, drag_mouse_button=drag_mouse_button
        )
        self.coordinate_system.center(
            focus_point=np.array([0, 0], dtype=np.float32), screen_size=self.screen.get_size()
        )

        self.render_context = RenderContext.default(font_size)

        self._drawable_cache: Optional[List[Drawable]] = None
        self._ui_element_cache: Optional[List[Union[UIContainer, UIElement]]] = None

    def iter_ui_elements(self) -> Iterable[Union[UIElement, UIContainer]]:
        """
        Iter over all elements in the container.
        :return: Iterable of BaseElement objects.
        """
        if self._ui_element_cache is None:
            self._ui_element_cache = [
                elem for elem in self.__dict__.values() if isinstance(elem, (UIElement, UIContainer))
            ]

        yield from self._ui_element_cache

    def iter_drawables(self) -> Iterable[Drawable]:
        """
        Iter over all elements in the container.
        :return: Iterable of BaseElement objects.
        """
        if self._drawable_cache is None:
            self._drawable_cache = [elem for elem in self.__dict__.values() if isinstance(elem, Drawable)]

        yield from self._drawable_cache

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.framerate)
        pg.quit()

    def render_content(self):
        self.render_drawables(self.iter_drawables())

    def render_ui(self):
        self.render_ui_elements(self.iter_ui_elements())

    def render_drawables(self, drawables: Iterable[Drawable]):
        for drawable in drawables:
            drawable.render(self.screen, self.coordinate_system, self.render_context)

    def render_ui_elements(self, ui_elements: Iterable[Union[UIElement, UIContainer]]):
        for ui_element in ui_elements:
            ui_element.render(self.screen, self.render_context)

    def render_coordinate_system(self, draw_numbers=True):
        draw_coordinate_system(self.screen, self.coordinate_system, self.render_context.font, draw_numbers=draw_numbers)

    def render(self):
        self.render_coordinate_system(draw_numbers=True)
        self.render_content()
        self.render_ui()
        pg.display.flip()

    def handle_events(self):
        events = pg.event.get()
        for event in events:
            self.handle_event(event)
        for ui_element in self.iter_ui_elements():
            ui_element.handle_events(events, self.render_context)
        for drawable in self.iter_drawables():
            drawable.handle_events(events, self.screen, self.coordinate_system, self.render_context)

    def handle_event(self, event: pg.event.Event):
        self.coordinate_system_controller.handle_event(event)
        if event.type == pg.MOUSEMOTION:
            self.mouse_pos = np.array(event.pos)
        if event.type == pg.QUIT:
            self.running = False

    def update(self):
        pass
