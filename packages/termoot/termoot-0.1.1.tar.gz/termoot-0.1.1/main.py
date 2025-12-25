import curses
from curses import wrapper

from ui.lobby import show_lobby
from game.loop import run_single_player_game


def main(stdscr):
    curses.curs_set(0)
    curses.set_escdelay(25)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    while True:
        stdscr.clear()
        stdscr.refresh()

        option = show_lobby(curses, stdscr)

        if option == "SINGLE":
            run_single_player_game(stdscr)
        elif option == "MULTI":
            stdscr.addstr(0, 0, "M")
            stdscr.refresh()
            stdscr.getch()
        elif option == "LAN":
            stdscr.addstr(0, 0, "L")
            stdscr.refresh()
            stdscr.getch()
        elif option == "QUIT":
            curses.endwin()
            break

def wrapper_main():
    """Entry point for the termoot console script"""
    wrapper(main)

if __name__ == "__main__":
    wrapper_main()