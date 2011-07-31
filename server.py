import os.path
import select
import string
import socket
import sys

GS_GETNAME      = 1
GS_GETPASS      = 2
GS_GAME         = 4

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

    def do_say(self, whoSaid, sendString):
        for p in self.pList:
            if p != whoSaid:
                p.outBuf += p.name+" said, \""+sendString+"\"\r\n"
            else:
                p.outBuf += "You said, \""+sendString+"\"\r\n"

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
                    client, address = self.s.accept()
                    c = Player(client, address, self)
                    self.input.append(c)
                    self.output.append(c)
                    self.error.append(c)
                    self.pList.append(c)

                elif f == sys.stdin:
                    if sys.stdin.readline()=='q':
                        self.shutdown = True

                else:
                    try:
                        data = f.s.recv(1024)
                        if data:
                            f.appendInbuf(data)
                        else:
                            print "client %d hung up" % f.s.fileno()
                            self.input.remove(f)
                            self.output.remove(f)
                            self.error.remove(f)
                            f.s.close()
                        if f.killed:
                            print "client killed"
                            self.input.remove(f)
                            self.output.remove(f)
                            self.error.remove(f)
                            f.s.close()
                            continue
                    except socket.error, e:
                        print "client %d had error" % f.s.fileno()
                        self.input.remove(f)
                        self.output.remove(f)
                        self.error.remove(f)

            for f in oList:
                if f == self.s:
                    pass
                else:
                    if f.outBuf:
                        f.s.send(f.outBuf)
                        f.clearOutbuf()
        # shut down server, main loop is over
        self.terminate()

    def terminate(self):
        # loop through player list and disconnect all
        for p in self.pList:
            p.s.send("Server shutting down.")
            p.s.close()

        # close server socket
        self.s.close()
                        
class Player:
    def __init__(self, sock, addr, server):
        print "New connection from",addr
        self.s = sock
        self.addr = addr
        self.server = server # handle to server
        self.outBuf = "Name: "
        self.gameState = GS_GETNAME
        self.inBuf = ""
        self.killed = False
        # initialize player variables
        self.name = ""
        self.level = -1

    def appendInbuf(self, c):
        self.inBuf += c
        # not 100% why I did it this way, this has to be buggy
        if self.inBuf[-2:] == "\r\n":
            self.inBuf = self.inBuf.rstrip('\r\n')
            self.processInput()
            self.inBuf = ''
            
    def appendOutbuf(self, c):
        self.outBuf += c

    def processInput(self):
        if self.gameState == GS_GETNAME:
            self.name = self.inBuf
            # check to see if user exists
            # by checking to see if file exists for that user
            if os.path.exists("players\\"+self.name+".plr"):                
                self.outBuf = "Pass: "
                self.gameState = GS_GETPASS
            else:
                self.outBuf = "No such player. Create? (Y/n)\r\n"
                # throw them in game for now, just testing
                self.gameState = GS_GAME
                self.name = "Anon"
        elif self.gameState == GS_GETPASS:
            self.password = self.inBuf
            # attempt to load file for self.name
            # TEST code
            f = open("players\\"+self.name+".plr", "r")
            while f:
                line = f.readline()
                line = line.split(':')
                if line[0]=="Password":
                    if line[1].rstrip()==self.password:
                        self.gameState = GS_GAME
                        self.outBuf = "Welcome!\r\n\r\n"
                        self.loadPlayer(self.name)
                        return
                    else:
                        self.outBuf += "DEBUG: \""+self.password+"\":\""+line[1]+"\"\r\n"
                        self.outBuf += "Incorrect password.\r\n\r\nName: "
                        self.name = ""
                        self.password = ""
                        self.gameState = GS_GETNAME
                        return
                    f.close()
                    break                        
                    
        elif self.gameState == GS_GAME:
            # strip first word for command"
            line = self.inBuf.split(" ")
            cmd = line[0]
            # place rest of string in cmdstr
            cmdstr = string.join(line[1:])
            # upper it for consistency           
            if string.upper(cmd)=="SAY":
                server.do_say(self,cmdstr)
            elif string.upper(cmd)=="QUIT":
                self.s.send("Goodbye!\r\n")
                self.kill();
            elif string.upper(cmd)=="LEVEL":
                if self.level:
                    self.outBuf+="Your current level is "+str(self.level)+".\r\n"
                else:
                    self.outBuf+="You have no level?\r\n"
            else:
                self.outBuf += "Unrecognized command: \""+cmd+"\"\r\n"
        else:
            self.kill()

    def loadPlayer(self, name):
        # empty temporary dict to hold file variables
        settings = {}
        # open file
        f = open("players\\"+self.name+".plr", "r")
        # iterate through file
        while f:
            line = f.readline()
            # test for empty line
            if line=="": break
            line = line.rstrip('\n')            
            # comment lines start with '#', discard line and continue
            if line.find('#')==0: continue            
            # split line into key:value
            line = line.split(':')            
            # create new value to key in dict
            settings[line[0]] = line[1]
            
        # iterate through dict
        for k in settings.keys():
            if k=="Username":
                self.name = settings[k]
            elif k=="Password":
                self.password = settings[k]
            elif k=="Level":
                # store as int as required
                self.level = int(settings[k])
        
    def clearOutbuf(self):
        self.outBuf = ''

    def kill(self):
        self.killed = True

    def fileno(self):
        return self.s.fileno()

class World:
    def __init__(self):
        """ Load world from files. """
        pass
        

if __name__== "__main__":
    server = MUDServer()
    try:
        server.serve()
    except KeyboardInterrupt:
        server.terminate()
        print "Keyboard Interrupt caught, shutting down..."
