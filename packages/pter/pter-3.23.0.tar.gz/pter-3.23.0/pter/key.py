import curses


class Key:
    SPECIAL = {' ': '<space>',
               }
    ALT_BACKSPACE = '<alt_backspace>'
    ALT_D = '<alt_d>'
    BACKSPACE = '<backspace>'
    CARET = '<caret>'
    CTRL_BACKSPACE = '<ctrl_backspace>'
    CTRL_DELETE = '<ctrl_del>'
    CTRL_LEFT = '<ctrl_left>'
    CTRL_RIGHT = '<ctrl_right>'
    DELETE = '<del>'
    LEFT = '<left>'
    RIGHT = '<right>'
    UP = '<up>'
    DOWN = '<down>'
    PGUP = '<pgup>'
    PGDN = '<pgdn>'
    HOME = '<home>'
    END = '<end>'
    RETURN = '<return>'
    ESCAPE = '<escape>'
    SPACE = ' '
    TAB = '<tab>'
    F1 = '<f1>'
    F2 = '<f2>'
    F3 = '<f3>'
    F4 = '<f4>'
    F5 = '<f5>'
    F6 = '<f6>'
    F7 = '<f7>'
    F8 = '<f8>'
    F9 = '<f9>'
    F10 = '<f10>'
    F11 = '<f11>'
    F12 = '<f12>'
    F13 = '<f13>'
    F14 = '<f14>'
    F15 = '<f15>'
    F16 = '<f16>'
    F17 = '<f17>'
    F18 = '<f18>'
    F19 = '<f19>'
    F20 = '<f20>'
    RESIZE = '<resize>'
    TIMEOUT = '<timeout>'

    def __init__(self, value, special=False):
        self.value = value
        self.special = special

    @classmethod
    def read(cls, stdscr):
        termname = curses.termname().decode()

        try:
            value = stdscr.get_wch()
            if value == -1:
                return Key(Key.TIMEOUT, special=True)

            # these have only been properly tested under `xterm-256color`
            if termname == 'xterm' or termname.startswith('xterm-'):
                # check for Ctrl + Delete
                if value == 524:
                    return Key(Key.CTRL_DELETE, special=True)
                # check for Ctrl + left arrow
                elif value == 550:
                    return Key(Key.CTRL_LEFT, special=True)
                # check for Ctrl + right arrow
                elif value == 565:
                    return Key(Key.CTRL_RIGHT, special=True)

            # check for good old caret to distinguish it from control sequences
            if value == '^':
                return Key(Key.CARET, special=True)

            # check for Alt + Backspace/Alt + d
            elif value == '\x1b': # Alt or Escape
                stdscr.timeout(curses.get_escdelay())
                try:
                    next_value = stdscr.get_wch()
                    if next_value == curses.KEY_BACKSPACE:
                        return Key(Key.ALT_BACKSPACE, special=True)
                    elif isinstance(next_value, str) and next_value == 'd': # M-d, a-la bash. TODO: Support Alt/Meta-based shortcuts?
                        return Key(Key.ALT_D, special=True)
                    else:
                        return Key(Key.TIMEOUT, special=True) # we don't want e.g. M-f to act as Escape
                except curses.error as exc:
                    if str(exc) == 'no input':
                        return Key(Key.ESCAPE, True) # good old Escape
                    else:
                        pass

            return Key.parse(value)
        except curses.error as exc:
            if str(exc) == 'no input':
                return Key(Key.TIMEOUT, special=True)
            return Key('C', special=True)
        except KeyboardInterrupt:
            return Key('C', special=True)
        except EOFError:
            return Key('D', special=True)

    @classmethod
    def parse(cls, value):
        if value == curses.KEY_BACKSPACE:
            return Key(Key.BACKSPACE, True)
        elif value == curses.KEY_DC:
            return Key(Key.DELETE, True)
        elif value == curses.KEY_LEFT:
            return Key(Key.LEFT, True)
        elif value == curses.KEY_RIGHT:
            return Key(Key.RIGHT, True)
        elif value == curses.KEY_UP:
            return Key(Key.UP, True)
        elif value == curses.KEY_DOWN:
            return Key(Key.DOWN, True)
        elif value == curses.KEY_END:
            return Key(Key.END, True)
        elif value == curses.KEY_HOME:
            return Key(Key.HOME, True)
        elif value == curses.KEY_NPAGE:
            return Key(Key.PGDN, True)
        elif value == curses.KEY_PPAGE:
            return Key(Key.PGUP, True)
        elif value == curses.KEY_F1:
            return Key(Key.F1, True)
        elif value == curses.KEY_F2:
            return Key(Key.F2, True)
        elif value == curses.KEY_F3:
            return Key(Key.F3, True)
        elif value == curses.KEY_F4:
            return Key(Key.F4, True)
        elif value == curses.KEY_F5:
            return Key(Key.F5, True)
        elif value == curses.KEY_F6:
            return Key(Key.F6, True)
        elif value == curses.KEY_F7:
            return Key(Key.F7, True)
        elif value == curses.KEY_F8:
            return Key(Key.F8, True)
        elif value == curses.KEY_F9:
            return Key(Key.F9, True)
        elif value == curses.KEY_F10:
            return Key(Key.F10, True)
        elif value == curses.KEY_F11:
            return Key(Key.F11, True)
        elif value == curses.KEY_F12:
            return Key(Key.F12, True)
        elif value == curses.KEY_F13:
            return Key(Key.F13, True)
        elif value == curses.KEY_F14:
            return Key(Key.F14, True)
        elif value == curses.KEY_F15:
            return Key(Key.F15, True)
        elif value == curses.KEY_F16:
            return Key(Key.F16, True)
        elif value == curses.KEY_F17:
            return Key(Key.F17, True)
        elif value == curses.KEY_F18:
            return Key(Key.F18, True)
        elif value == curses.KEY_F19:
            return Key(Key.F19, True)
        elif value == curses.KEY_F20:
            return Key(Key.F20, True)
        elif value == curses.KEY_RESIZE:
            return Key(Key.RESIZE, True)
        elif isinstance(value, int):
            # no idea what key that is
            return Key(Key.TIMEOUT, special=True)
        elif isinstance(value, str):
            try:
                ctrlkey = str(curses.unctrl(value), 'ascii')
            except OverflowError:
                # some unicode, you probably want to see it
                return Key(value, False)

            if value in "\n\r":
                return Key(Key.RETURN, special=True)

            if value == ' ':
                return Key(Key.SPACE)

            if value == "\t":
                return Key(Key.TAB)

            # check for Ctrl + Backspace
            if ctrlkey == '^H':
                return Key(Key.CTRL_BACKSPACE, special=True)

            if ctrlkey == '^?':
                return Key(Key.BACKSPACE, special=True)

            if ctrlkey == '^[':
                return Key(Key.ESCAPE, True)

            if ctrlkey != value:
                return Key(ctrlkey[1:], True)
            else:
                return Key(value)

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        if isinstance(other, Key):
            return self.value == other.value and self.special == other.special
        elif isinstance(other, str):
            return str(self) == other
        elif isinstance(other, bytes):
            return str(self) == str(other, 'ascii')
        raise ValueError("'other' has unexpected type {type(other)}")

    def __str__(self):
        if self.special:
            if self.value.startswith('<'):
                return self.value
            return  '^' + self.value
        return self.value

