# -*- coding: utf-8 -*-
player_right = "p"
player_left = "q"

enemy_right = "b"
enemy_left = "d"

PLAYER = "player"
ENEMY = "enemy"
X = "x"
Y = "y"
IS_ALIVE = "is_alive"

bullet_char_right = "‣"
bullet_char_left = "◂"

space_char = " "

DX = "dx"
DY = "dy"
BULLET_CHAR = "bullet_char"

COOLDOWN = "cooldown"
COOLDOWN_MAX = 5  # frames between shots (~250ms at 50ms/frame)

RANGE = "range"
MAX_RANGE = 30  # tiles

FACING = "facing"   # "left" or "right"
PLAYER_ON_LEFT = "left"
PLAYER_ON_RIGHT = "right"

AI_TICK = "ai_tick"
AI_DELAY = "ai_delay"

BULLET_OWNER = "bullet_owner"   # "player" or "enemy"