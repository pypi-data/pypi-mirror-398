import io
from pathlib import Path
from typing import Union, Optional, Tuple

import numpy as np
import pygame as pg
from PIL import Image as PilImage
from PIL.Image import Transpose

from viztools.coordinate_system import CoordinateSystem
from viztools.drawable.base_drawable import Drawable
from viztools.utils import RenderContext, Align


class Image(Drawable):
    def __init__(
            self, image: Union[np.ndarray, PilImage.Image, str, Path], position: np.ndarray,
            size: Union[np.ndarray, float] = 0.01, align: Align = Align.CENTER,
            offset: Optional[np.ndarray] = None, offset_color: Optional[np.ndarray] = None, visible: bool = True
    ):
        """
        Initializes a list of lines.

        :param image: Numpy array of shape [h, w, 3] or pillow image.
        :param position: The position of the image as a numpy array of shape [2].
        :param size: The size of the image as a numpy array or tuple (height, width) in world coordinates,
            or it can be defined as a scale factor to original size.
        :param align: The type of anker to use.
        :param offset: The offset of the image as a numpy array of shape [2].
        :param offset_color: The color of the offset as a numpy array of shape [3] or [4] (with alpha).
        :param visible: Whether the image is visible.
        """
        super().__init__(visible)

        image = to_pil_image(image)
        image = fix_image_axis_swap(image)
        self.image_data: bytes = encode_image(image)
        self.image_surface: Optional[pg.Surface] = None
        self.position = position
        self.align = align
        if isinstance(size, float):
            size = np.array(get_image_size(image)) * size
        elif isinstance(size, (tuple, np.ndarray)):
            size = np.asarray(size)
        else:
            raise TypeError(f'size must be a float, tuple or numpy array, not {type(size)}.')
        self.size = size
        self.last_size = None
        self.scaled_surface = None
        self.offset = offset
        self.offset_color = offset_color

    def _ensure_image_surface(self):
        if self.image_surface is None:
            self.image_surface = bytes_to_surf_array(self.image_data)

    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext):
        anchor_point = coordinate_system.space_to_screen_t(self.position).flatten().astype(int)
        pos = self.position + self.offset if self.offset is not None else self.position
        screen_points = coordinate_system.space_to_screen_t(pos).flatten().astype(int)
        size = np.abs(coordinate_system.space_to_screen_t(self.size, translate=False).flatten().astype(int))

        # get target rect
        target_rect = pg.Rect(0, 0, size[1], size[0])
        target_rect = self.align.arrange_by_anker(target_rect, screen_points)

        if target_rect.colliderect(screen.get_rect()) and np.prod(target_rect.size) < 30000000:
            self._ensure_image_surface()
            if self.last_size is None or np.any(size != self.last_size):
                self.scaled_surface = pg.transform.scale(self.image_surface, (size[1], size[0]))
                self.last_size = size

            if self.offset_color is not None:
                pg.draw.line(screen, self.offset_color, anchor_point, screen_points, 2)
            screen.blit(self.scaled_surface, target_rect)
        else:
            # remove unused data
            self.last_size = None
            self.scaled_surface = None
            self.image_surface = None

    def handle_event(
            self, event: pg.event.Event, screen: pg.Surface, coordinate_system: CoordinateSystem,
            render_context: RenderContext
    ):
        pass

    def update(
            self, screen: pg.Surface, coordinate_system: CoordinateSystem, render_context: RenderContext
    ):
        pass


def fix_image_axis_swap(image: Union[np.ndarray, PilImage.Image]) -> Union[np.ndarray, PilImage.Image]:
    """
    Swapes axis for the given image.
    :param image: The image to swap.
    :return: The image with swapped axes.
    """
    if isinstance(image, np.ndarray):
        return image.swapaxes(0, 1)
    elif isinstance(image, PilImage.Image):
        return image.transpose(Transpose.TRANSPOSE)
    else:
        raise TypeError(f'image must be of type np.ndarray or PIL.Image, not {type(image)}.')


def get_image_size(image: PilImage.Image) -> Tuple[int, int]:
    """
    Returns the size of the image in pixels as [height, width].

    :param image: The image to get the size of.
    :return: The size of the image in pixels as [height, width].
    """
    if isinstance(image, PilImage.Image):
        return image.size
    else:
        raise TypeError(f'image must be of type np.ndarray or PIL.Image, not {type(image)}.')


def to_pil_image(image: Union[np.ndarray, PilImage.Image, str, Path]) -> PilImage.Image:
    """
    Convert to pillow image. Accepts numpy array, path to image or pillow image.

    :param image: The image to convert.
    :return: A pillow image.
    """
    if isinstance(image, (str, Path)):
        return PilImage.open(image)
    elif isinstance(image, PilImage.Image):
        return image
    elif isinstance(image, np.ndarray):
        return PilImage.fromarray(image)
    else:
        raise TypeError(f'image must be of type str, Path or np.ndarray, not {type(image)}.')


def encode_image(image: PilImage.Image) -> bytes:
    """
    Encode data into bytes (jpg) for small memory footprint.

    :param image: The image to encode.
    :return: The jpg encoded image as bytes.
    """
    with io.BytesIO() as bytes_stream:
        image.save(bytes_stream, format="JPEG")
        return bytes_stream.getvalue()


def bytes_to_surf_array(data: bytes) -> pg.Surface:
    return pil_to_surf_array(decode_image(data))


def decode_image(data: bytes) -> PilImage.Image:
    return PilImage.open(io.BytesIO(data))


def pil_to_surf_array(pil_img: PilImage.Image) -> pg.Surface:
    """
    Converts a PIL Image to a Pygame Surface using surf_array.
    """
    pil_img = pil_img.convert('RGB')
    image_array = np.asarray(pil_img, dtype=np.uint8)
    pygame_surface = pg.surfarray.make_surface(image_array)
    return pygame_surface.convert()
