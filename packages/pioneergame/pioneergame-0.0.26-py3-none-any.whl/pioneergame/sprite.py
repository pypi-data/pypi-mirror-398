import pygame as pg
from pkg_resources import resource_filename
from .window import Window
from .rect import Rect
from os.path import exists


class Sprite:
    def __init__(self, window: Window, image_path: str = '', size: tuple[int, int] = None):
        self.window = window
        self.image_path = image_path

        if image_path and exists(image_path):
            self.image = pg.image.load(image_path)
        else:
            self.image = pg.image.load(resource_filename('pioneergame', 'missing_texture.png'))
            # TODO: make non-stretchable pattern

        if size:
            self.image = pg.transform.scale(self.image, size)

        self.attached_to = Rect(window, 0, 0, 0, 0)

    @property
    def size(self) -> tuple[int, int]:
        return self.image.get_size()

    # TODO: make setter
    def set_size(self, size: tuple[int, int] | list[int, int]) -> None:
        self.image = pg.transform.scale(self.image, size)

    def attach_to(self, rect: Rect, resize=True) -> None:
        self.attached_to = rect
        if resize:
            self.set_size(rect.size)

    def draw(self) -> None:
        self.window.screen.blit(self.image, self.attached_to.pos)

    def rotate(self, angle: int) -> None:
        self.image = pg.transform.rotate(self.image, angle)

    def get_rotated(self, angle: int) -> 'Sprite':
        rotated = Sprite(self.window, self.image_path, self.size)
        rotated.rotate(angle)
        return rotated
