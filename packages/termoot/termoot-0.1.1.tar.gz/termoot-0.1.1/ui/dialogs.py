import curses

def handle_quit(stdscr, replay=False):
    h, w = 3, 40
    y, x = (curses.LINES - h) // 2, (curses.COLS - w) // 2
    win = curses.newwin(h, w, y, x)
    win.box()
    if replay:
        win.addstr(1, 2, "Rematch? (y/n)")
    else:
        win.addstr(1, 2, "Quit? (y/n)")
    win.refresh()

    option = win.getch()
    win.clear()
    del win
    stdscr.touchwin()
    stdscr.refresh()

    return option == ord('y')
