# import pygame as pg
# from .window import Window
# from .label import Label
#
#
# class Ruler:
#     def __init__(self, window: Window,
#                  start: pg.Vector2 | tuple[int, int] | list[int, int],
#                  end: pg.Vector2 | tuple[int, int] | list[int, int],
#                  color: str | pg.Color | tuple[int, int, int] = '',
#                  width: int = 3, font: str = ''):
#         self.window = window  # main window
#         self.start = pg.Vector2(start)  # firts point
#         self.end = pg.Vector2(end)  # second point
#
#         self._bg_color = [0, 0, 0, 0]
#         self.color = color if color != '' else list(map(lambda c: ~c & 0xFF, self.window.bg_color[:3]))
#         # if color is not defined, then it will be the negative of the background color.
#         # a ~color & 0xFF are made for each element except alfa chanel
#
#         self.width = width
#
#         self.length = int(self.start.distance_to(self.end))
#         self._diff = self.end - self.start
#
#         x, y = self.start + self._diff // 2
#         self.label = Label(window, x, y, f'{self.length}px', self.color, font=font)
#
#     def draw(self):
#         if self.window.bg_color != self._bg_color:
#             self._bg_color = self.window.bg_color
#             self.color = list(map(lambda c: ~c & 0xFF, self._bg_color[:3]))
#             self.label.set_color(self.color)
#
#         pg.draw.aaline(self.window.screen, self.color, self.start, self.end, self.width)
#
#         self.length = self.start.distance_to(self.end)
#         dir = (self.end - self.start * 1.00001)
#
#         self.label.x = self.start.x + dir.x // 2 #- self.label.width * dir.y / abs(dir.y)
#         self.label.y = self.start.y + dir.y // 2 + self.label.height * dir.x / abs(dir.x)
#         self.label.set_text(f'{self.length:.0f}px')
#         self.label.draw()
