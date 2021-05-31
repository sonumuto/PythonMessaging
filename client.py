import socket
import threading
import time
from ui import ChatUI
from curses import wrapper

WHITE_COLOR = 253
RED_COLOR = 124
GREEN_COLOR = 35
PURPLE_COLOR = 99
YELLOW_COLOR = 220
ORANGE_COLOR = 208
PINK_COLOR = 200
DARK_PURPLE_COLOR = 219
LIGHT_BLUE_COLOR = 111
LIGHT_GREEN_COLOR = 84


def str_concatenate(list_, a, b):
    str_ = ""
    for i in range(a, b):
        str_ = str_ + list_[i] + " "
    return str_[:len(str_)-1]

def print_commands(ui: ChatUI):
    ui.chatbuffer_add(" ", PURPLE_COLOR)
    ui.chatbuffer_add("APPLICATION COMMANDS", PURPLE_COLOR)
    ui.chatbuffer_add("+\t/help : Show commands list", PURPLE_COLOR)
    ui.chatbuffer_add("+\t/quit : Quit application", PURPLE_COLOR)
    ui.chatbuffer_add("USER COMMANDS", PURPLE_COLOR)
    ui.chatbuffer_add("+\t/users : List all the users in the room", PURPLE_COLOR)
    ui.chatbuffer_add("+\t/status <new status> : Add or change status", PURPLE_COLOR)
    ui.chatbuffer_add("+\t/r <username> <message> : Send private message to the given username", PURPLE_COLOR)
    ui.chatbuffer_add("ROOM COMMANDS", PURPLE_COLOR)
    ui.chatbuffer_add("+\t/list : List all available rooms", PURPLE_COLOR)
    ui.chatbuffer_add("+\t/room <room name> : Create or join a room", PURPLE_COLOR)
    ui.chatbuffer_add("MODERATOR COMMANDS", PURPLE_COLOR)
    ui.chatbuffer_add("+\t/ban <user> <reason> : Ban user", PURPLE_COLOR)
    ui.chatbuffer_add("+\t/password <password> : Add or change password", PURPLE_COLOR)
    ui.chatbuffer_add("\t/description <new description> : Add or change description", PURPLE_COLOR)
    ui.chatbuffer_add("\t/moderator <username> : Make this user a moderator", PURPLE_COLOR)
    ui.chatbuffer_add("+\t/super <message> : Super message", PURPLE_COLOR)


def main(stdscr):
    SERVER = "127.0.0.1"
    PORT = 8286
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
            if in_[0] == "OK":
                ui.chatbuffer_add(f"Welcome back {username}", GREEN_COLOR)
                break
            else:
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
        if msg_split[0] == "QUIT":
            break

        elif msg_split[0] == "ROOM":
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[2] == "USER":
                    ui.chatbuffer_add(f"Welcome to the {msg_split[3]} room!", DARK_PURPLE_COLOR)
                elif msg_split[2] == "MODERATOR":
                    ui.chatbuffer_add(f"Welcome to the {msg_split[3]} room!", DARK_PURPLE_COLOR)
                    ui.chatbuffer_add("You are a moderator", DARK_PURPLE_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "INCORRECT_PASSWORD":
                    ui.chatbuffer_add("Incorrect password!", RED_COLOR)
                elif msg_split[2] == "PASSWORD_REQUIRED":
                    ui.chatbuffer_add("Password is required to join this room", RED_COLOR)
                    ui.chatbuffer_add(f"Please use /room <room name> <password> command to join {msg_split[3]}", RED_COLOR)
                elif msg_split[2] == "BANNED":
                    ui.chatbuffer_add("You have been banned from this room!", PINK_COLOR)
            elif msg_split[1] == "JOINED":
                ui.chatbuffer_add(f"{msg_split[2]} has joined the room.", DARK_PURPLE_COLOR)
            elif msg_split[1] == "LEFT":
                ui.chatbuffer_add(f"{msg_split[2]} has left the room.", DARK_PURPLE_COLOR)
            elif msg_split[1] == "LOGGED_IN":
                ui.chatbuffer_add(f"{msg_split[2]} has logged in.", DARK_PURPLE_COLOR)

        elif msg_split[0] == "LIST":
            for i in range(int(msg_split[1])):
                index = 3*i+2
                password = ""
                if msg_split[index+2] == "PASSWORD_REQUIRED":
                    password = "Password Required!"
                ui.chatbuffer_add(f"Room: {msg_split[index]}\tUsers: {msg_split[index+1]}\t{password}", LIGHT_BLUE_COLOR)

        elif msg_split[0] == "PASSWORD":
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[2] == "ADDED":
                    ui.chatbuffer_add("You have added a new password!", GREEN_COLOR)
                elif msg_split[2] == "CHANGED":
                    ui.chatbuffer_add("You have changed the password!", GREEN_COLOR)
                elif msg_split[2] == "REMOVED":
                    ui.chatbuffer_add("You have removed the password!", GREEN_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "NOT_MODERATOR":
                    ui.chatbuffer_add("You have to be a moderator to change the password!", RED_COLOR)
                elif msg_split[2] == "NO_PASSWORD_TO_REMOVE":
                    ui.chatbuffer_add("There is no password in this room!", RED_COLOR)
                    ui.chatbuffer_add("Please enter a alphanumeric password by using /password <new password> command", RED_COLOR)

        elif msg_split[0] == "SUPER":
            msg_ = str_concatenate(msg_split, 2, len(msg_split))
            ui.chatbuffer_add("* [" + msg_split[1] + "]: " + msg_, YELLOW_COLOR)

        elif msg_split[0] == "PRIVATE":
            msg_ = str_concatenate(msg_split, 3, len(msg_split))
            if msg_split[1] == "RECEIVER":
                ui.chatbuffer_add("> [" + msg_split[2] + "]: " + msg_, ORANGE_COLOR)
            elif msg_split[1] == "SENDER":
                ui.chatbuffer_add("< [" + msg_split[2] + "]: " + msg_, ORANGE_COLOR)
            elif msg_split[1] == "UNSUCCESSFUL":
                ui.chatbuffer_add("! [" + msg_split[2] + "]: " + msg_, RED_COLOR)
                ui.chatbuffer_add("This user does not exist!", RED_COLOR)

        elif msg_split[0] == "BAN":
            msg_ = str_concatenate(msg_split, 5, len(msg_split))
            if msg_split[1] == "USER":
                ui.chatbuffer_add(f"* [{msg_split[3]}]: You have been banned from {msg_split[4]} room! Reason: {msg_}", PINK_COLOR)
            elif msg_split[1] == "SUCCESSFUL":
                ui.chatbuffer_add(f"* [{msg_split[3]}]: {msg_split[2]} has been banned! Reason: {msg_}", PINK_COLOR)
            elif msg_split[1] == "NOT_MODERATOR":
                ui.chatbuffer_add("You have to be a moderator to use this command!", RED_COLOR)
            elif msg_split[1] == "NOT_EXISTS":
                ui.chatbuffer_add("There is no such a user in this room!", RED_COLOR)
            elif msg_split[1] == "MODERATOR":
                ui.chatbuffer_add("You can't ban a moderator!", RED_COLOR)

        elif msg_split[0] == "USERS":
            ui.chatbuffer_add(f"Current Room: {msg_split[1]}\tUsers: {msg_split[2]}", LIGHT_GREEN_COLOR)
            for i in range(int(msg_split[2])):
                index = 2*i+3
                ui.chatbuffer_add(f"User: {msg_split[index]}\t\tStatus: {msg_split[index+1]}", LIGHT_GREEN_COLOR)

        elif msg_split[0] == "STATUS":
            if (msg_split[1] == "SUCCESSFUL"):
                ui.chatbuffer_add(f"You have changed your status to {msg_split[2]}!", LIGHT_GREEN_COLOR)

        elif msg_split[0] == "MSG":
            msg_ = str_concatenate(msg_split, 2, len(msg_split))
            ui.chatbuffer_add("["+msg_split[1]+"]: "+msg_, WHITE_COLOR)


def take_input(client, ui):
    while True:
        out_data = ui.wait_input()
        if out_data != "":
            split_out = out_data.split()
            if split_out[0] == "/quit":
                client.sendall(bytes("QUIT", 'UTF-8'))
                break

            elif split_out[0] == "/help":
                print_commands(ui)

            elif split_out[0] == "/list":
                client.sendall(bytes("LIST", 'UTF-8'))

            elif split_out[0] == "/room":
                if len(split_out) == 3:
                    client.sendall(bytes("ROOM "+split_out[1]+" PASSWORD "+split_out[2], 'UTF-8'))
                elif len(split_out) == 2:
                    client.sendall(bytes("ROOM "+split_out[1]+" NO_PASSWORD", 'UTF-8'))

            elif split_out[0] == "/password":
                if len(split_out) >= 3:
                    ui.chatbuffer_add("Please enter a alphanumeric password by using /password <new password> command"
                                      , RED_COLOR)
                elif len(split_out) == 1:
                    client.sendall(bytes("PASSWORD " + "REMOVE", 'UTF-8'))
                else:
                    client.sendall(bytes("PASSWORD " + "NEW " + split_out[1], 'UTF-8'))

            elif split_out[0] == "/super":
                msg_ = str_concatenate(split_out, 1, len(split_out))
                client.sendall(bytes("SUPER " + msg_, 'UTF-8'))

            elif split_out[0] == "/r":
                msg_ = str_concatenate(split_out, 2, len(split_out))
                client.sendall(bytes("PRIVATE " + split_out[1] + " " + msg_, 'UTF-8'))

            elif split_out[0] == "/ban":
                msg_ = str_concatenate(split_out, 2, len(split_out))
                client.sendall(bytes("BAN " + split_out[1] + " " + msg_, 'UTF-8'))

            elif split_out[0] == "/users":
                client.sendall(bytes("USERS", 'UTF-8'))

            elif split_out[0] == "/status":
                if len(split_out) == 1:
                    client.sendall(bytes("STATUS available", 'UTF-8'))
                elif len(split_out) == 2:
                    client.sendall(bytes("STATUS " + split_out[1], 'UTF-8'))
                else:
                    ui.chatbuffer_add("Please enter a alphanumeric status by using /status <new status> command"
                                      , RED_COLOR)

            else:
                client.sendall(bytes("MSG " + out_data, 'UTF-8'))


if __name__ == '__main__':
    wrapper(main)
