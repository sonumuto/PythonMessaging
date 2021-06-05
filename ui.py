import curses


class ChatUI:
    def __init__(self, stdscr):
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i, i, -1)
        self.stdscr = stdscr
        self.input_buffer = ""
        self.line_buffer = []
        self.line_buffer_color = []

        # Curses, why must you confuse me with your height, width, y, x
        chat_buffer_hwyx = (curses.LINES - 2, 0, 0, 0)
        chatline_yx = (curses.LINES - 1, 0)
        self.win_chatline = stdscr.derwin(*chatline_yx)
        self.win_chat_buffer = stdscr.derwin(*chat_buffer_hwyx)

        self.redraw_ui()

    def redraw_ui(self):
        """Redraws the entire UI"""
        h, w = self.stdscr.getmaxyx()
        self.stdscr.clear()
        self.stdscr.hline(h - 2, 0, "=", w)
        self.stdscr.refresh()

        self.redraw_chatbuffer()
        self.redraw_chatline()

    def redraw_chatline(self):
        """Redraw the user input textbox"""
        h, w = self.win_chatline.getmaxyx()
        self.win_chatline.clear()
        start = len(self.input_buffer) - w + 1
        if start < 0:
            start = 0
        self.win_chatline.addstr(0, 0, self.input_buffer[start:])
        self.win_chatline.refresh()

    def redraw_chatbuffer(self):
        """Redraw the chat message buffer"""
        self.win_chat_buffer.clear()
        h, w = self.win_chat_buffer.getmaxyx()
        j = len(self.line_buffer) - h
        if j < 0:
            j = 0
        for i in range(min(h, len(self.line_buffer))):
            self.win_chat_buffer.addstr(i, 0, self.line_buffer[j], curses.color_pair(self.line_buffer_color[j]))
            j += 1
        self.win_chat_buffer.refresh()

    def chatbuffer_add(self, msg, color):
        """
        Add a message to the chat buffer, automatically slicing it to
        fit the width of the buffer
        """
        self._linebuffer_add(msg, color)
        self.redraw_chatbuffer()
        self.redraw_chatline()
        self.win_chatline.cursyncup()

    def _linebuffer_add(self, msg, color):
        h, w = self.stdscr.getmaxyx()
        while len(msg) >= w:
            self.line_buffer.append(msg[:w])
            self.line_buffer_color.append(color)
            msg = msg[w:]
        if msg:
            self.line_buffer.append(msg)
            self.line_buffer_color.append(color)

    def prompt(self, msg):
        """Prompts the user for input and returns it"""
        self.input_buffer = msg
        self.redraw_chatline()
        res = self.wait_input()
        res = res[len(msg):]
        return res

    def wait_input(self, prompt=""):
        """
        Wait for the user to input a message and hit enter.
        Returns the message
        """
        self.input_buffer = prompt
        self.redraw_chatline()
        self.win_chatline.cursyncup()
        last = -1
        while last != ord('\n'):
            last = self.stdscr.getch()
            if last == ord('\n'):
                tmp = self.input_buffer
                self.input_buffer = ""
                self.redraw_chatline()
                self.win_chatline.cursyncup()
                return tmp[len(prompt):]
            elif last == curses.KEY_BACKSPACE or last == 127:
                if len(self.input_buffer) > len(prompt):
                    self.input_buffer = self.input_buffer[:-1]
            elif 32 <= last <= 126:
                self.input_buffer += chr(last)
            self.redraw_chatline()
