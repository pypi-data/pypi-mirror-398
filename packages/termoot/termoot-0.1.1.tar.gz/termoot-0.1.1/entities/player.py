from game.constants import (
    player_right, player_left, PLAYER, X, Y, COOLDOWN, IS_ALIVE
)
from game.state import is_tile_free

player_1 = {
    PLAYER: player_right,
    X: 2,
    Y: 1,
    COOLDOWN: 0,
    IS_ALIVE: True
}

def update_player_pos(player, enemy, player_movement_input, walls):
    match player_movement_input:
        case "w":
            if is_tile_free(player[X], player[Y]-1, walls, player, enemy):
                player[Y] -= 1
        case "s":
            if is_tile_free(player[X], player[Y]+1, walls, player, enemy):
                player[Y] += 1
        case "a":
            if is_tile_free(player[X]-1, player[Y], walls, player, enemy):
                player[X] -= 1
            player[PLAYER] = player_left
        case "d":
            if is_tile_free(player[X]+1, player[Y], walls, player, enemy):
                player[X] += 1
            player[PLAYER] = player_right
