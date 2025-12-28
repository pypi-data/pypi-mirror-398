import pygame
from .window import Window
from random import randint
import math

WIDTH = 1200
HEIGHT = 800


class Particle:
    instances = []

    def __init__(self, window, x, y, angle, color, size=10, spread=100):
        self.__class__.instances.append(self)

        self.x = x
        self.y = y

        self.speed = randint(3, 40)

        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed

        self.size = size
        c = pygame.Color(color)
        self.color = [c.r, c.g, c.b]
        self.spread = spread

        self.gravity = [0, 1]

        self.window = window.screen

    def update(self):
        self.x += self.dx
        self.y += self.dy

        self.dx /= 1.05
        self.dy /= 1.05

        self.dx += self.gravity[0]
        self.dy += self.gravity[1]

        for i in range(3):
            if self.color[i] > 50:
                self.color[i] -= 0.005

        if self.y > HEIGHT:
            self.instances.remove(self)
            del self


def explode(window: Window, pos: tuple[int, int] | pygame.Vector2, size: int,
            color: tuple[int, int, int] | str) -> None:
    for k in range(0, 100):
        Particle(window, pos[0], pos[1], k, color, size=size)


def explosion_update() -> None:
    for particle in Particle.instances:
        pygame.draw.rect(particle.window, particle.color, (particle.x, particle.y, particle.size, particle.size))
        particle.update()
