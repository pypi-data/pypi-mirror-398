import enum
import warnings
from typing import Union, Tuple, Optional, Dict

import pygame as pg
import numpy as np

DEFAULT_FONT_SIZE = 16


def to_np_array(p):
    if isinstance(p, np.ndarray):
        return p
    return np.array(p)


Color = Union[np.ndarray, Tuple[int, int, int, int], Tuple[int, int, int]]


def normalize_color(color: Color) -> np.ndarray:
    if len(color) == 3:
        return np.array([*color, 255], dtype=np.float32)
    if len(color) != 4:
        raise ValueError(f'color must be of length 3 or 4, not {len(color)}.')
    return np.array(color, dtype=np.float32)


class RenderContext:
    def __init__(self, default_font_name: Optional[str] = None, default_font_size: int = DEFAULT_FONT_SIZE):
        if default_font_name is None:
            default_font_name = pg.font.get_default_font()
        self.default_font_name = default_font_name
        self.default_font_size = default_font_size
        self.font_cache: Dict[Tuple[str, int], pg.font.Font] = {}
        self.mouse_pressed = False

    def get_font(self, font_name: Optional[str] = None, font_size: int = -1) -> pg.font.Font:
        if font_name is None:
            font_name = self.default_font_name
        if font_size == -1:
            font_size = self.default_font_size

        key = (font_name, font_size)

        if key not in self.font_cache:
            self.font_cache[key] = pg.font.Font(font_name, font_size)
        return self.font_cache[key]


class Align(enum.StrEnum):
    CENTER = 'center'
    LEFT = 'left'
    RIGHT = 'right'
    TOP = 'top'
    BOTTOM = 'bottom'
    TOP_LEFT = 'top_left'
    TOP_RIGHT = 'top_right'
    BOTTOM_LEFT = 'bottom_left'
    BOTTOM_RIGHT = 'bottom_right'

    def set_rect(self, rect: pg.Rect, position: Tuple[int, int]):
        if self == Align.CENTER:
            rect.center = position
        elif self == Align.LEFT:
            rect.midleft = position
        elif self == Align.RIGHT:
            rect.midright = position
        elif self == Align.TOP:
            rect.midtop = position
        elif self == Align.BOTTOM:
            rect.midbottom = position
        elif self == Align.TOP_LEFT:
            rect.topleft = position
        elif self == Align.TOP_RIGHT:
            rect.topright = position
        elif self == Align.BOTTOM_LEFT:
            rect.bottomleft = position
        elif self == Align.BOTTOM_RIGHT:
            rect.bottomright = position
        else:
            raise ValueError(f'unknown anker type: {self}')

    def get_pos(self, rect: pg.Rect) -> Tuple[int, int]:
        if self == Align.CENTER:
            return rect.center
        elif self == Align.LEFT:
            return rect.midleft
        elif self == Align.RIGHT:
            return rect.midright
        elif self == Align.TOP:
            return rect.midtop
        elif self == Align.BOTTOM:
            return rect.midbottom
        elif self == Align.TOP_LEFT:
            return rect.topleft
        elif self == Align.TOP_RIGHT:
            return rect.topright
        elif self == Align.BOTTOM_LEFT:
            return rect.bottomleft
        elif self == Align.BOTTOM_RIGHT:
            return rect.bottomright
        else:
            raise ValueError(f'unknown anker type: {self}')

    def arrange_by_anker(self, rect: pg.Rect, anker: Union[np.ndarray, Tuple[int, int]]) -> pg.Rect:
        new_rect = rect.copy()
        self.set_rect(new_rect, anker)
        return new_rect

    def arrange_in_rect(self, rect: pg.Rect, container: pg.Rect) -> pg.Rect:
        new_rect = rect.copy()
        self.set_rect(new_rect, self.get_pos(container))
        return new_rect


def load_font(font_name: Optional[str] = None, font_size: int = DEFAULT_FONT_SIZE) -> pg.font.Font:
    """
    Helper function to load the default font.
    :return: The font to use
    """
    try:
        font = pg.font.Font(font_name, font_size)
    except pg.error:
        warnings.warn("Warning: Could not load font. Falling back to default font.")
        font = pg.font.Font(None, font_size)
    return font


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)
