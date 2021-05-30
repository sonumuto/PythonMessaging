import socket
import threading

Users = {"admin": {"room": "", "status": ""}}
Rooms = {"lobby": {"users": [], "description": "Lobby", "moderators": [], "password": "", "permanent": True}}


def str_concatenate(list_, a, b):
    str_ = ""
    for i in range(a, b):
        str_ = str_ + list_[i] + " "
    return str_[:len(str_) - 1]


class ClientThread(threading.Thread):

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print("New connection added: ", clientAddress)
        print("Active connections:", threading.active_count())

    def run(self):
        print("Connection from : ", clientAddress)
        msg = ""
        current_room = ""
        username = "new_user"

        while True:
            data = self.csocket.recv(2048)
            msg = data.decode()
            print(f"From client {username}: ", msg)
            msg_split = msg.split()
            if username != "new_user":
                current_room = Users[username]["room"]

            if msg_split[0] == "NEW_USER":
                if msg_split[1] in Users:
                    print(f"Taken username {msg_split[1]}")
                    self.csocket.send(bytes("ERROR USERNAME_TAKEN", 'UTF-8'))
                else:
                    username = msg_split[1]
                    Users[username] = {}
                    Users[username]["status"] = "available"
                    Users[username]["room"] = "lobby"
                    Rooms["lobby"]["users"].append(self.csocket)
                    print(f"New user created {username}")
                    self.csocket.send(bytes("OK", 'UTF-8'))

            elif msg_split[0] == "QUIT":
                print(f"{username} has left the app")
                self.csocket.send(bytes("QUIT", 'UTF-8'))
                Rooms[Users[username]["room"]]["users"].remove(self.csocket)
                Users.pop(username, None)
                break

            elif msg_split[0] == "ROOM":
                if msg_split[1] in Rooms:
                    if (msg_split[2] == "PASSWORD" and msg_split[3] == Rooms[msg_split[1]]["password"]) \
                            or Rooms[msg_split[1]]["password"] == "":
                        Rooms[current_room]["users"].remove(self.csocket)
                        if len(Rooms[current_room]["users"]) == 0 and not Rooms[current_room]["permanent"]:
                            Rooms.pop(current_room, None)
                        Rooms[msg_split[1]]["users"].append(self.csocket)
                        Users[username]["room"] = msg_split[1]
                        print(f"User successfully joined {msg_split[1]}")
                        self.csocket.send(bytes("ROOM SUCCESSFUL USER " + msg_split[1], 'UTF-8'))

                    elif msg_split[2] == "NO_PASSWORD" and Rooms[msg_split[1]]["password"] != "":
                        print(f"No password entered for {msg_split[1]}")
                        self.csocket.send(bytes("ROOM UNSUCCESSFUL PASSWORD_REQUIRED " + msg_split[1], 'UTF-8'))

                    else:
                        print(f"Incorrect password for {msg_split[1]}")
                        self.csocket.send(bytes("ROOM UNSUCCESSFUL INCORRECT_PASSWORD " + msg_split[1], 'UTF-8'))

                else:
                    Rooms[current_room]["users"].remove(self.csocket)
                    if len(Rooms[current_room]["users"]) == 1 and not Rooms[current_room]["permanent"]:
                        Rooms.pop(current_room, None)
                    Users[username]["room"] = msg_split[1]
                    Rooms[msg_split[1]] = {}
                    Rooms[msg_split[1]]["users"] = [self.csocket]
                    Rooms[msg_split[1]]["password"] = ""
                    Rooms[msg_split[1]]["description"] = ""
                    Rooms[msg_split[1]]["moderators"] = [username]
                    Rooms[msg_split[1]]["permanent"] = False
                    print(f"User successfully joined {msg_split[1]} as a moderator")
                    self.csocket.send(bytes("ROOM SUCCESSFUL MODERATOR " + msg_split[1], 'UTF-8'))

            elif msg_split[0] == "LIST":
                out_ = "LIST " + str(len(Rooms))
                for room in Rooms:
                    password = "PASSWORD_REQUIRED"
                    if Rooms[room]["password"] == "":
                        password = "NO_PASSWORD"
                    out_ = out_ + " " + room + " " + str(len(Rooms[room]["users"])) + " " + password
                print("List room", out_)
                self.csocket.send(bytes(out_, 'UTF-8'))

            elif msg_split[0] == "PASSWORD":
                if username in Rooms[current_room]["moderators"]:
                    if Rooms[current_room]["password"] == "":
                        self.csocket.send(bytes("PASSWORD SUCCESSFUL ADDED", 'UTF-8'))
                    else:
                        self.csocket.send(bytes("PASSWORD SUCCESSFUL CHANGED", 'UTF-8'))
                    Rooms[current_room]["password"] = msg_split[1]
                else:
                    self.csocket.send(bytes("PASSWORD UNSUCCESSFUL NOT_MODERATOR", 'UTF-8'))

            elif msg_split[0] == "MSG":
                for user in Rooms[Users[username]["room"]]["users"]:
                    msg_ = str_concatenate(msg_split, 1, len(msg_split))
                    user.send(bytes("MSG " + username + " " + msg_, 'UTF-8'))

        print("Active connections:", threading.active_count())


LOCALHOST = "127.0.0.1"
PORT = 8247
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
