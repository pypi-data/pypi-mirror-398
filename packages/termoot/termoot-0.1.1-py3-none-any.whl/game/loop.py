import curses
from game.constants import IS_ALIVE
from game.state import init_player_pos, init_enemy_pos, update_cooldowns, reset_game
from entities.player import player_1, update_player_pos
from entities.enemy import enemy_1, update_enemy_ai, enemy_can_see_player
from entities.bullet import player_shoot, update_bullets, check_bullet_enemy_collision, enemy_shoot, \
    check_bullet_player_collision
from world.walls import init_walls, create_walls
from ui.draw import draw_player, draw_enemy, draw_bullets, draw_walls
from ui.dialogs import handle_quit
from entities.bullet import bullets


def run_single_player_game(stdscr):
    stdscr.clear()
    curses.curs_set(0)
    curses.set_escdelay(25)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    has_colors = curses.has_colors()
    if has_colors:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)

    wall_height, wall_width = init_walls(stdscr)

    init_player_pos(wall_height, wall_width, player_1, enemy_1)
    init_enemy_pos(wall_height, wall_width, player_1, enemy_1)


    walls = create_walls(wall_height, wall_width)

    while True:
        stdscr.erase()

        if (player_1.get(IS_ALIVE) == False) and (enemy_1.get(IS_ALIVE) == True):
            stdscr.addstr(min(curses.LINES, curses.LINES // 2 - 5), (curses.COLS-13) // 2, "Enemy 1 wins!")
            stdscr.refresh()
            should_quit = not handle_quit(stdscr, True)
            if should_quit:
                break
            else:
                reset_game(stdscr, player_1, enemy_1, bullets)
        elif (player_1.get(IS_ALIVE) == True) and (enemy_1.get(IS_ALIVE) == False):
            stdscr.addstr(min(curses.LINES, curses.LINES // 2 - 5), (curses.COLS-14) // 2, "Player 1 wins!")
            stdscr.refresh()
            should_quit = not handle_quit(stdscr, True)
            if should_quit:
                break
            else:
                reset_game(stdscr, player_1, enemy_1, bullets)

        draw_walls(stdscr, walls, wall_height, wall_width) # draw map walls
        update_bullets(walls) # update bullets position
        check_bullet_enemy_collision(enemy_1) # check if bullet hits enemy
        check_bullet_player_collision(player_1) # check if bullet hits player
        update_cooldowns(player_1)
        update_cooldowns(enemy_1)
        draw_bullets(stdscr) # draw updated bullets

        if enemy_can_see_player(enemy_1, player_1, walls) and player_1.get(IS_ALIVE) and enemy_1.get(IS_ALIVE):
            enemy_shoot(enemy_1, player_1)
        else:
            update_enemy_ai(enemy_1, player_1, walls) # update enemy using basic algo

        if player_1.get(IS_ALIVE):
            draw_player(stdscr, has_colors) # add player in their updated position
        if enemy_1.get(IS_ALIVE):
            draw_enemy(stdscr, has_colors) # add enemy in their updated position

        stdscr.refresh()
        key = stdscr.getch()

        if key == -1:
            pass
        # Quit dialog
        elif key == 27:
            should_quit = handle_quit(stdscr)
            if should_quit:
                break
            continue
        elif key in (ord('W'), ord('w'), ord('A'), ord('a'), ord('S'), ord('s'), ord('D'), ord('d')):
            player_movement_input = chr(key).lower()
            update_player_pos(player_1, enemy_1, player_movement_input, walls)
        elif key == 32:
            player_shoot(player_1, enemy_1)

        curses.napms(50)  # ~20 FPS
