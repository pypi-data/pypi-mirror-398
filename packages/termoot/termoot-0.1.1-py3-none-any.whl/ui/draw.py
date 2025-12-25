import curses
from game.constants import X, Y, PLAYER, ENEMY, BULLET_CHAR
from entities.player import player_1
from entities.enemy import enemy_1
from entities.bullet import bullets

def draw_player(stdscr, has_colors):
    if has_colors:
        stdscr.attron(curses.color_pair(1))
        stdscr.attron(curses.A_BOLD)

    stdscr.addch(player_1.get(Y), player_1.get(X), player_1.get(PLAYER))

    if has_colors:
        stdscr.attroff(curses.color_pair(1))
        stdscr.attroff(curses.A_BOLD)

def draw_enemy(stdscr, has_colors):
    if has_colors:
        stdscr.attron(curses.color_pair(2))
        stdscr.attron(curses.A_BOLD)

    stdscr.addch(enemy_1.get(Y), enemy_1.get(X), enemy_1.get(ENEMY))

    if has_colors:
        stdscr.attroff(curses.color_pair(2))
        stdscr.attroff(curses.A_BOLD)

def draw_bullets(stdscr):
    for bullet in bullets:
        stdscr.addch(bullet[Y], bullet[X], bullet[BULLET_CHAR])

def draw_walls(stdscr, walls, wall_height, wall_width):
    for y in range(0, wall_height):
        for x in range(0, wall_width):
            stdscr.addch(y, x, walls[y][x])
