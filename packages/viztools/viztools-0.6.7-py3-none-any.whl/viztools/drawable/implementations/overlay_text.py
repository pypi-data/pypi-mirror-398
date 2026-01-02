import os

import pygame as pg
import numpy as np

from viztools.coordinate_system import CoordinateSystem
from viztools.drawable.base_drawable import Drawable
from viztools.utils import RenderContext


class OverlayText(Drawable):
    def __init__(
            self,
            text: str,
            position: np.ndarray,
            font_name: str = '',
            font_size: int | float = 16,
            color: np.ndarray | None = None,
            background_color: np.ndarray | None = None,
            border_color: np.ndarray | None = None,
            border_width: int = 2,
            visible: bool = True,
    ):
        """
        Creates an overlay text.

        :param text: The text content to be displayed on the overlay.
        :param position: The position of the overlay in the form of a NumPy array [x, y] or an OverlayPosition object.
            If absolute_position, this is interpreted as absolute coordinates in the screen. Otherwise, it is
            interpreted as center point of the text in the coordinate system. If an OverlayPosition object is provided,
            it is always interpreted as absolute coordinates.
        :param font_name: The font name to use for rendering the text. If not provided, defaults to a system font.
        :param font_size: The size of the font. If an integer is provided, it is interpreted as pixels. If a float is
            provided, it is interpreted as size in world coordinates.
        :param color: The color of the text as a NumPy array. If None, defaults to white. Does not support alpha.
        :param background_color: The background color of the text overlay as a NumPy array.
            If None, no background will be rendered.
        :param border_color: The color of the border around the text as a NumPy array. If
            None, no border will be rendered.
        :param border_width: The width of the border around the text, in pixels.
        :param visible: Whether the overlay is visible.
        """
        super().__init__(visible)
        self.text = text
        self.position = position
        if font_name:
            if not os.path.isfile(font_name):
                font_name = pg.font.match_font(font_name)
        else:
            font_name = pg.font.get_default_font()
        self.font_name = font_name
        self.font_size = font_size
        self.color = color if color is not None else np.array([255, 255, 255], dtype=np.uint8)
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width

    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext):
        text_lines = self.text.split('\n')
        font_size = self.font_size
        if isinstance(font_size, float):
            font_size = int(self.font_size * coordinate_system.zoom_factor)
        if font_size > 4000:
            return
        font = pg.font.Font(self.font_name, font_size)
        line_dimensions = [font.size(line) for line in text_lines]
        total_height = sum(d[1] for d in line_dimensions)
        max_width = max(d[0] for d in line_dimensions)

        combined_rect = pg.Rect(0, 0, max_width, total_height)
        padding = self.border_width * 2 if self.border_color is not None else 0

        pos = coordinate_system.space_to_screen(self.position.reshape(2, 1)).reshape(2)
        combined_rect.center = (int(pos[0]), int(pos[1]))

        # Add padding for border
        combined_rect.width += padding
        combined_rect.height += padding

        # skip if out of screen
        if not combined_rect.colliderect(screen.get_rect()):
            return

        if self.background_color is not None:
            background = pg.Surface(combined_rect.size, pg.SRCALPHA)
            background.fill(self.background_color)
            screen.blit(background, combined_rect)

        if self.border_color is not None:
            border_surface = pg.Surface(screen.get_size(), pg.SRCALPHA)
            pg.draw.rect(border_surface, self.border_color, combined_rect, self.border_width)
            screen.blit(border_surface, (0, 0))

        current_y = combined_rect.y + (padding // 2)
        line_surfaces = [font.render(line, True, self.color) for line in text_lines]
        for surface in line_surfaces:
            line_rect = surface.get_rect()
            line_rect.centerx = combined_rect.centerx
            line_rect.y = current_y
            screen.blit(surface, line_rect)
            current_y += line_rect.height

    def handle_event(
            self, event: pg.event.Event, screen: pg.Surface, coordinate_system: CoordinateSystem,
            render_context: RenderContext
    ):
        pass

    def update(
            self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext
    ):
        pass
