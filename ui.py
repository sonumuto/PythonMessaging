import curses


class ChatUI:
    def __init__(self, stdscr):
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i, i, -1)
        self.stdscr = stdscr
        self.input_buffer = ""
        self.buffer = []
        self.buffer_color = []

        chat_hwyx = (curses.LINES - 2, 0, 0, 0)
        chatline_yx = (curses.LINES - 1, 0)
        self.win_chatline = stdscr.derwin(*chatline_yx)
        self.chat_win = stdscr.derwin(*chat_hwyx)

        self.y, self.x = self.stdscr.getmaxyx()
        self.stdscr.clear()
        self.stdscr.hline(self.y - 2, 0, "~", self.x)
        self.stdscr.refresh()

        self.redraw_chat()
        self.redraw_chatline()

    def redraw_chatline(self):
        """
        Redraw the user input textbox
        """

        self.win_chatline.clear()
        start = len(self.input_buffer) - self.x + 1
        if start < 0:
            start = 0
        self.win_chatline.addstr(0, 0, self.input_buffer[start:])
        self.win_chatline.refresh()

    def redraw_chat(self):
        """
        Redraw the chat message buffer
        """
        self.chat_win.clear()
        y, x = self.chat_win.getmaxyx()
        j = len(self.buffer) - y
        if j < 0:
            j = 0
        for i in range(min(y, len(self.buffer))):
            self.chat_win.addstr(i, 0, self.buffer[j], curses.color_pair(self.buffer_color[j]))
            j += 1
        self.chat_win.refresh()

    def chat_window_add(self, msg, color):
        """
        Add a message to the chat buffer, automatically slicing it to
        fit the width of the buffer


        @param msg: Message to print
        @param color: Color of the message
        """
        self.add_buffer(msg, color)
        self.redraw_chat()
        self.redraw_chatline()
        self.win_chatline.cursyncup()

    def add_buffer(self, msg, color):
        y, x = self.stdscr.getmaxyx()
        while len(msg) >= x:
            self.buffer.append(msg[:x])
            self.buffer_color.append(color)
            msg = msg[x:]
        if msg:
            self.buffer.append(msg)
            self.buffer_color.append(color)

    def prompt(self, msg):
        """
        Prompts the user for input and returns it
        """
        self.input_buffer = msg
        self.redraw_chatline()
        res = self.user_input()
        res = res[len(msg):]
        return res

    def user_input(self, prompt=""):
        """
        Wait for the user to input a message and hit enter.
        Returns the message


        @param prompt: Input to return
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
