from pkg_resources import resource_filename
import pygame as pg
from .rect import Rect
from .window import Window


# TODO: textbox/multiple line label
class Label:
    def __init__(self, window: Window, x, y, text: str = 'Sample Text',
                 color: str | pg.Color | tuple[int, int, int] = 'purple',
                 size: int = 25, font: str = "", italic: bool = False):
        self.window = window
        self.x = x
        self.y = y
        self.color = color
        self.text = text
        if not font:
            self.font = pg.font.Font(resource_filename('pioneergame', 'Fixedsys.ttf'), size)
        else:
            self.font = pg.font.SysFont(font, size, False, italic)

        self._text_surface = self.font.render(self.text, True, self.color)

    def set_color(self, color: str | pg.Color | list[int, int, int] | tuple[int, int, int]) -> None:
        self.color = pg.Color(color)
        self._text_surface = self.font.render(self.text, True, color)

    def set_text(self, new_text: str | int | float) -> None:
        self.text = str(new_text)
        self._text_surface = self.font.render(self.text, True, self.color)

    def draw(self) -> None:
        self.window.screen.blit(self._text_surface, (self.x, self.y))

    def draw_box(self) -> None:
        pg.draw.rect(self.window.screen, (255, 0, 255), self.get_rect(), 1)

    @property
    def width(self) -> int:
        return self._text_surface.get_width()

    @property
    def height(self) -> int:
        return self._text_surface.get_height()

    @property
    def right(self) -> int:
        return self.x + self._text_surface.get_rect().right

    @property
    def left(self) -> int:
        return self.x + self._text_surface.get_rect().left

    @property
    def top(self) -> int:
        return self.y + self._text_surface.get_rect().top

    @property
    def bottom(self) -> int:
        return self.y + self._text_surface.get_rect().bottom

    def get_rect(self) -> Rect:
        return Rect(self.window, self.x, self.y, self.width, self.height)

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2

    @center.setter
    def center(self, pos: tuple[int, int]) -> None:
        self.x = pos[0] - self.width // 2
        self.y = pos[1] - self.height // 2
