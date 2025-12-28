# prestes

from .window import Window
from .rect import Rect
from .sprite import Sprite
from .label import Label


class Map:
    """map of blocks by char map\n
    # - brick\n
    W - unbreakable wall\n
    $ - bush\n
    @ - metal block
    """

    def __init__(self, window: Window, char_map: list[str], brick_sprite: Sprite,
                 metal_sprite: Sprite, bush_sprite: Sprite, block_size=50):
        self.window = window

        self.charm_map = char_map

        # brick
        self.brick_sprite = brick_sprite
        self.brick_sprite.window = self.window

        # wall is just grey rect

        # metal block
        self.metal_sprite = metal_sprite
        self.metal_sprite.window = self.window

        # bush
        self.bush_sprite = bush_sprite
        self.bush_sprite.window = self.window

        self.block_size = block_size

        self.blocks = []
        for y, row in enumerate(self.charm_map):
            for x, char in enumerate(row):
                if char == "#":  # brick
                    self.blocks.append(
                        Rect(self.window, x * self.block_size, y * block_size, self.block_size, self.block_size,
                             color='orange'))
                elif char == "W":  # unbreakable wall
                    self.blocks.append(
                        Rect(self.window, x * self.block_size, y * block_size, self.block_size, self.block_size,
                             color='grey'))
                elif char == "@":  # metal sprite
                    self.blocks.append(
                        Rect(self.window, x * self.block_size, y * block_size, self.block_size, self.block_size,
                             color='white'))
                elif char == "$":  # bush
                    self.blocks.append(
                        Rect(self.window, x * self.block_size, y * block_size, self.block_size, self.block_size,
                             color='green'))

    def draw(self):
        # type of block is knowed by color
        # (255, 165, 0, 255) orange - brick
        # (190, 190, 190, 255) grey - unbreakable wall
        # (255, 255, 255, 255) white - metal
        # (0, 255, 0, 255) green - bush
        for block in self.blocks:
            if block.color == (255, 165, 0, 255):
                self.brick_sprite.attach_to(block)
                self.brick_sprite.draw()
            elif block.color == (190, 190, 190, 255):
                block.draw()
            elif block.color == (255, 255, 255, 255):
                self.metal_sprite.attach_to(block)
                self.metal_sprite.draw()
            elif block.color == (0, 255, 0, 255):
                self.bush_sprite.attach_to(block)
                self.bush_sprite.draw()


class Bullet(Rect):
    instances = []

    def __init__(self, window: Window, x: int, y: int, width: int = 10, height: int = 10,
                 direction: list[int] = [1, 0], speed=10):
        super().__init__(window, x, y, width, height, color=(220, 200, 180))
        self.__class__.instances.append(self)

        self.direction = direction
        self.speed = speed

    def get_collision(self, collision_list: list[Rect]) -> Rect:
        """return rect that it has collide"""

        for rect in collision_list:
            if self.colliderect(rect):
                return rect

    def update_position(self):
        self.x += self.speed * self.direction[0]
        self.y += self.speed * self.direction[1]

    def destroy(self):
        self.__class__.instances.remove(self)


class Player(Rect):
    def __init__(self, window: Window, x: float, y: float, width: int, height: int, sprite: Sprite,
                 speed: int = 3, hp=5, shoot_cooldown=40):
        super().__init__(window, x, y, width, height)
        self.speed = speed

        self.old_sprite = sprite
        self.old_sprite.window = window
        self.old_sprite.attach_to(self)

        self.sprite = self.old_sprite  # спрайт для отрисовки, что б можно было вращать
        self.sprite.window = window

        self.direction = [0, -1]  # vector

        self.hp = hp
        self.start_hp = hp  # Изначальное количество жизней

        self.hp_label = Label(self.window, 0, 0, f'{hp} HP', color='white')
        self.hp_label_rect = self.hp_label.get_rect()

        self.shoot_cooldown = shoot_cooldown  # cooldown to shoot again
        self.shoot_cooldown_counter = 0

    def go(self, direction: str) -> None:
        """go("up"), go("down"), go("left") or go("right")"""

        match direction:
            case "up":
                self.sprite = self.old_sprite
                self.y -= self.speed
                self.direction = [0, -1]
            case "down":
                self.sprite = self.old_sprite.get_rotated(180)
                self.y += self.speed
                self.direction = [0, 1]
            case "right":
                self.sprite = self.old_sprite.get_rotated(-90)
                self.x += self.speed
                self.direction = [1, 0]
            case "left":
                self.sprite = self.old_sprite.get_rotated(90)
                self.x -= self.speed
                self.direction = [-1, 0]

        self.sprite.attach_to(self)

    def draw(self) -> None:
        self.shoot_cooldown_counter += 1

        self.sprite.draw()

        for bullet in Bullet.instances.copy():
            bullet.draw()
            bullet.update_position()

        # health display
        self.hp_label.x = self.right
        self.hp_label.y = self.top - self.hp_label_rect.height
        self.hp_label.draw()

    def damage(self, amount: int = 1):
        self.hp -= amount
        self.hp_label.set_text(f'{self.hp} HP')

    def collide_screen(self):
        """ collide with screen border"""
        if self.right > self.window.width:
            self.right = self.window.width
        if self.left < 0:
            self.left = 0
        if self.bottom > self.window.height:
            self.bottom = self.window.height
        if self.top < 0:
            self.top = 0

    def collide_player(self, other, collision_tolerance: int = 8) -> None:
        old = self.copy()
        self.collide(other, collision_tolerance)
        other.collide(old, collision_tolerance)

        for bullet in Bullet.instances.copy():
            if bullet.colliderect(other):
                other.damage()
                bullet.destroy()

    def collide_map(self, block_map: Map, collision_tolerance: int = 8):
        """Char map collision\n
        Wall and Metal couldn't break\n
        Bush couldn't collide"""
        for bullet in Bullet.instances.copy():
            rect = bullet.get_collision(block_map.blocks)
            if rect:
                if rect.color == (255, 255, 255, 255) or rect.color == (190, 190, 190, 255):
                    # if rect is wall or metal block, just destroy bullet
                    bullet.destroy()
                    continue
                block_map.blocks.remove(rect)
                bullet.destroy()

        for block in block_map.blocks.copy():
            if block.color == (0, 255, 0, 255):  # if block is bush, no collision
                continue
            self.collide(block, collision_tolerance)

    def shoot(self):
        """Shooting with instance of Bullet"""
        if self.shoot_cooldown_counter >= self.shoot_cooldown:  # if counter is overflowed
            self.shoot_cooldown_counter = 0

            Bullet(self.window, self.centerx + self.direction[0] * self.width // 2 - 5,
                   self.centery + self.direction[1] * self.height // 2 - 5, direction=self.direction)
