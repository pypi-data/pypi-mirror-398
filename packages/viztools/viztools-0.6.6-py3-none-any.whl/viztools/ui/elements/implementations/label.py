from typing import Optional

import pygame as pg

from ..base_element import UIElement
from viztools.utils import RenderContext, Color, Align


class Label(UIElement):
    def __init__(
            self, rect: pg.Rect, text: str, text_color: Color = (200, 200, 200),
            bg_color: Optional[Color] = None, align: Align = Align.CENTER,
            font_name: Optional[str] = None, font_size: int = -1,
    ):
        super().__init__(rect)
        self._text = text
        self.text_color = text_color
        self.bg_color = bg_color
        self._text_surface: Optional[pg.Surface] = None
        self.align: Align = align

        self.font_name = font_name
        self.font_size = font_size

    def handle_event(self, event: pg.event.Event, render_context: RenderContext):
        super().handle_event(event, render_context)

    def set_text(self, text: str):
        self._text = text
        self._text_surface = None

    def draw(self, screen: pg.Surface, render_context: RenderContext):
        if self.bg_color:
            pg.draw.rect(screen, self.bg_color, self.rect)

        if self._text:
            if self._text_surface is None:
                font = render_context.get_font(self.font_name, self.font_size)
                self._text_surface = font.render(self._text, True, self.text_color)
            rect = self.align.arrange_in_rect(self._text_surface.get_rect(), self.rect)
            screen.blit(self._text_surface, rect)

    def update(self, render_context: RenderContext):
        pass
