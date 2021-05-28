import socket
import threading
import curses

Users = {"admin": {"room": "", "status": ""}}
Rooms = {"lobby": {"users": [], "description": "Lobby", "moderators": [], "password": "", "permanent": True}}


class ClientThread(threading.Thread):

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print("New connection added: ", clientAddress)
        print("Active connections:", threading.active_count())

    def run(self):
        print("Connection from : ", clientAddress)
        self.csocket.send(bytes("Welcome to Chat App!!\n", 'utf-8'))
        msg = ""
        username = ""
        print(type(self.csocket))
        while True:
            self.csocket.send(bytes("Please enter an username\n", 'utf-8'))
            data = self.csocket.recv(2048)
            username = data.decode()
            if not username.isalnum():
                self.csocket.send(
                    bytes("Invalid character!\n", 'utf-8'))
                self.csocket.send(
                    bytes("Please enter an username that only contains alphanumeric characters\n", 'utf-8'))
            elif username in Users:
                self.csocket.send(
                    bytes("Username already exists!\n", 'utf-8'))
                self.csocket.send(
                    bytes("Please enter another username\n", 'utf-8'))
            else:
                Users[username] = {}
                Users[username]["status"] = "Available"
                Users[username]["room"] = "lobby"
                Rooms["lobby"]["users"].append(self.csocket)
                self.csocket.send(
                    bytes(f"Hey there {username}!\n", 'utf-8'))
                self.csocket.send(
                    bytes("Type /help to see all available commands\n", 'utf-8'))
                break

        while True:
            data = self.csocket.recv(2048)
            msg = data.decode()
            msg_split = msg.split()
            if msg == "/quit":
                self.csocket.send(
                    bytes("/quit", 'utf-8'))
            elif msg == "/help":
                continue
            elif msg_split[0] == "/edit":
                continue
            elif msg_split[0] == "/profile":
                continue
            elif msg_split[0] == "/r":
                continue
            elif msg_split[0] == "/list":
                continue
            elif msg_split[0] == "/room":
                new_room = msg_split[1]
                if new_room in Rooms or Rooms[new_room]["permanent"]:
                    if Rooms[new_room]["password"] != "":
                        self.csocket.send(bytes(f"Please enter password of the {new_room} room!\n", 'utf-8'))
                        data = self.csocket.recv(2048)
                        msg = data.decode()
                    self.csocket.send(
                        bytes(f"Welcome to the {new_room} room!\n", 'utf-8'))
                else:
                    continue
            elif msg_split[0] == "/ban":
                continue

            elif msg_split[0] == "/password":
                continue

            elif msg_split[0] == "/description":
                continue
            elif msg_split[0] == "/moderator":
                continue
            elif msg_split[0] == "/super":
                continue
            else:
                for user in Rooms[Users[username]["room"]]["users"]:
                    user.send(bytes("[" + username + "]: " + msg, 'utf-8'))

                """
                if Users[username]["room"] == "":
                    self.csocket.send(
                        bytes("Please join a room by using /room <room name> command!", 'utf-8'))
                    msg = ""
                else:
                    self.send_message("[" + username + "]: " + msg, Users[username]["room"])"""

            print("from client", msg)
            print("Client at ", clientAddress, " disconnected...")
            print("Active connections:", threading.active_count())

LOCALHOST = "127.0.0.1"
PORT = 8093
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))
print("Server started")
print("Waiting for client request..")
while True:
    server.listen(1)
    clientsock, clientAddress = server.accept()
    newthread = ClientThread(clientAddress, clientsock)
    newthread.start()
