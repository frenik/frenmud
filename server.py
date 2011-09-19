import os.path
import select       
import string
import socket
import sys
import time

# my imports
import objects
import world
import player
from constants import *

class MUDServer:
    def __init__(self):
        # if self.shutdown ever goes to True, a shutdown has been initiated.
        self.shutdown = False
        #setting up host/port tuple
        self.host = "localhost"
        self.port = 9999
        print "opening socket..."
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print "setting socket options..."
        self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        print "binding..."
        self.s.bind((self.host, self.port))
        self.s.listen(5)
        print "listening..."
        self.pList = []        
        # initialize World
        self.world = world.World()    

    def serve(self):
        print "Serving on port", self.port
        self.input = [self.s]
        self.output = [self.s]
        self.error = [self.s]
        while not self.shutdown:
            # build lists
            iList,oList,eList = select.select(self.input,self.output,
                                              self.error,0)
            for f in iList:     
                # handle server socket
                if f == self.s:
                    # accept client
                    client, address = self.s.accept()
                    # create new Player object for client
                    c = player.Player(client, address, self)                    
                    # add client to select() lists
                    self.input.append(c)
                    self.output.append(c)
                    self.error.append(c)
                    # add client to server player list
                    self.pList.append(c)
                else:
                    try:                
                        # get any data waiting for us from client
                        data = f.s.recv(1024)
                        if data: # if client sent
                            # add it to client's input buffer
                            f.appendInbuf(data)
                        else: # ?
                            print "client %d hung up" % f.s.fileno()
                            # remove from lists
                            self.input.remove(f)
                            self.output.remove(f)
                            self.error.remove(f)
                            self.pList.remove(f)
                            # close socket
                            f.s.close()
                    except socket.error, e: # socket error
                        print "client %d had error" % f.s.fileno()
                        # remove from lists
                        self.input.remove(f)
                        self.output.remove(f)
                        self.error.remove(f)
                        self.pList.remove(f)
                        # close socket
                        f.s.close()
            
            # handle output for clients ready to read
            for f in oList:
                if f == self.s:
                    # skip server socket
                    pass
                else:
                    # if we have anything to send
                    if f.outBuf:
                        # send it and clear output buffer
                        f.s.send(f.outBuf)
                        f.clearOutbuf()
            
            # trim plist, iterating over a copy so we can safely remove items
            for p in self.pList[:]: 
                if p.killed:       
                    p.s.close()
                    self.input.remove(p)
                    self.output.remove(p)
                    self.error.remove(p)
                    print 'client ("%s") killed'%p.name
                    self.pList.remove(p)   
              
            # sleep for 1/10th second, to save cpu. May need to decrease time
            # in future.
            time.sleep(0.01)
            
            # mob tick
                    
        # shut down server, main loop is over
        self.terminate()

    def terminate(self):
        # save world
        self.world.save()
    
        # loop through player list and disconnect all
        for p in self.pList:
            # save player first
            p.save()
            p.s.send("Server shutting down.")
            p.s.close()

        # close server socket
        self.s.close()
        
    def isLoggedIn(self, name):
        for p in self.pList:
            if p.name.upper()==name.upper() and p.gameState>=GS_GETPASS:
               return True
        return False
        
    def putPlayerInRoom(self,player,room):
        # makes it a little more readable
        r = self.world.rList[room]
        # tell everyone in the room that this guy has arrived
        r.printToRoom('%s phases in from the ether.\r\n'%player.name)
        # add player to room's pList
        r.pList.append(player)
        # turn player's room reference from an integer to a pointer to the object
        player.room = r
        # force player to look
        player.do_look()                              

if __name__== "__main__":
    server = MUDServer()
    try:
        server.serve()
    except KeyboardInterrupt:
        server.terminate()
        print "Keyboard Interrupt caught, shutting down..."
