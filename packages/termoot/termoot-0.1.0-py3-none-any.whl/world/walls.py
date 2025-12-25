# -*- coding: utf-8 -*-
from game.constants import space_char

def init_walls(stdscr):
    max_height, max_width = stdscr.getmaxyx()
    return max_height, max_width-1

def create_walls(wall_height, wall_width):
    walls = []
    for y in range(0, wall_height):
        row = ""
        for x in range(0, wall_width):
            if (y == 0 or y == wall_height - 1) or (x == 0 or x == wall_width - 1):
                if y == 0 and x == 0:
                    row += "┌"
                elif y == 0 and x == wall_width - 1:
                    row += "┐"
                elif y == wall_height - 1 and x == 0:
                    row += "└"
                elif y == wall_height - 1 and x == wall_width - 1:
                    row += "┘"
                elif(x == 0) or (x == wall_width - 1):
                    row += "│"
                else:
                    row += "─"
            else:
                row += space_char
        walls.append(row)

    return walls
