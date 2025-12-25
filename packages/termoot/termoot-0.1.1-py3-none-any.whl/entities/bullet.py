from game.constants import (
    player_right, player_left, bullet_char_right, bullet_char_left,
    space_char, X, Y, DX, DY, BULLET_CHAR, COOLDOWN, COOLDOWN_MAX, RANGE, MAX_RANGE, IS_ALIVE, PLAYER, FACING,
    PLAYER_ON_RIGHT, PLAYER_ON_LEFT, BULLET_OWNER, ENEMY
)

bullets = []

def player_shoot(player, enemy):
    if player.get(COOLDOWN) > 0:
        return

    if player.get(PLAYER) == player_right:
        if player[X]+1 == enemy[X] and player[Y] == enemy[Y]:
            enemy[IS_ALIVE] = False
            return

        bullets.append({
            X: player[X] + 1,
            Y: player[Y],
            DX: 1,
            DY: 0,
            BULLET_CHAR: bullet_char_right,
            RANGE: MAX_RANGE,
            BULLET_OWNER: PLAYER
        })
    elif player.get(PLAYER) == player_left:
        if player[X]-1 == enemy[X] and player[Y] == enemy[Y]:
            enemy[IS_ALIVE] = False
            return

        bullets.append({
            X: player[X] - 1,
            Y: player[Y],
            DX: -1,
            DY: 0,
            BULLET_CHAR: bullet_char_left,
            RANGE: MAX_RANGE,
            BULLET_OWNER: PLAYER
        })

    player[COOLDOWN] = COOLDOWN_MAX

def enemy_shoot(enemy, player):
    if enemy.get(COOLDOWN) > 0:
        return

    if enemy.get(FACING) == PLAYER_ON_RIGHT:
        if enemy[X]+1 == player[X] and enemy[Y] == player[Y]:
            player[IS_ALIVE] = False
            return

        bullets.append({
            X: enemy[X] + 1,
            Y: enemy[Y],
            DX: 1,
            DY: 0,
            BULLET_CHAR: bullet_char_right,
            RANGE: MAX_RANGE,
            BULLET_OWNER: ENEMY
        })
    elif enemy.get(FACING) == PLAYER_ON_LEFT:
        if enemy[X]-1 == player[X] and enemy[Y] == player[Y]:
            player[IS_ALIVE] = False
            return

        bullets.append({
            X: enemy[X] - 1,
            Y: enemy[Y],
            DX: -1,
            DY: 0,
            BULLET_CHAR: bullet_char_left,
            RANGE: MAX_RANGE,
            BULLET_OWNER: ENEMY
        })

    enemy[COOLDOWN] = COOLDOWN_MAX


def update_bullets(walls):
    for bullet in bullets[:]:  # copy to allow removal
        next_x = bullet[X] + bullet[DX]
        next_y = bullet[Y] + bullet[DY]

        if walls[next_y][next_x] != space_char:
            bullets.remove(bullet)
            continue

        bullet[X] = next_x
        bullet[Y] = next_y

        bullet[RANGE] -= 1

        if bullet[RANGE] <= 0:
            bullets.remove(bullet)

def check_bullet_enemy_collision(enemy):
    for bullet in bullets[:]:
        if bullet[BULLET_OWNER] != PLAYER:
            continue
        if bullet[X] == enemy[X] and bullet[Y] == enemy[Y]:
            enemy[IS_ALIVE] = False
            bullets.remove(bullet)
            break


def check_bullet_player_collision(player):
    for bullet in bullets[:]:
        if bullet[BULLET_OWNER] != ENEMY:
            continue
        if bullet[X] == player[X] and bullet[Y] == player[Y]:
            player[IS_ALIVE] = False
            bullets.remove(bullet)
            break