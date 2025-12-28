from random import randint
import pygame as pg
from .window import Window


class Rect(pg.Rect):  # add class circle
    def __init__(self, window: Window, x, y, width, height,
                 color: str | pg.Color | tuple[int, int, int] = (255, 0, 255)):
        super().__init__(x, y, width, height)

        self.window = window
        self.color = pg.Color(color)

    def draw(self) -> None:
        pg.draw.rect(self.window.screen, self.color, self)

    def draw_outline(self, color: str | pg.Color | tuple[int, int, int] = (255, 0, 255), width: int = 1):
        pg.draw.rect(self.window.screen, color, self, width)

    @property
    def pos(self) -> tuple[int, int]:
        return self.x, self.y

    def random_teleport(self) -> None:
        self.x = randint(0, self.window.width - self.width)
        self.y = randint(0, self.window.height - self.height)

    def collide_bottom(self, other, collision_tolerance: int = 2) -> bool:
        return self.colliderect(other) and abs(self.bottom - other.top) < collision_tolerance

    def collide_top(self, other, collision_tolerance: int = 2) -> bool:
        return self.colliderect(other) and abs(self.top - other.bottom) < collision_tolerance

    def collide_right(self, other, collision_tolerance: int = 2) -> bool:
        return self.colliderect(other) and abs(self.right - other.left) < collision_tolerance

    def collide_left(self, other, collision_tolerance: int = 2) -> bool:
        return self.colliderect(other) and abs(self.left - other.right) < collision_tolerance

    def collision(self, other, collision_tolerance: int = 2) -> str:  # left, right, top, bottom, no
        if not self.colliderect(other):
            return 'no'
        if abs(self.bottom - other.top) < collision_tolerance:
            return 'bottom'
        if abs(self.top - other.bottom) < collision_tolerance:
            return 'top'
        if abs(self.right - other.left) < collision_tolerance:
            return 'right'
        if abs(self.left - other.right) < collision_tolerance:
            return 'left'

    def collide(self, other, collision_tolerance: int) -> None:
        """Resolving rect collision with other rect"""

        if not self.colliderect(other):
            return

        collision = self.collision(other, collision_tolerance)

        match collision:
            case "top":
                self.top = other.bottom
            case "bottom":
                self.bottom = other.top
            case "left":
                self.left = other.right
            case "right":
                self.right = other.left
