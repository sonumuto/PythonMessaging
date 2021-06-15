import socket
import threading
from typing import Optional, Union, Dict

LOCALHOST = "127.0.0.1"
PORT = 8301

Users: Dict[str, Dict[str, Union[str, Optional[socket.socket]]]] = {"admin": {"room": "", "status": "", "socket": None}}
Rooms = {"lobby": {"users": [], "description": "Lobby", "moderators": [], "password": "", "banned": [],
                   "permanent": True}}


class ClientThread(threading.Thread):

    def __init__(self, client_address, client_socket):
        threading.Thread.__init__(self)
        self.client_address = client_address
        self.client_socket = client_socket
        self.separator = " "
        print("New connection added: ", client_address)
        print("Active connections:", threading.active_count())

    def run(self):
        print("Connection from : ", self.client_address)
        username = ""
        current_room = ""

        while True:
            # Receive and decode message from the client
            data = self.client_socket.recv(2048)
            msg = data.decode()

            if username != "":
                current_room = Users[username]["room"]
                print(f"From client {username}: ", msg)
            else:
                print("From new client: ", msg)

            msg_split = msg.split()

            if msg_split[0] == "NEW_USER":
                # Username is taken
                if msg_split[1] in Users:
                    print(f"Taken username {msg_split[1]}")
                    self.client_socket.send(bytes("NEW_USER UNSUCCESSFUL USERNAME_TAKEN", 'UTF-8'))
                else:
                    username = msg_split[1]
                    for user in Rooms["lobby"]["users"]:
                        print(f"{msg_split[1]} logged in ")
                        Users[user]["socket"].send(bytes("ROOM LOGGED_IN " + username, 'UTF-8'))

                    # Create user and initialize variables
                    current_room = "lobby"
                    Users[username] = {}
                    Users[username]["status"] = "available"
                    Users[username]["room"] = "lobby"
                    Users[username]["socket"] = self.client_socket
                    Rooms[current_room]["users"].append(username)
                    print(f"New user created {username}")
                    self.client_socket.send(bytes("NEW_USER SUCCESSFUL", 'UTF-8'))

            # APPLICATION COMMANDS
            # /quit : Quit application
            elif msg_split[0] == "QUIT":
                print(f"{username} has left the app")
                self.client_socket.send(bytes("QUIT", 'UTF-8'))
                # Remove user
                if username in Rooms[current_room]["moderators"]:
                    Rooms[current_room]["moderators"].remove(username)
                Rooms[Users[username]["room"]]["users"].remove(username)
                Users.pop(username, None)
                break

            # USER AND MESSAGE COMMANDS
            # /users : List all users in the room
            elif msg_split[0] == "USERS":
                out_ = "USERS " + current_room + " " + str(len(Rooms[current_room]["users"]))
                for user in Rooms[current_room]["users"]:
                    out_ = out_ + " " + user + " " + Users[user]["status"]
                print(f"{username}: User requested the list of users in {current_room}")
                self.client_socket.send(bytes(out_, 'UTF-8'))

            # /status <new status> : Add or change status
            elif msg_split[0] == "STATUS":
                if msg_split[1] == "DEFAULT":
                    print(f"{username}: Set status as available")
                    Users[username]["status"] = "available"
                    self.client_socket.send(bytes("STATUS SUCCESSFUL " + "available", 'UTF-8'))
                elif msg_split[1] == "NEW_STATUS":
                    print(f"{username}: Set status to {msg_split[2]}")
                    Users[username]["status"] = msg_split[2]
                    self.client_socket.send(bytes("STATUS SUCCESSFUL " + msg_split[2], 'UTF-8'))

            # /r <username> <message> : Send a private message to the given username
            elif msg_split[0] == "PRIVATE":
                msg_ = self.separator.join(msg_split[2:])
                # If receiver and sender are the same users, continue
                if msg_split[1] == username:
                    print(f"{username}: Receiver and sender are the same users")
                    continue
                # If receiver exists, find receiver and send message
                elif msg_split[1] in Users:
                    Users[msg_split[1]]["socket"].send(
                        bytes("PRIVATE  " + "RECEIVER " + username + " " + msg_, 'UTF-8'))
                    self.client_socket.send(bytes("PRIVATE " + "SENDER " + msg_split[1] + " " + msg_, 'UTF-8'))
                    print(f"{username}: Private message successfully sent to {msg_split[1]}: {msg_}")
                # If user doesn't exist, send unsuccessful message to the sender
                else:
                    print(f"{username}: {msg_split[1]} does not exist")
                    self.client_socket.send(bytes("PRIVATE " + "UNSUCCESSFUL " + msg_split[1] + " " + msg_, 'UTF-8'))

            # /super <message> : Send a message to all available users
            elif msg_split[0] == "SUPER":
                for user in Users:
                    if Users[user]["socket"] is None:
                        continue
                    msg_ = self.separator.join(msg_split[1:])
                    print(f"{username} sent super message: ", msg_,)
                    Users[user]["socket"].send(bytes("SUPER " + username + " " + msg_, 'UTF-8'))

            # ROOM COMMANDS
            # /room <room name> <password> : Create or join a room
            elif msg_split[0] == "ROOM":
                # Check if the room exists
                if msg_split[1] in Rooms:
                    if (msg_split[2] == "PASSWORD" and msg_split[3] == Rooms[msg_split[1]]["password"]) \
                            or Rooms[msg_split[1]]["password"] == "":
                        # Check if the user is banned
                        if username in Rooms[msg_split[1]]["banned"]:
                            print(f"{username}: Joining {msg_split[1]} is unsuccessful. User was banned.")
                            self.client_socket.send(bytes("ROOM UNSUCCESSFUL " + msg_split[1] + "BANNED", 'UTF-8'))
                        else:
                            # Remove user from the old room
                            if username in Rooms[current_room]["moderators"]:
                                Rooms[current_room]["moderators"].remove(username)
                            Rooms[current_room]["users"].remove(username)

                            for user in Rooms[current_room]["users"]:
                                Users[user]["socket"].send(bytes("ROOM LEFT " + username, 'UTF-8'))
                            # Remove room if there is no user left in the room and room is not permanent
                            if len(Rooms[current_room]["users"]) == 0 and not Rooms[current_room]["permanent"]:
                                Rooms.pop(current_room, None)
                            for user in Rooms[msg_split[1]]["users"]:
                                Users[user]["socket"].send(bytes("ROOM JOINED " + username, 'UTF-8'))
                            Rooms[msg_split[1]]["users"].append(username)
                            Users[username]["room"] = msg_split[1]
                            print(f"User successfully joined {msg_split[1]}")
                            if Rooms[msg_split[1]]["description"] != "":
                                self.client_socket.send(bytes("ROOM SUCCESSFUL " + msg_split[1]
                                                              + " USER DESCRIPTION "
                                                              + Rooms[msg_split[1]]["description"], 'UTF-8'))
                            else:
                                self.client_socket.send(bytes("ROOM SUCCESSFUL " + msg_split[1]
                                                              + " USER NO_DESCRIPTION", 'UTF-8'))

                    elif msg_split[2] == "NO_PASSWORD" and Rooms[msg_split[1]]["password"] != "":
                        print(f"No password entered for {msg_split[1]}")
                        self.client_socket.send(bytes("ROOM UNSUCCESSFUL " + msg_split[1] + " PASSWORD_REQUIRED",
                                                      'UTF-8'))
                    else:
                        print(f"Incorrect password for {msg_split[1]}")
                        self.client_socket.send(bytes("ROOM UNSUCCESSFUL " + msg_split[1] + " INCORRECT_PASSWORD",
                                                      'UTF-8'))

                else:
                    if username in Rooms[current_room]["moderators"]:
                        Rooms[current_room]["moderators"].remove(username)
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
                    self.client_socket.send(bytes("ROOM SUCCESSFUL " + msg_split[1] + " MODERATOR", 'UTF-8'))

            # /list : List all available rooms
            elif msg_split[0] == "LIST":
                out_ = "LIST " + str(len(Rooms))
                for room in Rooms:
                    password = "PASSWORD_REQUIRED"
                    if Rooms[room]["password"] == "":
                        password = "NO_PASSWORD"
                    out_ = out_ + " " + room + " " + str(len(Rooms[room]["users"])) + " " + password
                print("List room", out_)
                self.client_socket.send(bytes(out_, 'UTF-8'))

            # MODERATOR COMMANDS
            # /password <password> : Add or change password
            elif msg_split[0] == "PASSWORD":
                if username in Rooms[current_room]["moderators"]:
                    if msg_split[1] == "NEW_PASSWORD":
                        if Rooms[current_room]["password"] == "":
                            self.client_socket.send(bytes("PASSWORD SUCCESSFUL ADDED", 'UTF-8'))
                        else:
                            self.client_socket.send(bytes("PASSWORD SUCCESSFUL CHANGED", 'UTF-8'))
                        Rooms[current_room]["password"] = msg_split[2]
                    elif msg_split[1] == "REMOVE":
                        if Rooms[current_room]["password"] == "":
                            self.client_socket.send(bytes("PASSWORD UNSUCCESSFUL NO_PASSWORD_TO_REMOVE", 'UTF-8'))
                        else:
                            Rooms[current_room]["password"] = ""
                            self.client_socket.send(bytes("PASSWORD SUCCESSFUL REMOVED", 'UTF-8'))
                else:
                    self.client_socket.send(bytes("PASSWORD UNSUCCESSFUL NOT_MODERATOR", 'UTF-8'))

            # /description <new description> : Add or change description
            elif msg_split[0] == "DESCRIPTION":
                if username in Rooms[current_room]["moderators"]:
                    if msg_split[1] == "DEFAULT":
                        Rooms[current_room]["description"] = ""
                    elif msg_split[1] == "NEW_DESCRIPTION":
                        msg_ = self.separator.join(msg_split[2:])
                        Rooms[current_room]["description"] = msg_
                        if Rooms[current_room]["description"] == "":
                            msg_ = "DESCRIPTION SUCCESSFUL ADDED " + username + " " + msg_
                        else:
                            msg_ = "DESCRIPTION SUCCESSFUL CHANGED " + username + " " + msg_
                        for user in Rooms[current_room]["users"]:
                            Users[user]["socket"].send(bytes(msg_, 'UTF-8'))

            # /ban <user> <reason> : Ban user
            elif msg_split[0] == "BAN":
                msg_ = self.separator.join(msg_split[2:])
                if msg_split[1] in Rooms[current_room]["users"]:
                    if username in Rooms[current_room]["moderators"]:
                        if msg_split[1] in Rooms[current_room]["moderators"]:
                            self.client_socket.send(bytes("BAN UNSUCCESSFUL RECEIVER_MODERATOR", 'UTF-8'))
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
                        self.client_socket.send(bytes("BAN UNSUCCESSFUL SENDER_NOT_MODERATOR", 'UTF-8'))
                else:
                    self.client_socket.send(bytes("BAN UNSUCCESSFUL NOT_EXISTS", 'UTF-8'))

            # /moderator <username> : Make user a moderator
            elif msg_split[0] == "MODERATOR":
                if username not in Rooms[current_room]["moderators"]:
                    self.client_socket.send(bytes("MODERATOR UNSUCCESSFUL NOT_MODERATOR", 'UTF-8'))
                elif msg_split[1] not in Rooms[current_room]["users"]:
                    self.client_socket.send(bytes("MODERATOR UNSUCCESSFUL NOT_EXIST", 'UTF-8'))
                elif msg_split[1] in Rooms[current_room]["moderators"]:
                    self.client_socket.send(bytes("MODERATOR UNSUCCESSFUL ALREADY_MODERATOR", 'UTF-8'))
                else:
                    for user in Rooms[current_room]["users"]:
                        Users[user]["socket"].send(bytes("MODERATOR SUCCESSFUL OTHERS " + username + " "
                                                         + msg_split[1], 'UTF-8'))
                        Users[user]["socket"].send(bytes("MODERATOR SUCCESSFUL RECEIVER " + username, 'UTF-8'))

            # Message
            elif msg_split[0] == "MSG":
                for user in Rooms[current_room]["users"]:
                    msg_ = self.separator.join(msg_split[1:])
                    Users[user]["socket"].send(bytes("MSG " + username + " " + msg_, 'UTF-8'))

        print("Active connections:", threading.active_count())


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))
print("Server started")
print("Waiting for client request..")
while True:
    server.listen(1)
    new_client_socket, new_client_address = server.accept()
    new_thread = ClientThread(new_client_address, new_client_socket)
    new_thread.start()
