import pygame as pg
import sys


# TODO: make surface class

class Window:
    instance = None

    def __init__(self, width, height, caption=None):
        self.instance = self
        pg.init()

        self.width = width
        self.height = height
        self.screen = pg.display.set_mode((width, height))

        self.clock = pg.time.Clock()

        self.caption = 'Pioneer Window' if caption is None else caption
        pg.display.set_caption(self.caption)

        self._mouse = ['left', 'middle', 'right']

        self.left = 0
        self.right = width
        self.top = 0
        self.bottom = height

        self.bg_color = [0, 0, 0]  # the current background color required for other widgets that get the window color

        self.__close = False
        self.__mouse_scroll_y = 0

    def get_fps(self) -> float:
        return self.clock.get_fps()

    def fill(self, color: pg.Color | tuple[int, int, int] | str | int) -> None:
        self.bg_color = pg.Color(color)
        self.screen.fill(color)

    def update(self, FPS: int = 60) -> int:
        self.__mouse_scroll_y = 0
        for e in pg.event.get():
            if e.type == pg.QUIT or self.__close:
                sys.exit()
            if e.type == pg.MOUSEWHEEL:
                self.__mouse_scroll_y = e.y

        pg.display.flip()
        return self.clock.tick(FPS)

    def draw_rect(self, color: str | tuple[int, int, int] | tuple[int, int, int] | pg.Color,
                  rect: tuple[int, int, int, int] | pg.Rect | pg.rect.RectType, width: int = 0) -> None:
        pg.draw.rect(self.screen, color, rect, width)

    def draw_circle(self, color: str | tuple[int, int, int] | tuple[int, int, int] | pg.Color,
                    center: tuple[int, int], radius: int, width: int = 0) -> None:
        pg.draw.circle(self.screen, color, center, radius, width)

    def draw_line(self, color: str | tuple[int, int, int] | tuple[int, int, int] | pg.Color,
                  start_pos=tuple[float, float], end_pos=tuple[float, float], width: int = 1) -> None:
        pg.draw.line(self.screen, color, start_pos, end_pos, width)

    def get_mouse_button(self, button: str = 'left') -> bool:
        return pg.mouse.get_pressed()[self._mouse.index(button)]

    def get_scroll(self) -> int:
        """Returns scroll delta"""
        return self.__mouse_scroll_y

    @staticmethod
    def mouse_position() -> pg.Vector2:
        return pg.Vector2(pg.mouse.get_pos())

    @staticmethod
    def get_key(key: str) -> bool:
        return pg.key.get_pressed()[pg.key.key_code(key)]  # Example: Check if space key is pressed

    # TODO: shortcuts/multiple key press
    def close(self) -> None:
        self.__close = True

    @staticmethod
    def set_caption(text) -> None:
        pg.display.set_caption(str(text))

    @property
    def center(self) -> tuple[int, int]:
        return self.width // 2, self.height // 2
