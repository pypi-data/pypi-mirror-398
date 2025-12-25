MESSAGE = "Choose an option:"

OPTIONS = [
    "Option 1",
    "Option 2",
    "Option 3",
    "Option 4",
    "Option 5",
    "Option 6",
    "Option 7",
    "Option 8",
    "Option 9",
    "Option 10"
]

RETURN_MESSAGE = "exit"

MENU_TYPE = "default"


def standard_menu(message, options, return_message):
    while True:
        option_number = 1
        print(message)
        for option in options:
            print("    " + str(option_number) + ". " + option)
            option_number += 1

        print(f"    0. {return_message}")

        try:
            selection = int(input(f"""Please make a selection (0 - {option_number - 1})
    > """))
            if selection in range(len(options) + 1):
                return selection

        except ValueError:
            print(
                f"Invalid selection, please try again (0 - {option_number - 1})")


def curses_menu(message, options, return_message):
    import curses

    def _menu(stdscr):
        # configure curses
        curses.curs_set(0)  # hide cursor
        stdscr.keypad(True)
        max_y, max_x = stdscr.getmaxyx()

        # Layout
        title_lines = message.splitlines()
        title_height = len(title_lines) + 1  # leave a blank line after title
        options_height = len(options) + 1  # include return option
        window_height = title_height + options_height + 1

        if max_y < window_height or max_x < 20:
            raise curses.error("Terminal too small for menu")

        current = 0
        top_index = 0

        while True:
            stdscr.clear()

            # Print title/message
            for i, line in enumerate(title_lines):
                stdscr.addstr(i, 0, line[:max_x-1])

            # Print options. Keep simple: show all if fits, otherwise allow basic scroll
            start_y = title_height
            visible_height = max_y - start_y
            items = [f"{i+1}. {opt}" for i,
                     opt in enumerate(options)] + ["0. " + return_message]
            n_items = len(items)

            # Adjust top_index so current visible
            if current < top_index:
                top_index = current
            elif current >= top_index + visible_height:
                top_index = current - visible_height + 1

            for index in range(top_index, min(n_items, top_index + visible_height)):
                display_y = start_y + (index - top_index)
                text = items[index][:max_x-1]
                if index == current:
                    stdscr.attron(curses.A_REVERSE)
                    stdscr.addstr(display_y, 0, text)
                    stdscr.attroff(curses.A_REVERSE)
                else:
                    stdscr.addstr(display_y, 0, text)

            stdscr.refresh()

            key = stdscr.getch()
            if key in (curses.KEY_UP, ord('w')):
                # move up
                if current > 0:
                    current -= 1
            elif key in (curses.KEY_DOWN, ord('s')):
                # move down
                if current < n_items - 1:
                    current += 1
            elif key in (curses.KEY_HOME,):
                current = 0
            elif key in (ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6'), ord('7'), ord('8'), ord('9')) and int(chr(key)) <= len(options):
                current = int(chr(key)) - 1
            elif key in (ord('0'),):
                current = len(options)
            elif key in (10, 13, curses.KEY_ENTER):
                if current == len(options):
                    return 0
                return current + 1
            elif key in (27, ord('q')):  # Esc or q -> return 0
                return 0
    
    # Try to initialize curses; if it fails, fall back to standard_menu
    try:
        return curses.wrapper(_menu)
    except Exception:
        # fallback to standard menu if curses unavailable or terminal too small
        return standard_menu(message, options, return_message)


def menu_handler(message, options, return_message, menu_type="default"):
    # TODO add length checks to create tiers of menus, add checks for curses and select menu type
    if menu_type.lower() == "default" or menu_type.lower() == "curses":
        try:
            import curses
            menu_type = "curses"
        except ImportError:
            menu_type = "standard"

    if menu_type == "standard":
        return standard_menu(message, options, return_message)
    elif menu_type == "curses":
        return curses_menu(message, options, return_message)
    else:
        return "Invalid menu type"


if __name__ == "__main__":
    print(menu_handler(
        MESSAGE,
        OPTIONS, 
        RETURN_MESSAGE,
        MENU_TYPE))
