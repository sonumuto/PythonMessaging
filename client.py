import socket
import threading
import time
from ui import ChatUI
from curses import wrapper

SERVER = "127.0.0.1"
PORT = 8301

# Curses colors
WHITE_COLOR = 253
RED_COLOR = 124
GREEN_COLOR = 35
PURPLE_COLOR = 99
YELLOW_COLOR = 220
ORANGE_COLOR = 208
LIGHT_ORANGE_COLOR = 209
PINK_COLOR = 200
DARK_PURPLE_COLOR = 219
DARK_BLUE_COLOR = 27
DARK_GREEN_COLOR = 22

separator = " "

def print_commands(ui: ChatUI):
    """
    Prints all available commands


    @param ui: ChatUI
    """
    ui.chat_window_add(" ", PURPLE_COLOR)
    ui.chat_window_add("APPLICATION COMMANDS", PURPLE_COLOR)
    ui.chat_window_add("\t/quit : Quit application", PURPLE_COLOR)
    ui.chat_window_add("\t/help : List all commands", PURPLE_COLOR)
    ui.chat_window_add("USER AND MESSAGE COMMANDS", PURPLE_COLOR)
    ui.chat_window_add("\t/users : List all users in the room", PURPLE_COLOR)
    ui.chat_window_add("\t/status <new status> : Add or change status", PURPLE_COLOR)
    ui.chat_window_add("\t/r <username> <message> : Send a private message to the given username", PURPLE_COLOR)
    ui.chat_window_add("\t/super <message> : Send a message to all available users", PURPLE_COLOR)
    ui.chat_window_add("ROOM COMMANDS", PURPLE_COLOR)
    ui.chat_window_add("\t/room <room name> <password> : Create or join a room", PURPLE_COLOR)
    ui.chat_window_add("\t/list : List all available rooms", PURPLE_COLOR)
    ui.chat_window_add("MODERATOR COMMANDS", PURPLE_COLOR)
    ui.chat_window_add("\t/password <password> : Add or change password", PURPLE_COLOR)
    ui.chat_window_add("\t/description <new description> : Add or change description", PURPLE_COLOR)
    ui.chat_window_add("\t/ban <user> <reason> : Ban user", PURPLE_COLOR)
    ui.chat_window_add("\t/moderator <username> : Make user a moderator", PURPLE_COLOR)


def main(stdscr):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    stdscr.clear()
    ui = ChatUI(stdscr)

    ui.chat_window_add("Welcome to the chat app!", GREEN_COLOR)
    # Ask the user to enter a username until it is alphanumeric and is not taken.
    while True:
        ui.chat_window_add("Please enter a username:", GREEN_COLOR)
        username = ui.user_input()
        if not username.isalnum():
            ui.chat_window_add("Please enter a username that only contains alphanumeric characters!", RED_COLOR)
        else:
            client.sendall(bytes("NEW_USER " + username, 'UTF-8'))
            in_data = client.recv(1024)
            in_ = in_data.decode()
            in_ = in_.split()
            if in_[0] == "NEW_USER":
                if in_[1] == "SUCCESSFUL":
                    ui.chat_window_add(f"Welcome back {username}", GREEN_COLOR)
                    ui.chat_window_add(f"You can use /help command for list of available commands.", GREEN_COLOR)
                    break
                elif in_[1] == "UNSUCCESSFUL":
                    if in_[2] == "USERNAME_TAKEN":
                        ui.chat_window_add("Username is taken!", RED_COLOR)

    # Create and start threads for taking input and printing output.
    input_thread = threading.Thread(target=take_input, args=(client, ui,))
    output_thread = threading.Thread(target=print_output, args=(client, ui,))

    input_thread.start()
    output_thread.start()

    input_thread.join()
    output_thread.join()

    client.close()


def print_output(client, ui):
    """
    Prints output according to the command received from the server.


    @param client: Socket address
    @param ui: ChatUI
    """
    while True:
        # Receive and decode message from the server
        in_data = client.recv(1024)
        msg = in_data.decode()
        msg_split = msg.split()

        # APPLICATION COMMANDS
        # /quit : Quit application
        if msg_split[0] == "QUIT":
            ui.chat_window_add("Bye!", GREEN_COLOR)
            time.sleep(1)
            break

        # USER AND MESSAGE COMMANDS
        # /users : List all users in the room
        elif msg_split[0] == "USERS":
            ui.chat_window_add(f"Current Room: {msg_split[1]}\tUsers: {msg_split[2]}", DARK_GREEN_COLOR)
            for i in range(int(msg_split[2])):
                index = 2 * i + 3
                ui.chat_window_add(f"User: {msg_split[index]}\t\tStatus: {msg_split[index + 1]}", DARK_GREEN_COLOR)

        # /status <new status> : Add or change status
        elif msg_split[0] == "STATUS":
            if msg_split[1] == "SUCCESSFUL":
                ui.chat_window_add(f"You have changed your status to {msg_split[2]}!", DARK_GREEN_COLOR)

        # /r <username> <message> : Send a private message to the given username
        elif msg_split[0] == "PRIVATE":
            msg_ = separator.join(msg_split[3:])
            if msg_split[1] == "RECEIVER":
                ui.chat_window_add("> [" + msg_split[2] + "]: " + msg_, ORANGE_COLOR)
            elif msg_split[1] == "SENDER":
                ui.chat_window_add("< [" + msg_split[2] + "]: " + msg_, LIGHT_ORANGE_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                ui.chat_window_add("! [" + msg_split[2] + "]: " + msg_, RED_COLOR)
                ui.chat_window_add("This user does not exist!", RED_COLOR)

        # /super <message> : Send a message to all available users
        elif msg_split[0] == "SUPER":
            msg_ = separator.join(msg_split[2:])
            ui.chat_window_add("* [" + msg_split[1] + "]: " + msg_, YELLOW_COLOR)

        # ROOM COMMANDS
        # /room <room name> <password> : Create or join a room
        elif msg_split[0] == "ROOM":
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[3] == "USER":
                    ui.chat_window_add(f"Welcome to the {msg_split[2]} room!", DARK_PURPLE_COLOR)
                    if msg_split[4] == "DESCRIPTION":
                        msg_ = separator.join(msg_split[5:])
                        ui.chat_window_add(f"Description: {msg_}", DARK_PURPLE_COLOR)
                elif msg_split[3] == "MODERATOR":
                    ui.chat_window_add(f"Welcome to the {msg_split[2]} room!", DARK_PURPLE_COLOR)
                    ui.chat_window_add("You are now a moderator", PINK_COLOR)
                    ui.chat_window_add("You can use /help command to list moderator commands.", PINK_COLOR)

            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[3] == "INCORRECT_PASSWORD":
                    ui.chat_window_add(f"Incorrect password for {msg_split[2]}!", RED_COLOR)
                elif msg_split[3] == "PASSWORD_REQUIRED":
                    ui.chat_window_add(f"Password is required to join {msg_split[2]} room!", RED_COLOR)
                    ui.chat_window_add(f"Please use /room <room name> <password> command to join {msg_split[2]}",
                                       RED_COLOR)
                elif msg_split[3] == "BANNED":
                    ui.chat_window_add(f"You have been banned from {msg_split[2]} room!", PINK_COLOR)
            elif msg_split[1] == "JOINED":
                ui.chat_window_add(f"{msg_split[2]} has joined the room.", DARK_PURPLE_COLOR)
            elif msg_split[1] == "LEFT":
                ui.chat_window_add(f"{msg_split[2]} has left the room.", DARK_PURPLE_COLOR)
            elif msg_split[1] == "LOGGED_IN":
                ui.chat_window_add(f"{msg_split[2]} has logged in.", DARK_PURPLE_COLOR)

        # /list : List all available rooms
        elif msg_split[0] == "LIST":
            for i in range(int(msg_split[1])):
                index = 3 * i + 2
                password = ""
                if msg_split[index + 2] == "PASSWORD_REQUIRED":
                    password = "Password Required!"
                ui.chat_window_add(f"Room: {msg_split[index]}\tUsers: {msg_split[index + 1]}\t{password}",
                                   DARK_BLUE_COLOR)

        # MODERATOR COMMANDS
        # /password <password> : Add or change password
        elif msg_split[0] == "PASSWORD":
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[2] == "ADDED":
                    ui.chat_window_add("You have added a new password!", DARK_PURPLE_COLOR)
                elif msg_split[2] == "CHANGED":
                    ui.chat_window_add("You have changed the password!", DARK_PURPLE_COLOR)
                elif msg_split[2] == "REMOVED":
                    ui.chat_window_add("You have removed the password!", DARK_PURPLE_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "NOT_MODERATOR":
                    ui.chat_window_add("You have to be a moderator to change the password!", RED_COLOR)
                elif msg_split[2] == "NO_PASSWORD_TO_REMOVE":
                    ui.chat_window_add("There is no password in this room!", RED_COLOR)
                    ui.chat_window_add("Please enter a alphanumeric password by using /password <new password> command",
                                       RED_COLOR)
        # /description <new description> : Add or change description
        elif msg_split[0] == "DESCRIPTION":
            if msg_split[1] == "SUCCESSFUL":
                msg_ = separator.join(msg_split[4:])
                if msg_split[2] == "ADDED":
                    ui.chat_window_add(f"* {msg_split[3]} has added a description to room!", DARK_PURPLE_COLOR)
                    ui.chat_window_add(f"Description: {msg_}", DARK_PURPLE_COLOR)
                elif msg_split[2] == "CHANGED":
                    ui.chat_window_add(f"{msg_split[3]} has changed the description of the room!",
                                       DARK_PURPLE_COLOR)
                    ui.chat_window_add(f"Description: {msg_}", DARK_PURPLE_COLOR)

            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "NOT_MODERATOR":
                    ui.chat_window_add("You have to be a moderator to change description of the room!",
                                       RED_COLOR)

        # /ban <user> <reason> : Ban user
        elif msg_split[0] == "BAN":
            msg_ = separator.join(msg_split[5:])
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[2] == "RECEIVER":
                    ui.chat_window_add(
                        f"* [{msg_split[3]}]: You have been banned from {msg_split[5]} room! Reason: {msg_}",
                        PINK_COLOR)
                elif msg_split[2] == "OTHERS":
                    ui.chat_window_add(f"* [{msg_split[4]}]: {msg_split[3]} has been banned! Reason: {msg_}", PINK_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "SENDER_NOT_MODERATOR":
                    ui.chat_window_add("You have to be a moderator to use this command!", RED_COLOR)
                elif msg_split[2] == "NOT_EXISTS":
                    ui.chat_window_add("There is no such a user in this room!", RED_COLOR)
                elif msg_split[2] == "RECEIVER_MODERATOR":
                    ui.chat_window_add("You can't ban a moderator!", RED_COLOR)

        # /moderator <username> : Make user a moderator
        elif msg_split[0] == "MODERATOR":
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[2] == "RECEIVER":
                    ui.chat_window_add("You can use /help command to list moderator commands.", PINK_COLOR)
                elif msg_split[2] == "OTHERS":
                    ui.chat_window_add(f"* [{msg_split[3]}]: {msg_split[4]} is now a moderator!", PINK_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "NOT_MODERATOR":
                    ui.chat_window_add("You have to be a moderator to use /moderator <username> command!", RED_COLOR)
                elif msg_split[2] == "ALREADY_MODERATOR":
                    ui.chat_window_add("User is already moderator!", RED_COLOR)
                elif msg_split[2] == "NOT_EXIST":
                    ui.chat_window_add("There is no such a user in this room!", RED_COLOR)

        # MESSAGE
        elif msg_split[0] == "MSG":
            msg_ = separator.join(msg_split[2:])
            ui.chat_window_add("[" + msg_split[1] + "]: " + msg_, WHITE_COLOR)


def take_input(client, ui):
    """
    Take input from the ui and send command to the server.


    @param client:
    @param ui:
    """
    while True:
        out_data = ui.user_input()
        if out_data != "":
            split_out = out_data.split()
            if split_out[0][0] == '/':
                command = split_out[0][1:].upper()

                # APPLICATION COMMANDS
                # /quit : Quit application
                if command == "QUIT":
                    client.sendall(bytes("QUIT", 'UTF-8'))
                    break

                # /help : List all commands
                elif command == "HELP":
                    print_commands(ui)

                # USER AND MESSAGE COMMANDS
                # /users : List all users in the room
                elif command == "USERS":
                    client.sendall(bytes("USERS", 'UTF-8'))

                # /status <new status> : Add or change status
                elif command == "STATUS":
                    if len(split_out) == 1:
                        client.sendall(bytes("STATUS DEFAULT", 'UTF-8'))
                    elif len(split_out) == 2:
                        client.sendall(bytes("STATUS NEW_STATUS " + split_out[1], 'UTF-8'))
                    else:
                        ui.chat_window_add("Please enter a alphanumeric status by using /status <new status> command",
                                           RED_COLOR)

                # /r <username> <message> : Send a private message to the given username
                elif command == "R":
                    if len(split_out) < 3:
                        ui.chat_window_add("Please enter an username and a message by using /r <username> <message> "
                                          "command", RED_COLOR)
                    else:
                        msg_ = separator.join(split_out[2:])
                        client.sendall(bytes("PRIVATE " + split_out[1] + " " + msg_, 'UTF-8'))

                # /super <message> : Send a message to all available users
                elif command == "SUPER":
                    if len(split_out) == 1:
                        ui.chat_window_add("Please enter a message by using /super <message> command", RED_COLOR)
                    else:
                        msg_ = separator.join(split_out[1:])
                        client.sendall(bytes("SUPER " + msg_, 'UTF-8'))

                # ROOM COMMANDS
                # /room <room name> <password> : Create or join a room
                elif command == "ROOM":
                    if len(split_out) == 3:
                        client.sendall(bytes("ROOM " + split_out[1] + " PASSWORD " + split_out[2], 'UTF-8'))
                    elif len(split_out) == 2:
                        client.sendall(bytes("ROOM " + split_out[1] + " NO_PASSWORD", 'UTF-8'))
                    else:
                        ui.chat_window_add("Please use /room <room name> <password> command to join a room", RED_COLOR)

                # /list : List all available rooms
                elif command == "LIST":
                    client.sendall(bytes("LIST", 'UTF-8'))

                # MODERATOR COMMANDS
                # /password <password> : Add or change password
                elif command == "PASSWORD":
                    if len(split_out) >= 3:
                        ui.chat_window_add("Please enter a alphanumeric password by using /password <new password> "
                                          "command", RED_COLOR)
                    elif len(split_out) == 1:
                        client.sendall(bytes("PASSWORD REMOVE", 'UTF-8'))
                    else:
                        client.sendall(bytes("PASSWORD NEW_PASSWORD " + split_out[1], 'UTF-8'))

                # /description <new description> : Add or change description
                elif command == "DESCRIPTION":
                    if len(split_out) == 1:
                        client.sendall(bytes("DESCRIPTION DEFAULT", 'UTF-8'))
                    else:
                        msg_ = separator.join(split_out[1:])
                        client.sendall(bytes("DESCRIPTION NEW_DESCRIPTION " + msg_, 'UTF-8'))

                # /ban <user> <reason> : Ban user
                elif command == "BAN":
                    msg_ = separator.join(split_out[2:])
                    client.sendall(bytes("BAN " + split_out[1] + " " + msg_, 'UTF-8'))

                # /moderator <username> : Make user a moderator
                elif command == "MODERATOR":
                    if len(split_out) == 1:
                        ui.chat_window_add("Please enter a username by using /moderator <username> command!",
                                           RED_COLOR)
                    else:
                        client.sendall(bytes("MODERATOR " + split_out[1], 'UTF-8'))

                # Invalid command
                else:
                    ui.chat_window_add("Invalid command!", RED_COLOR)

            # Message
            else:
                client.sendall(bytes("MSG " + out_data, 'UTF-8'))


if __name__ == '__main__':
    wrapper(main)
