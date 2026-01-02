from typing import Optional

import pygame as pg

from ..base_element import UIElement
from viztools.utils import RenderContext, Color


class Slider(UIElement):
    def __init__(
            self, rect: pg.Rect, value: float = 0.0, min_val: float = 0.0, max_val: float = 100.0,
            cursor_color: Color = (220, 220, 220), bg_color: Color = (30, 30, 30), hover_color: Color = (45, 45, 45),
            clicked_color: Color = (60, 60, 60), border_color: Color = (100, 100, 100),
    ):
        super().__init__(rect)

        self.value = value
        self.min_val = min_val
        self.max_val = max_val

        self.cursor_color = cursor_color
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.clicked_color = clicked_color
        self.border_color = border_color
        self.border_width = 2

        self.controlled = False
        self.has_changed = False

    def handle_event(self, event: pg.event.Event, render_context: RenderContext):
        super().handle_event(event, render_context)

        start_value = self.value

        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.controlled = True
                # Update value based on click position
                relative_x = event.pos[0] - self.rect.x
                self.value = self.min_val + (relative_x / self.rect.width) * (self.max_val - self.min_val)
                self.value = max(self.min_val, min(self.max_val, self.value))

        if event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.controlled = False

        if event.type == pg.MOUSEMOTION:
            if self.controlled:
                # Update value based on drag position
                relative_x = event.pos[0] - self.rect.x
                self.value = self.min_val + (relative_x / self.rect.width) * (self.max_val - self.min_val)
                self.value = max(self.min_val, min(self.max_val, self.value))

        if self.value != start_value:
            self.has_changed = True

    def draw(self, screen: pg.Surface, render_context: RenderContext):
        # Determine background color based on state
        if self.controlled:
            bg_color = self.clicked_color
        elif self.is_hovered:
            bg_color = self.hover_color
        else:
            bg_color = self.bg_color

        # Draw background
        pg.draw.rect(screen, bg_color, self.rect)

        # Draw border
        pg.draw.rect(screen, self.border_color, self.rect, self.border_width)

        # Calculate cursor position
        value_ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        cursor_x = self.rect.x + int(value_ratio * self.rect.width)
        cursor_width = 8
        cursor_rect = pg.Rect(
            cursor_x - cursor_width // 2,
            self.rect.y,
            cursor_width,
            self.rect.height
        )

        # Draw cursor
        pg.draw.rect(screen, self.cursor_color, cursor_rect)

    def update(self, render_context: RenderContext):
        pass

    def finalize(self):
        self.has_changed = False
