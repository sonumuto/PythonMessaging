import socket
import threading
import time
from ui import ChatUI
from curses import wrapper

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
    PORT = 8093
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    stdscr.clear()
    ui = ChatUI(stdscr)

    input_thread = threading.Thread(target=take_input, args=(client, ui,))
    output_thread = threading.Thread(target=print_output, args=(client, ui,))

    input_thread.start()
    output_thread.start()

    input_thread.join()
    output_thread.join()

    client.close()

def take_input(client, ui):
    while True:
        in_data = client.recv(1024)
        print(in_data.decode())
        in_ = in_data.decode()
        if in_ == "/quit":
            break
        elif in_ != "":
            ui.chatbuffer_add(in_)
        time.sleep(0.1)

def print_output(client, ui):
    while True:
        out_data = ui.wait_input()
        if out_data != "":
            client.sendall(bytes(out_data, 'UTF-8'))
            split_out = out_data.split()
            if split_out[0] == "/quit":
                break
            elif split_out[0] == "/help":
                print_commands(ui)
        time.sleep(0.1)


if __name__ == '__main__':

    wrapper(main)