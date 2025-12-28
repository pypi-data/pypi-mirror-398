from pioneergame import Window, Label, Button, Rect, Sprite, explode, explosion_update
from pioneergame.presets import Player, Map
from pioneergame.sprites import green_tank, yellow_tank, brick_sprite, metal_sprite, bush_sprite

window = Window(1050, 900)
fps = 80

text = Label(window, 0, 0, '123123', 'red')

player = Player(window, 500, 300, 50, 50, green_tank)

player2 = Player(window, 700, 300, 50, 50, yellow_tank)

charmap = ['#####################',
           '#...................#',
           '#...................#',
           '#...................#',
           '#...................#',
           '#...................#',
           '#...................#',
           '#...................#',
           '#...................#',
           '#...................#',
           '#...................#',
           '#......W@$..........#',
           '#...................#',
           '#...................#',
           '#...................#',
           '#...................#',
           '#...................#',
           '#####################']


map = Map(window, charmap, brick_sprite, metal_sprite, bush_sprite)

flag = False

while True:
    window.fill('black')
    if window.get_scroll():
        print(">", window.get_scroll())

    player.draw()
    player.collide_map(map)
    player.collide_screen()
    player.collide_player(player2)

    player2.draw()
    player2.collide_map(map)
    player2.collide_screen()
    player2.collide_player(player)

    map.draw()

    text.center = player.center
    text.draw()

    if window.get_key('w'):
        player.go('up')
    elif window.get_key('s'):
        player.go('down')
    elif window.get_key('a'):
        player.go('left')
    elif window.get_key('d'):
        player.go('right')

    if window.get_key('up'):
        player2.go('up')
    elif window.get_key('down'):
        player2.go('down')
    elif window.get_key('left'):
        player2.go('left')
    elif window.get_key('right'):
        player2.go('right')

    if window.get_key('space'):
        player.shoot()
        player2.shoot()

    window.set_caption(f'{window.get_fps():.1f}')

    window.update(fps)
