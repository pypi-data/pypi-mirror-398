from typing import Optional

import pygame as pg

from ..base_element import UIElement
from viztools.utils import RenderContext, Color


class Button(UIElement):
    def __init__(
            self, rect: pg.Rect, text: str = "",
            bg_color: Color = (180, 180, 180), hover_color: Color = (195, 195, 195),
            clicked_color: Color = (220, 220, 220), border_color: Color = (100, 100, 100),
            text_color: Color = (10, 10, 10)
    ):
        super().__init__(rect)
        self.text = text

        self.bg_color = bg_color
        self.hover_color = hover_color
        self.clicked_color = clicked_color
        self.border_color = border_color
        self.text_color = text_color
        self.border_width = 2

        self.text_surface: Optional[pg.Surface] = None

    def handle_event(self, event: pg.event.Event, render_context: RenderContext):
        super().handle_event(event, render_context)

    def draw(self, screen: pg.Surface, render_context: RenderContext):
        # Draw button background
        if self.is_hovered:
            color = self.clicked_color if pg.mouse.get_pressed()[0] else self.hover_color
        else:
            color = self.bg_color
        pg.draw.rect(screen, color, self.rect)

        # Draw border
        pg.draw.rect(screen, self.border_color, self.rect, self.border_width)

        # Render text
        if self.text:
            if self.text_surface is None:
                self.text_surface = render_context.font.render(self.text, True, self.text_color)
            text_rect = self.text_surface.get_rect(center=self.rect.center)
            screen.blit(self.text_surface, text_rect)

    def set_text(self, text: str):
        self.text = text
        self.text_surface = None

    def update(self, render_context: RenderContext):
        pass
