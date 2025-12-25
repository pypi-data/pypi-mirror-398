OPTIONS = [
    ("Single Player", "SINGLE"),
    ("Multiplayer", "MULTI"),
    ("LAN", "LAN"),
    ("Quit", "QUIT"),
]


def show_lobby(curses, stdscr):
    selected_index = 0
    h, w = 6, 30
    max_y, max_x = stdscr.getmaxyx()
    y, x = (max_y - h) // 2, (max_x - w) // 2

    win = curses.newwin(h, w, y, x)
    win.keypad(True)
    win.nodelay(False)

    while True:
        win.erase()
        win.box()

        win.addstr("┌")
        win.attron(curses.A_BOLD)
        win.addstr("TERMOOT")
        win.attroff(curses.A_BOLD)
        show_options(curses, win, selected_index)
        win.refresh()

        key = win.getch()

        if key in (curses.KEY_UP, 38, ord('w'), ord('W')) and selected_index > 0:
            selected_index -= 1
        elif key in (curses.KEY_DOWN, 40, ord('s'), ord('S')) and selected_index < len(OPTIONS) - 1:
            selected_index += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            win.clear()
            del win
            stdscr.touchwin()
            stdscr.refresh()
            label, key = OPTIONS[selected_index]
            return key

def show_options(curses, win, selected_index):
        for i, (label, key) in enumerate(OPTIONS):
            if i == selected_index:
                win.attron(curses.A_REVERSE)
            win.addstr(i+1, 1, f' {i+1}. {label} ')
            if i == selected_index:
                win.attroff(curses.A_REVERSE)
