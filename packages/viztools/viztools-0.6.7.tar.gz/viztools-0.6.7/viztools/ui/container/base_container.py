from typing import Iterable, Optional, List

import pygame as pg

from ..elements.base_element import UIElement
from viztools.utils import RenderContext


class UIContainer:
    def __init__(self, visible: bool = True):
        self.visible = visible
        self._element_cache: Optional[List[UIElement]] = None

    def iter_elements(self) -> Iterable[UIElement]:
        """
        Iter over all elements in the container.
        :return: Iterable of BaseElement objects.
        """
        if self._element_cache is None:
            self._element_cache = [elem for elem in self.__dict__.values() if isinstance(elem, UIElement)]

        yield from self._element_cache

    def handle_events(self, events: List[pg.event.Event], render_context: RenderContext):
        if self.visible:
            for elem in self.iter_elements():
                elem.handle_events(events, render_context)

    def render(self, screen: pg.Surface, render_context: RenderContext):
        if self.visible:
            for element in self.iter_elements():
                element.render(screen, render_context)
