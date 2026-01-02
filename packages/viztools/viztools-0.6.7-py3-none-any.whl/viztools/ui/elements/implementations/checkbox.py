from typing import Optional

import pygame as pg

from ..base_element import UIElement
from viztools.utils import RenderContext, Color


class CheckBox(UIElement):
    def __init__(
            self, rect: pg.Rect, checked: bool = False, bg_color: Color = (20, 20, 20),
            hover_color: Color = (30, 30, 30), border_color: Color = (100, 100, 100),
    ):
        super().__init__(rect)
        self.checked = checked
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.border_color = border_color
        self.border_width = 2
        self.hovered = False

    def handle_event(self, event: pg.event.Event, render_context: RenderContext):
        super().handle_event(event, render_context)
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked

    def draw(self, screen: pg.Surface, render_context: RenderContext):
        # Draw background
        current_bg_color = self.hover_color if self.hovered else self.bg_color
        pg.draw.rect(screen, current_bg_color, self.rect)

        # Draw border
        pg.draw.rect(screen, self.border_color, self.rect, self.border_width)

        # Draw checkmark if checked
        if self.checked:
            padding = self.rect.width // 4
            start_pos = (self.rect.left + padding, self.rect.centery)
            middle_pos = (self.rect.centerx - padding // 2, self.rect.bottom - padding)
            end_pos = (self.rect.right - padding, self.rect.top + padding)

            pg.draw.line(screen, (200, 200, 200), start_pos, middle_pos, 3)
            pg.draw.line(screen, (200, 200, 200), middle_pos, end_pos, 3)

    def update(self, render_context: RenderContext):
        mouse_pos = pg.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)
