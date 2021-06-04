import socket
import threading
import time
from ui import ChatUI
from curses import wrapper

SERVER = "127.0.0.1"
PORT = 8300

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


def str_concatenate(list_, a, b):
    str_ = ""
    for i in range(a, b):
        str_ = str_ + list_[i] + " "
    return str_[:len(str_) - 1]


def print_commands(ui: ChatUI):
    ui.chatbuffer_add(" ", PURPLE_COLOR)
    ui.chatbuffer_add("APPLICATION COMMANDS", PURPLE_COLOR)
    ui.chatbuffer_add("\t/quit : Quit application", PURPLE_COLOR)
    ui.chatbuffer_add("\t/help : List all commands", PURPLE_COLOR)
    ui.chatbuffer_add("USER AND MESSAGE COMMANDS", PURPLE_COLOR)
    ui.chatbuffer_add("\t/users : List all users in the room", PURPLE_COLOR)
    ui.chatbuffer_add("\t/status <new status> : Add or change status", PURPLE_COLOR)
    ui.chatbuffer_add("\t/r <username> <message> : Send a private message to the given username", PURPLE_COLOR)
    ui.chatbuffer_add("\t/super <message> : Send a message to all available users", PURPLE_COLOR)
    ui.chatbuffer_add("ROOM COMMANDS", PURPLE_COLOR)
    ui.chatbuffer_add("\t/room <room name> <password> : Create or join a room", PURPLE_COLOR)
    ui.chatbuffer_add("\t/list : List all available rooms", PURPLE_COLOR)
    ui.chatbuffer_add("MODERATOR COMMANDS", PURPLE_COLOR)
    ui.chatbuffer_add("\t/password <password> : Add or change password", PURPLE_COLOR)
    ui.chatbuffer_add("\t/description <new description> : Add or change description", PURPLE_COLOR)
    ui.chatbuffer_add("\t/ban <user> <reason> : Ban user", PURPLE_COLOR)
    ui.chatbuffer_add("\t/moderator <username> : Make user a moderator", PURPLE_COLOR)


def main(stdscr):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    stdscr.clear()
    ui = ChatUI(stdscr)

    ui.chatbuffer_add("Welcome to the chat app!", GREEN_COLOR)
    while True:
        ui.chatbuffer_add("Please enter an username:", GREEN_COLOR)
        username = ui.wait_input()
        if not username.isalnum():
            ui.chatbuffer_add("Please enter an username that only contains alphanumeric characters!", RED_COLOR)
        else:
            client.sendall(bytes("NEW_USER " + username, 'UTF-8'))
            in_data = client.recv(1024)
            in_ = in_data.decode()
            in_ = in_.split()
            if in_[0] == "NEW_USER":
                if in_[1] == "SUCCESSFUL":
                    ui.chatbuffer_add(f"Welcome back {username}", GREEN_COLOR)
                    ui.chatbuffer_add(f"You can use /help command for list of available commands.", GREEN_COLOR)
                    break
                elif in_[1] == "UNSUCCESSFUL":
                    if in_[2] == "USERNAME_TAKEN":
                        ui.chatbuffer_add("Username is taken!", RED_COLOR)

    input_thread = threading.Thread(target=take_input, args=(client, ui,))
    output_thread = threading.Thread(target=print_output, args=(client, ui,))

    input_thread.start()
    output_thread.start()

    input_thread.join()
    output_thread.join()

    client.close()

def print_output(client, ui):
    while True:
        in_data = client.recv(1024)
        msg = in_data.decode()
        msg_split = msg.split()

        # APPLICATION COMMANDS
        # /quit
        if msg_split[0] == "QUIT":
            break

        # USER AND MESSAGE COMMANDS
        # /users
        elif msg_split[0] == "USERS":
            ui.chatbuffer_add(f"Current Room: {msg_split[1]}\tUsers: {msg_split[2]}", DARK_GREEN_COLOR)
            for i in range(int(msg_split[2])):
                index = 2 * i + 3
                ui.chatbuffer_add(f"User: {msg_split[index]}\t\tStatus: {msg_split[index + 1]}", DARK_GREEN_COLOR)

        # /status
        elif msg_split[0] == "STATUS":
            if msg_split[1] == "SUCCESSFUL":
                ui.chatbuffer_add(f"You have changed your status to {msg_split[2]}!", DARK_GREEN_COLOR)

        # /r
        elif msg_split[0] == "PRIVATE":
            msg_ = str_concatenate(msg_split, 3, len(msg_split))
            if msg_split[1] == "RECEIVER":
                ui.chatbuffer_add("> [" + msg_split[2] + "]: " + msg_, ORANGE_COLOR)
            elif msg_split[1] == "SENDER":
                ui.chatbuffer_add("< [" + msg_split[2] + "]: " + msg_, LIGHT_ORANGE_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                ui.chatbuffer_add("! [" + msg_split[2] + "]: " + msg_, RED_COLOR)
                ui.chatbuffer_add("This user does not exist!", RED_COLOR)

        # /super
        elif msg_split[0] == "SUPER":
            msg_ = str_concatenate(msg_split, 2, len(msg_split))
            ui.chatbuffer_add("* [" + msg_split[1] + "]: " + msg_, YELLOW_COLOR)

        # ROOM COMMANDS
        # /room
        elif msg_split[0] == "ROOM":
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[3] == "USER":
                    ui.chatbuffer_add(f"Welcome to the {msg_split[2]} room!", DARK_PURPLE_COLOR)
                    if msg_split[4] == "DESCRIPTION":
                        msg_ = str_concatenate(msg_split, 5, len(msg_split))
                        ui.chatbuffer_add(f"Description: {msg_}", DARK_PURPLE_COLOR)
                elif msg_split[3] == "MODERATOR":
                    ui.chatbuffer_add(f"Welcome to the {msg_split[2]} room!", DARK_PURPLE_COLOR)
                    ui.chatbuffer_add("You are now a moderator", PINK_COLOR)
                    ui.chatbuffer_add("You can use /help command to list moderator commands.", PINK_COLOR)

            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[3] == "INCORRECT_PASSWORD":
                    ui.chatbuffer_add(f"Incorrect password for {msg_split[2]}!", RED_COLOR)
                elif msg_split[3] == "PASSWORD_REQUIRED":
                    ui.chatbuffer_add(f"Password is required to join {msg_split[2]} room!", RED_COLOR)
                    ui.chatbuffer_add(f"Please use /room <room name> <password> command to join {msg_split[2]}"
                                      , RED_COLOR)
                elif msg_split[3] == "BANNED":
                    ui.chatbuffer_add(f"You have been banned from {msg_split[2]} room!", PINK_COLOR)
            elif msg_split[1] == "JOINED":
                ui.chatbuffer_add(f"{msg_split[2]} has joined the room.", DARK_PURPLE_COLOR)
            elif msg_split[1] == "LEFT":
                ui.chatbuffer_add(f"{msg_split[2]} has left the room.", DARK_PURPLE_COLOR)
            elif msg_split[1] == "LOGGED_IN":
                ui.chatbuffer_add(f"{msg_split[2]} has logged in.", DARK_PURPLE_COLOR)

        # /list
        elif msg_split[0] == "LIST":
            for i in range(int(msg_split[1])):
                index = 3 * i + 2
                password = ""
                if msg_split[index + 2] == "PASSWORD_REQUIRED":
                    password = "Password Required!"
                ui.chatbuffer_add(f"Room: {msg_split[index]}\tUsers: {msg_split[index + 1]}\t{password}",
                                  DARK_BLUE_COLOR)

        # MODERATOR COMMANDS
        # /password
        elif msg_split[0] == "PASSWORD":
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[2] == "ADDED":
                    ui.chatbuffer_add("You have added a new password!", DARK_PURPLE_COLOR)
                elif msg_split[2] == "CHANGED":
                    ui.chatbuffer_add("You have changed the password!", DARK_PURPLE_COLOR)
                elif msg_split[2] == "REMOVED":
                    ui.chatbuffer_add("You have removed the password!", DARK_PURPLE_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "NOT_MODERATOR":
                    ui.chatbuffer_add("You have to be a moderator to change the password!", RED_COLOR)
                elif msg_split[2] == "NO_PASSWORD_TO_REMOVE":
                    ui.chatbuffer_add("There is no password in this room!", RED_COLOR)
                    ui.chatbuffer_add("Please enter a alphanumeric password by using /password <new password> command",
                                      RED_COLOR)
        # /description
        elif msg_split[0] == "DESCRIPTION":
            if msg_split[1] == "SUCCESSFUL":
                msg_ = str_concatenate(msg_split, 4, len(msg_split))
                if msg_split[2] == "ADDED":
                    ui.chatbuffer_add(f"* {msg_split[3]} has added a description to room!", DARK_PURPLE_COLOR)
                    ui.chatbuffer_add(f"Description: {msg_}", DARK_PURPLE_COLOR)
                elif msg_split[2] == "CHANGED":
                    ui.chatbuffer_add(f"{msg_split[3]} has changed the description of the room!",
                                      DARK_PURPLE_COLOR)
                    ui.chatbuffer_add(f"Description: {msg_}", DARK_PURPLE_COLOR)

            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "NOT_MODERATOR":
                    ui.chatbuffer_add("You have to be a moderator to change description of the room!",
                                      RED_COLOR)

        # /ban
        elif msg_split[0] == "BAN":
            msg_ = str_concatenate(msg_split, 5, len(msg_split))
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[2] == "RECEIVER":
                    ui.chatbuffer_add(
                        f"* [{msg_split[3]}]: You have been banned from {msg_split[5]} room! Reason: {msg_}",
                        PINK_COLOR)
                elif msg_split[2] == "OTHERS":
                    ui.chatbuffer_add(f"* [{msg_split[4]}]: {msg_split[3]} has been banned! Reason: {msg_}", PINK_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "SENDER_NOT_MODERATOR":
                    ui.chatbuffer_add("You have to be a moderator to use this command!", RED_COLOR)
                elif msg_split[2] == "NOT_EXISTS":
                    ui.chatbuffer_add("There is no such a user in this room!", RED_COLOR)
                elif msg_split[2] == "RECEIVER_MODERATOR":
                    ui.chatbuffer_add("You can't ban a moderator!", RED_COLOR)

        # /moderator
        elif msg_split[0] == "MODERATOR":
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[2] == "RECEIVER":
                    ui.chatbuffer_add("You can use /help command to list moderator commands.", PINK_COLOR)
                elif msg_split[2] == "OTHERS":
                    ui.chatbuffer_add(f"* [{msg_split[3]}]: {msg_split[4]} is now a moderator!", PINK_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "NOT_MODERATOR":
                    ui.chatbuffer_add("You have to be a moderator to use /moderator <username> command!", RED_COLOR)
                elif msg_split[2] == "ALREADY_MODERATOR":
                    ui.chatbuffer_add("User is already moderator!", RED_COLOR)
                elif msg_split[2] == "NOT_EXIST":
                    ui.chatbuffer_add("There is no such a user in this room!", RED_COLOR)

        # MESSAGE
        elif msg_split[0] == "MSG":
            msg_ = str_concatenate(msg_split, 2, len(msg_split))
            ui.chatbuffer_add("[" + msg_split[1] + "]: " + msg_, WHITE_COLOR)


def take_input(client, ui):
    while True:
        out_data = ui.wait_input()
        if out_data != "":
            split_out = out_data.split()
            if split_out[0][0] == '/':
                command = split_out[0][1:].upper()

                # APPLICATION COMMANDS
                # /quit
                if command == "QUIT":
                    client.sendall(bytes("QUIT", 'UTF-8'))
                    break

                # /help
                elif command == "HELP":
                    print_commands(ui)

                # USER AND MESSAGE COMMANDS
                # /users
                elif command == "USERS":
                    client.sendall(bytes("USERS", 'UTF-8'))

                elif command == "STATUS":
                    if len(split_out) == 1:
                        client.sendall(bytes("STATUS DEFAULT", 'UTF-8'))
                    elif len(split_out) == 2:
                        client.sendall(bytes("STATUS NEW_STATUS " + split_out[1], 'UTF-8'))
                    else:
                        ui.chatbuffer_add("Please enter a alphanumeric status by using /status <new status> command"
                                          , RED_COLOR)

                # /r
                elif command == "R":
                    if len(split_out) < 3:
                        ui.chatbuffer_add("Please enter an username and a message by using /r <username> <message> "
                                          "command", RED_COLOR)
                    else:
                        msg_ = str_concatenate(split_out, 2, len(split_out))
                        client.sendall(bytes("PRIVATE " + split_out[1] + " " + msg_, 'UTF-8'))

                # /super
                elif command == "SUPER":
                    if len(split_out) == 1:
                        ui.chatbuffer_add("Please enter a message by using /super <message> command", RED_COLOR)
                    else:
                        msg_ = str_concatenate(split_out, 1, len(split_out))
                        client.sendall(bytes("SUPER " + msg_, 'UTF-8'))

                # ROOM COMMANDS
                # /room
                elif command == "ROOM":
                    if len(split_out) == 3:
                        client.sendall(bytes("ROOM " + split_out[1] + " PASSWORD " + split_out[2], 'UTF-8'))
                    elif len(split_out) == 2:
                        client.sendall(bytes("ROOM " + split_out[1] + " NO_PASSWORD", 'UTF-8'))
                    else:
                        ui.chatbuffer_add("Please use /room <room name> <password> command to join a room", RED_COLOR)

                # /list
                elif command == "LIST":
                    client.sendall(bytes("LIST", 'UTF-8'))

                # MODERATOR COMMANDS
                # /password
                elif command == "PASSWORD":
                    if len(split_out) >= 3:
                        ui.chatbuffer_add("Please enter a alphanumeric password by using /password <new password> "
                                          "command", RED_COLOR)
                    elif len(split_out) == 1:
                        client.sendall(bytes("PASSWORD REMOVE", 'UTF-8'))
                    else:
                        client.sendall(bytes("PASSWORD NEW_PASSWORD " + split_out[1], 'UTF-8'))

                # /description
                elif command == "DESCRIPTION":
                    if len(split_out) == 1:
                        client.sendall(bytes("DESCRIPTION DEFAULT", 'UTF-8'))
                    else:
                        msg_ = str_concatenate(split_out, 1, len(split_out))
                        client.sendall(bytes("DESCRIPTION NEW_DESCRIPTION " + msg_, 'UTF-8'))

                # /ban
                elif command == "BAN":

                    msg_ = str_concatenate(split_out, 2, len(split_out))
                    client.sendall(bytes("BAN " + split_out[1] + " " + msg_, 'UTF-8'))

                # /moderator
                elif command == "MODERATOR":
                    if len(split_out) == 1:
                        ui.chatbuffer_add("Please enter a username by using /moderator <username> command!"
                                          , RED_COLOR)
                    else:
                        client.sendall(bytes("MODERATOR " + split_out[1], 'UTF-8'))

                # Invalid command
                else:
                    ui.chatbuffer_add("Invalid command!", RED_COLOR)

            # Message
            else:
                client.sendall(bytes("MSG " + out_data, 'UTF-8'))


if __name__ == '__main__':
    wrapper(main)
