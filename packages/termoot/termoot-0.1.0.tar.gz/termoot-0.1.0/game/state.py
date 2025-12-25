import random
from game.constants import COOLDOWN, X, Y, IS_ALIVE, space_char
from world.walls import init_walls

def init_player_pos(wall_height, wall_width, player, enemy):
    player[COOLDOWN] = 0
    player[X] = 2
    player[Y] = random.randint(1, wall_height-2)

def init_enemy_pos(wall_height, wall_width, player, enemy):
    enemy[COOLDOWN] = 0
    enemy[X] = wall_width - 3

    while True:
        y = random.randint(1, wall_height - 2)
        if y != player[Y]:
            enemy[Y] = y
            break

def update_cooldowns(player):
    if player[COOLDOWN] > 0:
        player[COOLDOWN] -= 1

def reset_game(stdscr, player, enemy, bullets):
    wall_height, wall_width = init_walls(stdscr)

    init_player_pos(wall_height, wall_width, player, enemy)
    init_enemy_pos(wall_height, wall_width, player, enemy)

    player[IS_ALIVE] = True
    enemy[IS_ALIVE] = True

    bullets.clear()

def is_tile_free(x, y, walls, player, enemy):
    if walls[y][x] != space_char:
        return False
    if player[X] == x and player[Y] == y and player[IS_ALIVE]:
        return False
    if enemy[X] == x and enemy[Y] == y and enemy[IS_ALIVE]:
        return False
    return True