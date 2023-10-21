
import asyncio
import json
import argparse
import tkinter as tk

class ChatClientProtocol(asyncio.Protocol):
    def __init__(self, loop, user):
        self.user = user
        #self.chatroom = chatroom
        self.loop = loop
        self.is_open = False
        self.last_message = ""
        
    def connection_made(self, transport):
        self.sockname = transport.get_extra_info("sockname")
        self.transport = transport
        self.transport.write(self.user.encode())
        #self.transport.write(("/join " + self.chatroom).encode())
        self.is_open = True
        
    def connection_lost(self, exc):
        self.is_open = False
        self.loop.stop()

    def data_received(self, data):
        while not hasattr(self, "output"):  # Wait until output is established
            pass
        if data:
            message = json.loads(data.decode())
            self.process_message(message)

    def process_message(self, message):
        try:
            if message["event"] == "message":
                content = "{timestamp} | {author}: {content}".format(**message)
            elif message["event"] == "servermsg":
                content = "{timestamp} | {author} {content}".format(**message)
            else:
                content = "{timestamp} | {author}: {content}".format(**message)
            
            self.output(content.strip() + '\n')
        except KeyError:
            print("Malformed message, skipping")

    def send(self, data):
        if data and self.user:
            self.last_message = "{author}: {content}".format(author=self.user, content=data)
            self.transport.write(data.encode())
            
    async def getmsgs(self, loop):
        self.output = self.stdoutput
        self.output("Connected to {0}:{1}\n".format(*self.sockname))
        while True:
            msg = await loop.run_in_executor(None, input, "{}: ".format(self.user))  # Get stdout input forever
            self.send(msg)

    async def getgui(self, loop):
        def executor():
            while not self.is_open:
                pass
            self.gui = Gui(None, self)
            self.output = self.tkoutput  # Set client output to tk window
            self.output("Connected to {0}:{1}\n".format(*self.sockname))
            self.gui.mainloop()
            self.transport.close()  # If the window is closed, close the connection
            self.loop.stop()

        await loop.run_in_executor(None, executor)  # Run GUI in executor for simultaneity

    def stdoutput(self, data):
        if self.last_message.strip() == data.strip():
            return  # Unclogs stdout with duplicate messages (sent and received)
        else:
            print(data.strip())

    def tkoutput(self, data):
        print(data)
        return self.gui.text1.insert(1.0, data)
    
class Gui(tk.Tk):
    """GUI for chat client. Two labels and exit button at the top,
    then single-line text entry and Send button for user, finally
    multiple-line text box to receive messages
    from chat server."""
    
    def __init__(self, parent, client):
        """Gui constructor"""
        tk.Tk.__init__(self)
        self.parent = parent
        self.client = client
        self.user = client.user
        self.initialize()

       
    def onPressEnter(self, event): 
        """Handle Enter button press the same as Send button click"""
        self.send()
    
    def send(self):
        """Send user input from client to server, then clear Entry"""
        msg = self.mytext.get()
        self.client.send(msg)
        self.mytext.set('')


    def initialize(self):
        """Initialize the GUI components"""
        self.title('Chat')
        self.minsize(350,300)
        self.maxsize(350,300)
        self.maxlines = 10  # number of lines in receive Text
      
        frame1 = tk.Frame(self)
        frame1.pack()
        handle = tk.StringVar()
        label1 = tk.Label(frame1, textvariable=handle)
        handle.set(self.user)
        button1 = tk.Button(frame1, text="Exit", command=self.destroy)
        label1.pack(side=tk.LEFT)
        button1.pack(side=tk.LEFT, padx=20)
    
        frame2 = tk.Frame(self)
        frame2.pack()
        lb2 = tk.StringVar()
        label2 = tk.Label(frame2, textvariable=lb2)
        sockname = self.client.transport.get_extra_info("sockname")
        lb2.set("{0}:{1}".format(*sockname))  #IP:port
        label2.pack()

        # Add a label for the instruction message
        frame3 = tk.Frame(self)
        frame3.pack()
        instruction_msg = tk.Label(frame3, text="Join chatroom: /join room_name")
        instruction_msg.pack()
    
        frame4 = tk.Frame(self)
        frame4.pack()
        self.mytext = tk.StringVar()
        entry1 = tk.Entry(frame4, width=40, textvariable=self.mytext)
        entry1.bind("<Return>", self.onPressEnter)  # same as Send button
        button2 = tk.Button(frame4, text="Send", command=self.send)
        entry1.pack()
        button2.pack()

        frame5 = tk.Frame(self)
        frame5.pack()
        spacer1 = tk.Label(frame5)
        self.text1 = tk.Text(frame5, width=50, height=self.maxlines)
        spacer2 = tk.Label(frame5)
        spacer1.pack()
        self.text1.pack()
        spacer2.pack()
        
        self.output = self.client.tkoutput


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client settings")
    parser.add_argument("--user", default="User", type=str)
    parser.add_argument("--addr", default="127.0.0.1", type=str)
    parser.add_argument("--port", default=50000, type=int)
    ##parser.add_argument("--chatroom", default="Default", type=str)
    parser.add_argument("--nogui", default=False, action="store_true")
    args = vars(parser.parse_args())

    loop = asyncio.get_event_loop()

    try:
        #userClient = ChatClientProtocol(loop, args["user"], args["chatroom"])
        userClient = ChatClientProtocol(loop, args["user"])
        coro = loop.create_connection(lambda: userClient, args["addr"], args["port"])

        server = loop.run_until_complete(coro)

        if args["nogui"]:
            asyncio.ensure_future(userClient.getmsgs(loop))
        else:
            asyncio.ensure_future(userClient.getgui(loop))

        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()



        

        
        

        



        

        



        

        


        

        