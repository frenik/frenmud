from constants import *
import os
import objects
import string

class Player:        
    def __init__(self, sock, addr, server):
        self.cmds = {'look':self.parse_look,
                'quit':self.parse_quit,
                'say':self.parse_say,
                'get':self.parse_get,
                'give':self.parse_give}

        for e in EXIT_STRINGS:
            self.cmds[e] = self.parse_move
        for e in EXIT_STRINGS_SHORT:
            self.cmds[e.lower()] = self.parse_move
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
                self.kill()
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
            # parse string in input buffer to command
            parseResult = self.parse(self.inBuf)
                                        
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
        f.close()
        
    def clearOutbuf(self):
        self.outBuf = ''

    def kill(self):
        try:
            self.room.removePlayerFromRoom(self,'%s has quit.\r\n'%self.name)
        except:
            pass
        self.killed = True

    def fileno(self):
        return self.s.fileno()
        
    def do_look(self,target=None):
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
        # display mobs
        for m in self.room.mList:
            lookStr += '%s is here.\r\n'%m.displayName
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
        print dir
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
        self.save()
        self.s.send("Goodbye!\r\n")
        self.kill();
        
    def save(self):            
        # open file
        f = open("players\\"+self.name+".plr", "w")
        
        # write hard settings
        f.write('Username:%s\n'%self.name)
        f.write('Password:%s\n'%self.password)
        f.write('Level:%i\n'%self.level)
        f.write('Room:%i\n'%self.room.id)
        
        # loop through inventory
        for i in self.inventory:
            # write to file
            f.write('I:%i\n'%i.id)
            # save object
            i.save()
            
        f.close()
        print 'User saved.'
            
    def actionToRoom(self, msg):
        for p in self.room.pList:
            if p!=self:
                p.outBuf += '%s\r\n'%msg
                
    def parse_look(self, arg):
        self.do_look()
        
    def parse_quit(self, arg):
        self.do_quit()
        
    def parse_say(self, arg):
        self.do_say(arg)
        
    def parse_get(self, arg):
        self.do_get(arg)
        
    def parse_give(self, arg):
        self.outBuf += 'Sorry, "give" command not implemented yet.\r\n'
        
    def parse_move(self, arg):
        self.move(arg)
            
    def parse(self, line):
        # strip whitespace from ends
        line = line.strip()
        # count spaces
        spaces = line.count(' ')
        if not spaces:
            first = line
            arg = None
        else:
            # grab the first word, convert to lowercase
            line = line.split(' ',1)
            first = line[0].lower()
            arg = line[1]
        
        # init some variables
        possibleCmds = []
        cmd = None
        
        # loop through command list
        for c in self.cmds:
            # does our current command's first letter match the given word's?
            if first[0]==c[0]:
                # if the words match entirely, we've found our command, shortcut
                if first==c:
                    cmd = c
                    break # get out of loop, we're done
                # only add it if it's equal to or shorter in length than the cmd
                elif len(first)<=len(c):
                    possibleCmds.append(c)                
        # At this point we have either a list of possible commands, or
        # have found the command itself. 
        # If we've found it, possibleCmds will have only one element.
        if not cmd:
            if len(possibleCmds)==1:
                cmd = possibleCmds[0]

        # if we still haven't found it...
        if not cmd:
            # attempt to narrow down possibleCmds by comparing 
            # successive letters, starting at [1].
            for i in range(1,len(first)):
                for p in possibleCmds[:]:
                    if first[i] != p[i]:
                        # if we run into a letter that doesn't match, remove it
                        # as a possibility
                        possibleCmds.remove(p)            
                # this will be True if we only have one possibility
                if len(possibleCmds)==1: 
                    cmd = possibleCmds[0]
                    break
        
        # still haven't found it, possibleCmds is 2+ or 0
        if not cmd:
            print possibleCmds
            # too many possibilities to decide
            if len(possibleCmds)>1:
                return possibleCmds
            # no possibilities left
            elif not len(possibleCmds):
                return first
        
        # we've found it here, otherwise we'd already have returned.
        # see if it's a direction...
        if EXIT_STRINGS.count(cmd):
            print EXIT_STRINGS.count(cmd)
            try:
                pos = EXIT_STRINGS.index(cmd)
                # sends the number of the direction as the arg instead
                self.cmds[cmd](pos)            
            except:
                pass
        elif EXIT_STRINGS_SHORT.count(cmd.upper()):
            try:
                pos = EXIT_STRINGS_SHORT.index(cmd.upper())
                # sends the number of the direction as the arg instead
                self.cmds[cmd](pos)
            except:
                pass
        # send the argument to the function specified in the dictionary.
        else:
            self.cmds[cmd](arg)