import os.path
import select
import string
import socket
import sys
import time
import objects

GS_GETNAME      = 1
GS_GETPASS      = 2
GS_GAME         = 4

EXIT_STRINGS = ['north','northeast','east','southeast','south',
                'southwest','west','northwest','up','down']
EXIT_STRINGS_SHORT = ['N','NE','E','SE','S','SW','W','NW','U','D']

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
        self.world = World()    

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
            
            # trim plist, iterating over a copy so we can safely remove items
            for p in self.pList[:]: 
                if p.killed:       
                    p.s.close()
                    self.input.remove(p)
                    self.output.remove(p)
                    self.error.remove(p)
                    print 'client ("%s") killed'%p.name
                    self.pList.remove(p)   
                    
            time.sleep(0.1)
                    
        # shut down server, main loop is over
        self.terminate()

    def terminate(self):
        # loop through player list and disconnect all
        for p in self.pList:
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
                # make sure player isn't already logged in
                if server.isLoggedIn(self.name):
                    self.outBuf = "Sorry, that player is already logged in."
                    self.kill()
                    return
                self.outBuf = "Pass: "
                self.gameState = GS_GETPASS
            else:
                self.outBuf = "No such player. Create? (Y/n)\r\n"
                # throw them in game for now, just testing
                self.gameState = GS_GAME
                self.name = "Anon"
                self.outBuf = "Welcome!\r\n\r\n"                
                self.room = 0
                self.server.putPlayerInRoom(self, self.room)
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
                        self.server.putPlayerInRoom(self,self.room)
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
            # PARSING BEGINS HERE, SPLIT
            # strip first word for command"
            line = self.inBuf.split(" ")
            cmd = line[0]
            # place rest of string in cmdstr
            cmdstr = string.join(line[1:])
            # upper it for consistency           
            if string.upper(cmd)=="SAY":
                self.do_say(cmdstr)
            elif string.upper(cmd)=="QUIT":
                self.s.send("Goodbye!\r\n")
                self.kill();
            elif string.upper(cmd)=="LEVEL":
                if self.level:
                    self.outBuf+="Your current level is "+str(self.level)+".\r\n"
                else:
                    self.outBuf+="You have no level?\r\n"
            elif string.upper(cmd)=="L":
                self.do_look()
            elif string.upper(cmd)=='N':
                self.move(0)
            elif string.upper(cmd)=='NE':
                self.move(1)
            elif string.upper(cmd)=='E':
                self.move(2)
            elif string.upper(cmd)=='SE':
                self.move(3)
            elif string.upper(cmd)=='S':
                self.move(4)
            elif string.upper(cmd)=='SW':
                self.move(5)
            elif string.upper(cmd)=='W':
                self.move(6)
            elif string.upper(cmd)=='NW':
                self.move(7)
            elif string.upper(cmd)=='U':
                self.move(8)
            elif string.upper(cmd)=='D':
                self.move(9)
            elif string.upper(cmd)=='INV':
                self.do_inventory()
            elif len(cmd)==0:
                return
            else:
                self.outBuf += "Unrecognized command: \""+cmd+"\"\r\n"
        else:
            self.kill()

    def loadPlayer(self, name):
        # inventory
        self.inventory = []

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
            elif k=="Room":
                print settings[k]
                for r in self.server.world.rList:
                    if r.id==int(settings[k]):                   
                        self.room = int(settings[k])
        
        # TEMP: add a "sword" to inventory
        self.inventory.append(objects.Object(self,1,'Sword'))
        
    def clearOutbuf(self):
        self.outBuf = ''

    def kill(self):
        self.killed = True

    def fileno(self):
        return self.s.fileno()
        
    def do_look(self):
        lookStr = ''
        # get title (& id for now, later make this admin only)
        lookStr += '%s (%i)\r\n'%(self.room.title, self.room.id)
        # get description
        lookStr += '%s\r\n'%self.room.desc
        # get exits
        lookStr += 'Exits: '
        eFound = False
        for i in range(10):
            if self.room.exits[i] != None:
                if eFound:
                    lookStr += ', '
                lookStr += '%s'%EXIT_STRINGS_SHORT[i]
                eFound = True
        lookStr += '\r\n'
        # display players
        for p in self.room.pList:
            if p!=self:
                lookStr += '%s is here.\r\n'%p.name
        lookStr += '\r\n'
        self.outBuf += lookStr
      
    def do_say(self, sendString):
        for p in self.room.pList:
            if p != self:
                p.outBuf += self.name+" said, \""+sendString+"\"\r\n"
        self.outBuf += "You said, \""+sendString+"\"\r\n"
        
    def move(self, dir):
        self.room.removePlayerFromRoom(self,
            '%s walks to the %s.\r\n'%(self.name,EXIT_STRINGS[dir]))
        self.room = self.room.exits[dir]
        self.room.addPlayerToRoom(self,'%s walks in.'%self.name)
        self.outBuf += 'You walk %s.\r\n'%EXIT_STRINGS[dir]
        self.do_look()
        
    def do_inventory(self):
        self.outBuf += 'Inventory:\r\n'
        if self.inventory == []:
            self.outBuf += 'None\r\n'
        else:
            for i in self.inventory:
                self.outBuf += '%s\r\n'%i.name
        self.outBuf += '\r\n'

class World:
    def __init__(self):
        """ Load world from files. """
        self.rList = []
        
        # open all files in directory world/rooms/
        files = os.listdir('world\\rooms\\')
        
        # find highest room number and create self.rList with that many slots
        highNum = 1
        for f in files:
            num = f.split('.')
            if int(num[0]) > highNum:
                highNum = int(num[0])
        self.rList = [0]*(highNum+1)
    
        for f in files:
            currfile = open('world\\rooms\\%s'%f,'r')
            settings = {}
            id = None
            title = None 
            desc = None
            exits = [None]*10
            while currfile:
                line = currfile.readline()
                if line=='': break
                line = line.rstrip('\n')
                if line.find('#')==0: continue
                line = line.split(':')
                settings[line[0]] = line[1]
            for k in settings.keys():
                if k=='ID':
                    id = int(settings[k])
                elif k=='Title':
                    title = settings[k]
                elif k=='Desc':
                    desc = settings[k]
                elif k=='N':
                    exits[0] = int(settings[k])
                elif k=='NE':
                    exits[1] = int(settings[k])
                elif k=='E':
                    exits[2] = int(settings[k])
                elif k=='SE':
                    exits[3] = int(settings[k])
                elif k=='S':
                    exits[4] = int(settings[k])
                elif k=='SW':
                    exits[5] = int(settings[k])
                elif k=='W':
                    exits[6] = int(settings[k])
                elif k=='NW':
                    exits[7] = int(settings[k])
                elif k=='U':
                    exits[8] = int(settings[k])
                elif k=='D':
                    exits[9] = int(settings[k])
            r = Room(id,title,desc,exits)
            self.rList[id] = r
        
        # loop through rooms and turn exit ints into room links
        for r in self.rList:
            # loop through exits in room
            for e in range(len(r.exits)):
                # if room has an exit
                if r.exits[e] != None:
                    # loop through room list again
                    for t in self.rList:
                        # if current room id == exit int
                        if t.id==r.exits[e]:
                            # set exit to room object
                            r.exits[e] = t

class Room:
    def __init__(self, id, title, desc, exits):
        self.id = id
        self.title = title
        self.desc = desc
        self.exits = exits
        self.pList = []
    
    def printToRoom(self,message):
        for p in self.pList:
            p.outBuf += message       
    
    def removePlayerFromRoom(self,player,message):
        self.pList.remove(player)
        for p in self.pList:
            p.outBuf += message
        
    def addPlayerToRoom(self, player, message):
        for p in self.pList:
            p.outBuf += message
        self.pList.append(player)

if __name__== "__main__":
    server = MUDServer()
    try:
        server.serve()
    except KeyboardInterrupt:
        server.terminate()
        print "Keyboard Interrupt caught, shutting down..."
