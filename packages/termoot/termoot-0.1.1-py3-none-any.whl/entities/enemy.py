from game.constants import (
    enemy_left, ENEMY, X, Y, COOLDOWN, IS_ALIVE, FACING, PLAYER_ON_LEFT, enemy_right, PLAYER_ON_RIGHT, MAX_RANGE,
    space_char, AI_TICK, AI_DELAY
)
from game.state import is_tile_free

enemy_1 = {
    ENEMY: enemy_left,
    X: 2,
    Y: 1,
    COOLDOWN: 0,
    IS_ALIVE: True,
    FACING: PLAYER_ON_LEFT,
    AI_TICK: 0,
    AI_DELAY: 5,   # higher value means slower enemy movement
}

def update_enemy_ai(enemy, player, walls):
    enemy[AI_TICK] += 1
    if enemy[AI_TICK] < enemy[AI_DELAY]:
        return
    enemy[AI_TICK] = 0

    if abs(enemy[X] - player[X]) + abs(enemy[Y] - player[Y]) == 1:
        return

    if enemy[Y] > player[Y] and is_tile_free(enemy[X], enemy[Y]-1, walls, player, enemy):
        enemy[Y] -= 1
    elif enemy[Y] < player[Y] and is_tile_free(enemy[X], enemy[Y]+1, walls, player, enemy):
        enemy[Y] += 1
    elif enemy[X] > player[X] and is_tile_free(enemy[X]-1, enemy[Y], walls, player, enemy):
        enemy[ENEMY] = enemy_left
        enemy[FACING] = PLAYER_ON_LEFT
        enemy[X] -= 1
    elif enemy[X] < player[X] and is_tile_free(enemy[X]+1, enemy[Y], walls, player, enemy):
        enemy[ENEMY] = enemy_right
        enemy[FACING] = PLAYER_ON_RIGHT
        enemy[X] += 1


def enemy_can_see_player(enemy, player, walls, max_range=MAX_RANGE):
    if enemy[Y] != player[Y]:
        return False

    # Player on left
    if enemy[X] > player[X] and enemy[FACING] == PLAYER_ON_LEFT:
        if abs(enemy[X] - player[X]) <= max_range:
            for x in range(player[X]+1, enemy[X]):
                if walls[enemy[Y]][x] != space_char:
                    return False
            return True

    # Player on right
    if enemy[X] < player[X] and enemy[FACING] == PLAYER_ON_RIGHT:
        if abs(enemy[X] - player[X]) <= max_range:
            for x in range(enemy[X]+1, player[X]):
                if walls[enemy[Y]][x] != space_char:
                    return False
            return True

    return False
