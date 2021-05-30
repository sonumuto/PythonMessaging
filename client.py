import socket
import threading
import time
from ui import ChatUI
from curses import wrapper


def str_concatenate(list, a, b):
    str_ = ""
    for i in range(a, b):
        str_ = str_ + list[i] + " "
    return str_[:len(str_)-1]

def print_commands(ui: ChatUI):
    ui.chatbuffer_add("APPLICATION COMMANDS")
    ui.chatbuffer_add("\t/help : Show commands list")
    ui.chatbuffer_add("\t/quit : Quit application")
    ui.chatbuffer_add("USER COMMANDS")
    ui.chatbuffer_add("\t/edit <status> : Add or change status")
    ui.chatbuffer_add("\t/profile <username> : Show the profile of the given username")
    ui.chatbuffer_add("\t/r <username> : Send private message to the given username")
    ui.chatbuffer_add("ROOM COMMANDS")
    ui.chatbuffer_add("\t/list : List all available rooms")
    ui.chatbuffer_add("\t/room <room name> : Create or join a room")
    ui.chatbuffer_add("MODERATOR COMMANDS")
    ui.chatbuffer_add("\t/ban <user> : Ban user")
    ui.chatbuffer_add("\t/password <password> : Add or change password")
    ui.chatbuffer_add("\t/description <new description> : Add or change description")
    ui.chatbuffer_add("\t/moderator <username> : Make this user a moderator")
    ui.chatbuffer_add("\t/super <message> : Super message")


def main(stdscr):
    SERVER = "127.0.0.1"
    PORT = 8247
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    stdscr.clear()
    ui = ChatUI(stdscr)

    ui.chatbuffer_add("Welcome to the chat app!")
    while True:
        ui.chatbuffer_add("Please enter an username:")
        username = ui.wait_input()
        if not username.isalnum():
            ui.chatbuffer_add("Please enter an username that only contains alphanumeric characters!")
        else:
            client.sendall(bytes("NEW_USER " + username, 'UTF-8'))
            in_data = client.recv(1024)
            in_ = in_data.decode()
            in_ = in_.split()
            if in_[0] == "OK":
                ui.chatbuffer_add(f"Welcome back {username}")
                break
            else:
                ui.chatbuffer_add("Username is taken!")

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
                    ui.chatbuffer_add(f"Welcome to the {msg_split[3]} room!")
                elif msg_split[2] == "MODERATOR":
                    ui.chatbuffer_add(f"Welcome to the {msg_split[3]} room!")
                    ui.chatbuffer_add("You are a moderator")
            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "INCORRECT_PASSWORD":
                    ui.chatbuffer_add("Incorrect password!")
                elif msg_split[2] == "PASSWORD_REQUIRED":
                    ui.chatbuffer_add("Password is required to join this room")
                    ui.chatbuffer_add(f"Please use /room <room name> <password> command to join {msg_split[3]}")

        elif msg_split[0] == "LIST":
            for i in range(int(msg_split[1])):
                index = 3*i+2
                password = ""
                if msg_split[index+2] == "PASSWORD_REQUIRED":
                    password = "Password Required!"
                ui.chatbuffer_add(f"Room: {msg_split[index]}\tUsers: {msg_split[index+1]}\t{password}")

        elif msg_split[0] == "PASSWORD":
            if msg_split[1] == "SUCCESSFUL":
                if msg_split[2] == "ADDED":
                    ui.chatbuffer_add("You have added a new password!")
                elif msg_split[2] == "CHANGED":
                    ui.chatbuffer_add("You have changed the password!")
            elif msg_split[1] == "UNSUCCESSFUL":
                if msg_split[2] == "NOT_MODERATOR":
                    ui.chatbuffer_add("You have to be a moderator to change the password!")

        elif msg_split[0] == "MSG":
            msg_ = str_concatenate(msg_split, 2, len(msg_split))
            ui.chatbuffer_add("["+msg_split[1]+"]: "+msg_)
        time.sleep(0.1)


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
                else:
                    client.sendall(bytes("ROOM "+split_out[1]+" NO_PASSWORD", 'UTF-8'))

            elif split_out[0] == "/password":
                if len(split_out) == 1 or len(split_out) >= 3:
                    ui.chatbuffer_add("Please enter a alphanumeric password by using /password <new password>")
                else:
                    client.sendall(bytes("PASSWORD "+split_out[1], 'UTF-8'))

            else:
                client.sendall(bytes("MSG " + out_data, 'UTF-8'))
        time.sleep(0.1)


if __name__ == '__main__':
    wrapper(main)
