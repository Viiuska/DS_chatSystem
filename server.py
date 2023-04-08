# https://github.com/xysun/pychat  
# https://github.com/sidjee/PyRooms/blob/master/server.py 
# https://github.com/Eisah-Jones/MultiRoom-Chat/blob/master/Multi-Room%20Chat/Multi_Chat_Server.py  

from socket import *
import threading
import atexit
import time

# 127.0.0.1 IP address


class Client():

    # Information from the GUI
    def __init__(self, name, connection, address, room):
        self._clientName = name
        self._clientSocket = connection
        self._clientAddress = address
        self._currentRoom = room
        self._currentRoom.add_client(self)
        self._exists = True

        # Handles Thread for client
        receivingThread = threading.Thread(target=self._receive_from_client)
        receivingThread.start()

    # Check the room  and adds client to it
    def set_room(self, room):
        if not self._currentRoom == None:
            self._currentRoom.remove_client(self)

        if type(room) == int:
            room = eval(
                "eval('self._currentRoom.get_server().ROOM{}')".format(room))
        self._currentRoom = room
        self._currentRoom.add_client(self)

    # Get the client's name from the GUI
    def get_name(self):
        return self._clientName

    # Send the message to the GUI
    def send_to_client(self, data: str):
        self._clientSocket.send(data.encode("UTF-8"))

    # Receive the message from the GUI
    def _receive_from_client(self):
        while self._exists:
            packet = self._clientSocket.recv(1024).decode("UTF-8")
            self._parse_packet(packet)

    # Handles the connections, adding and removing client from the server
    def _parse_packet(self, p: str):
        parsed = p.split(';')
        command = parsed[0]
        if command == '_message':
            self._currentRoom.send_message(
                self._clientName, ';'.join(parsed[1:]).rstrip())
        elif command == 'room':
            self.set_room(int(parsed[1]))
        elif command == 'disconnect':
            if self._exists:
                self._exists = False
                self._clientSocket.close()
                self._currentRoom.remove_client(self)
                self._currentRoom.get_server().remove_client(self)
        elif command == 'name':
            old_name = self._clientName
            self._clientName = ';'.join(parsed[1:]).rstrip()
            self._currentRoom.send_update(
                "update;--{} has changed their name to {}--".format(old_name, self._clientName))
        elif command == "update":
            self._currentRoom.send_update(';'.join(parsed[1:]).rstrip())
        elif command == '':
            if self._exists:
                self._exists = False
                self._clientSocket.close()
                self._currentRoom.remove_client(self)
                self._currentRoom.get_server().remove_client(self)

    def _send_confirmation(self, c):
        self.send_to_client(c)


# Hanles room's functions
class Room():

    # Get information
    def __init__(self, name, server):
        self._roomName = name
        self._server = server
        self._occupants = []

    # Get server from the GUI
    def get_server(self):
        return self._server

    # Get the room name
    def get_name(self):
        return self._roomName

    # Add client to the room and inform others in the room.
    def add_client(self, c):
        self._occupants.append(c)
        m = "update;" + c._clientName + " has joined the room"
        time.sleep(1)
        self.send_update(m)

    # Removing client from the room and inform others in the room
    def remove_client(self, client):
        if client in self._occupants:
            self._occupants.remove(client)
        m = "update;" + client._clientName + " has disconnected from the room"
        self.send_update(m)

    # Sends client's message to the other in the room
    def send_message(self, sender, _message):
        packet = "_message;" + sender + ': ' + _message
        for o in self._occupants:
            if not o.get_name() == sender:
                o.send_to_client(packet)

    # Print participants in the room
    def _print_occupants(self):
        if self._occupants == []:
            print("Empty")
            return
        s = ''
        for o in self._occupants:
            s += o.get_name() + ', '
        print(s[0:-2])

    # Send updates when client's leave or join
    def send_update(self, u):
        for o in self._occupants:
            o.send_to_client(u)


# Handles multiple room
class MultiChatServer():

    # Starting server up, declaring the rooms
    def __init__(self, maxClients, serverPort):
        self._maxClients = maxClients

        self._clients = []

        self.ROOM1 = Room('1', self)
        self.ROOM2 = Room('2', self)
        self.ROOM3 = Room('3', self)
        self.ROOM4 = Room('4', self)

        self._serverSocket = socket(AF_INET, SOCK_STREAM)
        self._serverPort = serverPort

    # Prints the clients in the rooms
    def print_room_clients(self):
        for r in [self.ROOM1, self.ROOM2, self.ROOM3, self.ROOM4]:
            print(r.get_name(), r._occupants)

    # Starting server up for the rooms and listening threads
    def start(self):
        self._serverSocket.bind(('', self._serverPort))
        self._serverSocket.listen(16)
        print("Server is listening on port", self._serverPort)
        listeningThread = threading.Thread(target=self._acceptConnections)
        listeningThread.start()

    # Closing the server
    def end(self):
        try:
            self._serverSocket.close()
        except:
            pass

    # Remove clients
    def remove_client(self, c):
        if c in self._clients:
            self._clients.remove(c)
        del c

    # Check if server has max people (6)
    def _serverIsFull(self):
        return self._maxClients == len(self._clients)

    # Connect client to the server and checking the server is not full
    def _acceptConnections(self):
        while True:
            if not self._serverIsFull():
                connectionSocket, addr = self._serverSocket.accept()
                new_client = Client("Client{}".format(
                    len(self._clients)+1), connectionSocket, addr, self.ROOM1)
                self._clients.append(new_client)
                self._clients[-1].send_to_client(
                    '1;{}'.format(new_client.get_name()))
            else:
                connectionSocket, addr = self._serverSocket.accept()
                connectionSocket.send("error;Server is full".decode("UTF-8"))
                connectionSocket.close()


if __name__ == "__main__":
    maxClients = 6
    serverPort = 5000
    server = MultiChatServer(maxClients, serverPort)
    server.start()
    atexit.register(server.end)
