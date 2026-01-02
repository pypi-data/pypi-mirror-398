from typing import Union, Container

import numpy as np
import pygame as pg

from viztools.coordinate_system import CoordinateSystem


class CoordinateSystemController:
    def __init__(self, coordinate_system: CoordinateSystem, drag_mouse_button: Union[int, Container[int]] = 2):
        self.coordinate_system = coordinate_system
        self.dragging: bool = False
        self.mouse_position = np.zeros(2, dtype=int)
        if isinstance(drag_mouse_button, int):
            drag_mouse_button = (drag_mouse_button,)
        self.drag_mouse_button = drag_mouse_button

    def handle_event(self, event: pg.event.Event) -> bool:
        """

        :param event:
        :return:
        """
        render_needed = False
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button in self.drag_mouse_button:
                self.dragging = True
                render_needed = True
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button in self.drag_mouse_button:
                self.dragging = False
                render_needed = True
        elif event.type == pg.MOUSEMOTION:
            self.mouse_position = np.array(event.pos, dtype=np.int32)
            if self.dragging:
                self.coordinate_system.translate(np.array(event.rel, dtype=np.int32))
                render_needed = True
        elif event.type == pg.MOUSEWHEEL:
            if event.y < 0:
                self.coordinate_system.zoom_out(focus_point=self.mouse_position)
                render_needed = True
            else:
                self.coordinate_system.zoom_in(focus_point=self.mouse_position)
                render_needed = True
        return render_needed
