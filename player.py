from constants import *
import os
import objects
import string

class Player:        
    def __init__(self, sock, addr, server):
        ''' Initialize Player object.
        '''
        # dictionary containing commands, mapped to their functions for
        # further parsing.
        self.cmds = {'look':self.parse_look,
                'quit':self.parse_quit,
                'say':self.parse_say,
                'get':self.parse_get,
                'give':self.parse_give}
        # add long directions to self.cmds (this saved me some typing)
        for e in EXIT_STRINGS:
            self.cmds[e] = self.parse_move
        # add short directions (ex: "n", "s", etc.)
        for e in EXIT_STRINGS_SHORT:
            self.cmds[e.lower()] = self.parse_move
        # tell console we've got a connection
        print "New connection from",addr       
        self.s = sock   # s contains our socket handle
        self.addr = addr # addr contains address tuple
        self.server = server # handle to server
        self.outBuf = "Name: " # send this to player
        self.gameState = GS_GETNAME # put them in the first gamestate
        self.inBuf = "" # clear their inbuf
        self.killed = False # when killed is True, player will be disconnected
        # initialize player variables
        self.name = ""
        self.level = -1
        self.inventory = []
        self.room = None

    def appendInbuf(self, c):
        ''' Add a string to the player's input buffer, and process it if we've hit
            a newline (end of command).
            
            c: string containing the data to be appended
            
            I think the reason I did it this way was because I'm testing using 
            plain old telnet, which means as I type, commands get sent. So when
            it sends \r\n, I hit enter and it's time to process what I sent.
            ZMud works, however, so it must also send the terminator.
        '''
        self.inBuf += c
        # if we've received the terminator
        if self.inBuf[-2:] == "\r\n":
            # strip terminator
            self.inBuf = self.inBuf.rstrip('\r\n')
            # send it off to be processed
            self.processInput()
            # clear input buffer after it's been processed
            self.inBuf = ''
            
    def appendOutbuf(self, c):
        ''' I don't think this function ever gets used. It simply appends a 
            string (c) to the player's output buffer. In practice I just do it
            this way anyway inline.
        '''
        self.outBuf += c

    def processInput(self):
        ''' Process the data in the player's input buffer, depending on game state.
        '''
        # user freshly logged in, presented with Name: prompt.
        if self.gameState == GS_GETNAME:
            # set name to what's in the input buffer (could this lead to bugs?)
            self.name = self.inBuf
            # check to see if user exists
            # by checking to see if file exists for that user
            if os.path.exists("players\\"+self.name+".plr"):
                # make sure player isn't already logged in
                if self.server.isLoggedIn(self.name):
                    # player is already logged in, tell the player
                    self.outBuf = "Sorry, that player is already logged in."
                    # and kill the player
                    self.killed = True
                    # done processing. COOOOLD BLOOOODED
                    return
                # at this point, we've established that the player exists
                # and is not already logged in, so let's get a password
                self.outBuf = "Pass: "
                self.gameState = GS_GETPASS
                # and load player while we're at it
                self.loadPlayer(self.name)
            else:
                # user doesn't exist, ask if they'd like to create a character
                self.outBuf = "No such player. Create? (Y/n)\r\n"
                # put them in GS_CREATE_YN to get answer
                self.gameState = GS_CREATE_YN
        elif self.gameState == GS_CREATE_YN:
            # not yet implemented
            pass
        elif self.gameState == GS_GETPASS:            
            if self.password==self.inBuf:
                self.gameState = GS_GAME
                self.outBuf += "Welcome!\r\n\r\n"
                self.server.putPlayerInRoom(self, self.room)
            else:
                ''' I'll need to be really careful here, it could open it up to 
                    hacks. For example, I don't plan on putting "IsAdmin:False" 
                    or whatever in every single player file. If someone types in
                    my admin name, but gets a wrong password, this method will
                    set self.isAdmin to true, and never reset it. Perhaps a method
                    that fully resets all variables set by LoadPlayer() is in order
                '''
                self.outBuf += "Incorrect password.\r\n\r\nName: "
                self.name = ""
                self.password = ""
                self.gameState = GS_GETNAME 
        elif self.gameState == GS_GAME: # in game
            # parse string in input buffer to command
            parseResult = self.parse(self.inBuf)                                      
        else:
            # no valid game state, kill player
            # this should be treated as an error, as it shouldn't happen.
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
        if target:
            lookStr += target.lookStr
            pass
        else:        
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
        # make sure there's actually an exit that way.
        if self.room:
            if not self.room.exits[dir]:
                self.outBuf += "There's no exit there.\r\n"
                return
            
        # otherwise do the moving crap   
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
        if arg:
            ''' I have a feeling that this code is going to need to be moved
                to its own method. Something like findObjectInRoom(string)
                that returns an object, or the string on failure. Because I'll 
                also need to find things for give and get, off the top of my head.
                The basic algorithm for matching strings is used in parsing
                the command, as well. Perhaps I could reuse all of that somehow.
                
                Food for thought.
            '''
            # attempt to find name in room that matches arg
            possibleTargs = []
            targ = None
            objList = self.room.pList[:]
            objList += self.room.mList[:]
            objList += self.room.inventory[:]
            # look through list
            for o in objList:
                # compare first letter of object's name to first letter of arg
                if arg[0]==o.name[0]:
                    # if our argument matches exactly, skip the rest of loop
                    if arg==o.name:
                        possibleTargs.append(o)
                        break
                    # doesn't match exactly, but still a possibility
                    else:
                        possibleTargs.append(o)
                            
            # if we only found one possibility
            if len(possibleTargs)==1:
                targ = possibleTargs[0]
            # if we found no possibilities, it'll take care of itself as targ == None        
            elif len(possibleTargs)==0: pass 
            # more than one possibility
            else: 
                # narrow it down somehow
                # for now just return the first possibility
                targ = possibleTargs[0]
                
            # found it yet?
            if targ:
                self.do_look(targ)
                return
            else:
                # maybe get fancy with this and use proper 'a/an' grammar later
                # example, right now:  You don't see a "apple" here.
                # might bug grammar nazis, which is fine, but why not be nice
                # to the pedantic little pricks.
                self.outBuf += "You don't see a \"%s\" here.\r\n"%arg
        else:
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