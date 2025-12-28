import pygame as pg

from . import Window, Rect, Label


class Button:
    def __init__(self, window: Window, x: int, y: int, width: int, height: int,
                 title: str = 'Push button', color: tuple[int, int, int] = (220, 220, 220),
                 border_color: tuple[int, int, int] = (20, 20, 20), border_radius: int = -1,
                 border_width: int = 0,
                 text_color: tuple[int, int, int] = (20, 20, 20), font: str = '', font_size: int = 25):
        self.window = window
        self.x, self.y, self.width, self.height = x, y, width, height
        self.color = list(color)
        self.border_color = list(border_color)
        self.border_radius = border_radius
        self.border_width = border_width

        self.hovered = False
        self.pressed = False

        self.label = Label(self.window, 0, 0, title, text_color, size=font_size, font=font)
        x, y, w, h = self.label.get_rect()
        self.label.x = self.x + self.width // 2 - w // 2
        self.label.y = self.y + self.height // 2 - h // 2

    def draw(self):
        color = self.color  # local color for tweaks
        x, y, w, h = self.x, self.y, self.width, self.height
        if self.hovered:
            color = (240, 240, 240)
        if self.pressed:
            x += 1
            y += 1
            w -= 2
            h -= 2

        pg.draw.rect(self.window.screen, color, (x, y, w, h),
                     border_radius=self.border_radius)

        if self.border_width:
            pg.draw.rect(self.window.screen, self.border_color, (x, y, w, h),
                         width=self.border_width,
                         border_radius=self.border_radius)

        self.label.draw()

    def get_rect(self):
        return Rect(self.window, self.x, self.y, self.width, self.height)

    def get_pressed(self, button: int = 0) -> bool:  # TODO: maybe add callback
        x, y = pg.mouse.get_pos()
        btn = pg.mouse.get_pressed()
        if self.get_rect().collidepoint(x, y):
            self.hovered = True
            if btn[button]:
                self.pressed = True
            else:
                self.pressed = False
        else:
            self.hovered = False

        return self.pressed
