from constants import *
import os
import objects
import string

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
        self.inventory = []

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
                if self.server.isLoggedIn(self.name):
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
                self.do_quit()
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
            elif string.upper(cmd)=='DROP':
                self.do_drop(cmdstr)
            elif string.upper(cmd)=='GET':
                self.do_get(cmdstr)
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
                for r in self.server.world.rList:
                    if r.id==int(settings[k]):                   
                        self.room = int(settings[k])
            elif k=='I':
                self.inventory.append(objects.Object(self,settings[k]))
        
    def clearOutbuf(self):
        self.outBuf = ''

    def kill(self):
        self.room.removePlayerFromRoom(self,'%s has quit.\r\n'%self.name)
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
        # display objects
        for o in self.room.inventory:
            lookStr += '%s is on the ground.\r\n'%o.name
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
        
    def do_drop(self, objectstr):
        object = None
        for i in self.inventory:
            if string.upper(i.name)==string.upper(objectstr):
                object = i
         
        if object:
            self.inventory.remove(object)
            self.room.inventory.append(object)
            self.outBuf += 'You drop %s.'%object.name
            self.actionToRoom('%s drops %s.'%(self.name,object.name))
        else:
            self.outBuf += 'You don\'t have "%s".'%objectstr
        self.outBuf += '\r\n'
    
    def do_get(self, objectstr):
        object = None
        for i in self.room.inventory:
            if string.upper(i.name)==string.upper(objectstr):
                object = i
        
        if object:
            self.room.inventory.remove(object)
            self.inventory.append(object)
            self.outBuf += 'You get %s.'%object.name
            self.actionToRoom('%s gets %s.'%(self.name, object.name))
        else:
            self.outBuf += 'There is no "%s".'%objectstr
        self.outBuf += '\r\n'
        
    def do_quit(self):
        self.s.send("Goodbye!\r\n")
        self.kill();
            
    def actionToRoom(self, msg):
        for p in self.room.pList:
            if p!=self:
                p.outBuf += '%s\r\n'%msg