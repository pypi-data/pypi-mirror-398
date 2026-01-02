from abc import ABC
from typing import Tuple, Optional, List, Union, Iterable

import numpy as np
import pygame as pg

from viztools.ui.container.base_container import UIContainer
from viztools.ui.elements.base_element import UIElement
from viztools.utils import RenderContext, DEFAULT_FONT_SIZE, Color


class UIViewer(ABC):
    def __init__(
            self, screen_size: Optional[Tuple[int, int]] = None, title: str = "Visualization", framerate: float = 60.0,
            default_font_name: Optional[str] = None, default_font_size: int = DEFAULT_FONT_SIZE,
            background_color: Color = (20, 20, 20)
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

        self.render_context = RenderContext(default_font_name, default_font_size)
        self.background_color = background_color

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

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.framerate)
        pg.quit()

    def render_ui(self):
        self.render_ui_elements(self.iter_ui_elements())

    def render_ui_elements(self, ui_elements: Iterable[Union[UIElement, UIContainer]]):
        for ui_element in ui_elements:
            ui_element.render(self.screen, self.render_context)

    def render(self):
        self.screen.fill(self.background_color)
        self.render_ui()
        pg.display.flip()

    def handle_events(self):
        events = pg.event.get()
        for event in events:
            self.handle_event(event)
        for ui_element in self.iter_ui_elements():
            ui_element.handle_events(events, self.render_context)

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEMOTION:
            self.mouse_pos = np.array(event.pos)
        if event.type == pg.QUIT:
            self.running = False

    def update(self):
        pass
