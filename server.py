import socket
import threading

LOCALHOST = "127.0.0.1"
PORT = 8290

Users = {"admin": {"room": "", "status": "", "socket": None}}
Rooms = {"lobby": {"users": [], "description": "Lobby", "moderators": [], "password": "", "banned": [],
                   "permanent": True}}


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
                    self.csocket.send(bytes("NEW_USER UNSUCCESSFUL USERNAME_TAKEN", 'UTF-8'))
                else:
                    username = msg_split[1]
                    for user in Rooms["lobby"]["users"]:
                        Users[user]["socket"].send(bytes("ROOM LOGGED_IN " + username, 'UTF-8'))

                    Users[username] = {}
                    Users[username]["status"] = "available"
                    Users[username]["room"] = "lobby"
                    Users[username]["socket"] = self.csocket
                    Rooms["lobby"]["users"].append(username)
                    print(f"New user created {username}")
                    self.csocket.send(bytes("NEW_USER SUCCESSFUL", 'UTF-8'))

            elif msg_split[0] == "QUIT":
                print(f"{username} has left the app")
                self.csocket.send(bytes("QUIT", 'UTF-8'))
                Rooms[Users[username]["room"]]["users"].remove(username)
                Users.pop(username, None)
                break

            elif msg_split[0] == "ROOM":
                if msg_split[1] in Rooms:
                    if (msg_split[2] == "PASSWORD" and msg_split[3] == Rooms[msg_split[1]]["password"]) \
                            or Rooms[msg_split[1]]["password"] == "":
                        if username in Rooms[msg_split[1]]["banned"]:
                            self.csocket.send(bytes("ROOM UNSUCCESSFUL " + msg_split[1] + "BANNED", 'UTF-8'))
                        else:
                            Rooms[current_room]["users"].remove(username)
                            for user in Rooms[current_room]["users"]:
                                Users[user]["socket"].send(bytes("ROOM LEFT " + username, 'UTF-8'))
                            if len(Rooms[current_room]["users"]) == 0 and not Rooms[current_room]["permanent"]:
                                Rooms.pop(current_room, None)
                            for user in Rooms[msg_split[1]]["users"]:
                                Users[user]["socket"].send(bytes("ROOM JOINED " + username, 'UTF-8'))
                            Rooms[msg_split[1]]["users"].append(username)
                            Users[username]["room"] = msg_split[1]
                            print(f"User successfully joined {msg_split[1]}")
                            if Rooms[msg_split[1]]["description"] != "":
                                self.csocket.send(bytes("ROOM SUCCESSFUL " + msg_split[1] + " USER DESCRIPTION "
                                                        + Rooms[msg_split[1]]["description"], 'UTF-8'))
                            else:
                                self.csocket.send(bytes("ROOM SUCCESSFUL " + msg_split[1]
                                                        + " USER NO_DESCRIPTION", 'UTF-8'))

                    elif msg_split[2] == "NO_PASSWORD" and Rooms[msg_split[1]]["password"] != "":
                        print(f"No password entered for {msg_split[1]}")
                        self.csocket.send(bytes("ROOM UNSUCCESSFUL " + msg_split[1] + " PASSWORD_REQUIRED", 'UTF-8'))

                    else:
                        print(f"Incorrect password for {msg_split[1]}")
                        self.csocket.send(bytes("ROOM UNSUCCESSFUL " + msg_split[1] + " INCORRECT_PASSWORD", 'UTF-8'))

                else:
                    Rooms[current_room]["users"].remove(username)
                    if len(Rooms[current_room]["users"]) == 0 and not Rooms[current_room]["permanent"]:
                        Rooms.pop(current_room, None)
                    for user in Rooms[current_room]["users"]:
                        Users[user]["socket"].send(bytes("ROOM LEFT " + username, 'UTF-8'))
                    Users[username]["room"] = msg_split[1]
                    Rooms[msg_split[1]] = {}
                    Rooms[msg_split[1]]["users"] = [username]
                    Rooms[msg_split[1]]["password"] = ""
                    Rooms[msg_split[1]]["description"] = ""
                    Rooms[msg_split[1]]["moderators"] = [username]
                    Rooms[msg_split[1]]["banned"] = []
                    Rooms[msg_split[1]]["permanent"] = False
                    print(f"User successfully joined {msg_split[1]} as a moderator")
                    self.csocket.send(bytes("ROOM SUCCESSFUL " + msg_split[1] + " MODERATOR", 'UTF-8'))

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
                    if msg_split[1] == "NEW_PASSWORD":
                        if Rooms[current_room]["password"] == "":
                            self.csocket.send(bytes("PASSWORD SUCCESSFUL ADDED", 'UTF-8'))
                        else:
                            self.csocket.send(bytes("PASSWORD SUCCESSFUL CHANGED", 'UTF-8'))
                        Rooms[current_room]["password"] = msg_split[2]
                    elif msg_split[1] == "REMOVE":
                        if Rooms[current_room]["password"] == "":
                            self.csocket.send(bytes("PASSWORD UNSUCCESSFUL NO_PASSWORD_TO_REMOVE", 'UTF-8'))
                        else:
                            Rooms[current_room]["password"] = ""
                            self.csocket.send(bytes("PASSWORD SUCCESSFUL REMOVED", 'UTF-8'))
                else:
                    self.csocket.send(bytes("PASSWORD UNSUCCESSFUL NOT_MODERATOR", 'UTF-8'))

            elif msg_split[0] == "SUPER":
                for user in Users:
                    if Users[user]["socket"] is None:
                        continue
                    msg_ = str_concatenate(msg_split, 1, len(msg_split))
                    Users[user]["socket"].send(bytes("SUPER " + username + " " + msg_, 'UTF-8'))

            elif msg_split[0] == "PRIVATE":
                msg_ = str_concatenate(msg_split, 2, len(msg_split))
                if msg_split[1] == username:
                    continue
                elif msg_split[1] in Users:
                    Users[msg_split[1]]["socket"].send(
                        bytes("PRIVATE  " + "RECEIVER " + username + " " + msg_, 'UTF-8'))
                    self.csocket.send(bytes("PRIVATE " + "SENDER " + msg_split[1] + " " + msg_, 'UTF-8'))
                else:
                    print(f"{msg_split[1]} does not exist")
                    self.csocket.send(bytes("PRIVATE " + "UNSUCCESSFUL " + msg_split[1] + " " + msg_, 'UTF-8'))

            elif msg_split[0] == "BAN":
                msg_ = str_concatenate(msg_split, 2, len(msg_split))
                if msg_split[1] in Rooms[current_room]["users"]:
                    if username in Rooms[current_room]["moderators"]:
                        if msg_split[1] in Rooms[current_room]["moderators"]:
                            self.csocket.send(bytes("BAN UNSUCCESSFUL RECEIVER_MODERATOR", 'UTF-8'))
                        else:
                            Rooms[current_room]["banned"].append(msg_split[1])
                            Users[msg_split[1]]["room"] = "lobby"
                            Rooms[current_room]["users"].remove(msg_split[1])
                            Rooms["lobby"]["users"].append(msg_split[1])
                            Users[msg_split[1]]["socket"].send(
                                bytes("BAN SUCCESSFUL RECEIVER " + msg_split[1] + " " + username + " "
                                      + current_room + " " + msg_, 'UTF-8'))
                            for user in Rooms[current_room]["users"]:
                                Users[user]["socket"].send(bytes("BAN SUCCESSFUL OTHERS " + msg_split[
                                    1] + " " + username + " " + current_room + " " + msg_, 'UTF-8'))
                    else:
                        self.csocket.send(bytes("BAN UNSUCCESSFUL SENDER_NOT_MODERATOR", 'UTF-8'))
                else:
                    self.csocket.send(bytes("BAN UNSUCCESSFUL NOT_EXISTS", 'UTF-8'))

            elif msg_split[0] == "USERS":
                out_ = "USERS " + current_room + " " + str(len(Rooms[current_room]["users"]))
                for user in Rooms[current_room]["users"]:
                    out_ = out_ + " " + user + " " + Users[user]["status"]
                print(f"Show users in {current_room}", out_)
                self.csocket.send(bytes(out_, 'UTF-8'))

            elif msg_split[0] == "STATUS":
                if msg_split[1] == "DEFAULT":
                    Users[username]["status"] = "available"
                    self.csocket.send(bytes("STATUS SUCCESSFUL " + "available", 'UTF-8'))
                elif msg_split[1] == "NEW_STATUS":
                    Users[username]["status"] = msg_split[1]
                    self.csocket.send(bytes("STATUS SUCCESSFUL " + msg_split[1], 'UTF-8'))

            elif msg_split[0] == "DESCRIPTION":
                if username in Rooms[current_room]["moderators"]:
                    if msg_split[1] == "DEFAULT":
                        Rooms[current_room]["description"] = ""
                    elif msg_split[1] == "NEW_DESCRIPTION":
                        msg_ = str_concatenate(msg_split, 2, len(msg_split))
                        Rooms[current_room]["description"] = msg_
                        if Rooms[current_room]["description"] == "":
                            msg_ = "DESCRIPTION SUCCESSFUL ADDED " + username + " " + msg_
                        else:
                            msg_ = "DESCRIPTION SUCCESSFUL CHANGED " + username + " " + msg_
                        for user in Rooms[current_room]["users"]:
                            Users[user]["socket"].send(bytes(msg_, 'UTF-8'))


            elif msg_split[0] == "MSG":
                for user in Rooms[current_room]["users"]:
                    msg_ = str_concatenate(msg_split, 1, len(msg_split))
                    Users[user]["socket"].send(bytes("MSG " + username + " " + msg_, 'UTF-8'))

        print("Active connections:", threading.active_count())


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
