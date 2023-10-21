import asyncio
import json
import argparse
from datetime import datetime

class ChatServerProtocol(asyncio.Protocol):
    def __init__(self, connections, chatrooms):
        self.connections = connections
        self.chatrooms = chatrooms
        self.user = None
        self.chatroom = None
        self.peername = None 

    def connection_made(self, transport):
        self.transport = transport
        self.peername = transport.get_extra_info('peername')

    def connection_lost(self, exc):
        if self.user:
            self.leave_chatroom()
        if self.transport in self.connections:
            self.connections.remove(self.transport)
            print('{} disconnected'.format(self.peername))
            self.peername = None

    def connection_lost(self, exc):
     if self.transport in self.connections:
        self.connections.remove(self.transport)
     if self.user:
        self.leave_chatroom()

     err = "{}:{} disconnected".format(*self.peername)
     message = self.make_msg(err, "[Server]", "servermsg")
     print(err)
     for connection in self.connections:
        connection.write(message)

    def data_received(self, data):
        if not self.user:
            user = data.decode().strip()
            self.user = user
            self.transport.write(self.make_msg("Connected as {}.".format(user), "[Server]", "servermsg"))
        else:
            message = data.decode().strip()
            if message.startswith('/join '):
                chatroom_name = message[6:]
                self.join_chatroom(chatroom_name)
                print("{} connected to chatroom with the name of {}".format(self.user,chatroom_name))
            else:
                if self.chatroom:
                    self.send_to_chatroom(message)
                else:
                    self.transport.write(self.make_msg("You need to join a chatroom first.", "[Server]", "servermsg"))

    def join_chatroom(self, chatroom_name):
        if chatroom_name not in self.chatrooms:
            self.chatrooms[chatroom_name] = set()
        if self.chatroom:
            self.leave_chatroom()
        self.chatroom = chatroom_name
        self.chatrooms[chatroom_name].add(self.transport)
        self.transport.write(self.make_msg("Joined chatroom: {}".format(chatroom_name), "[Server]", "servermsg"))

    def leave_chatroom(self):
        if self.chatroom and self.transport in self.chatrooms[self.chatroom]:
            self.chatrooms[self.chatroom].remove(self.transport)
            self.transport.write(self.make_msg("Left chatroom: {}".format(self.chatroom), "[Server]", "servermsg"))
            self.chatroom = None

    def send_to_chatroom(self, message):
        if self.chatroom:
            author = self.user
            timestamp = datetime.utcnow().strftime("%H:%M:%S")
            msg = self.make_msg(message, author, "message")
            for connection in self.chatrooms[self.chatroom]:
                connection.write(msg)

    def make_msg(self, message, author, event="message"):
        msg = {
            "content": message,
            "author": author,
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "event": event
        }
        return json.dumps(msg).encode()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Server settings")
    parser.add_argument("--addr", default="127.0.0.1", type=str)
    parser.add_argument("--port", default=50000, type=int)
    args = vars(parser.parse_args())

    connections = []
    chatrooms = {}

    loop = asyncio.get_event_loop_policy().new_event_loop()
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)

    coro = loop.create_server(lambda: ChatServerProtocol(connections, chatrooms), args["addr"], args["port"])
    server = loop.run_until_complete(coro)

    print('Serving on {}:{}'.format(args["addr"], args["port"]))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()









