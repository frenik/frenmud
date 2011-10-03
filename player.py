from constants import *
import os
import objects
import string
import files

class Player:        
    def __init__(self, sock, addr, server):
        ''' Initialize Player object.
        '''
        # dictionary containing commands, mapped to their functions for
        # further parsing. I'm putting it here so it can be added to per-player
        self.cmds = {   
                        'look':self.parse_look,
                        'quit':self.parse_quit,
                        'say':self.parse_say,
                        'get':self.parse_get,
                        'give':self.parse_give
                    }
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
        self.isAdmin = False

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
        # get dict of settings in player's file
        settings = files.loadFromFile('players\\%s.plr'%self.name)
            
        # iterate through dict
        for k in settings.keys():
            if k=="Username":
                self.name = settings[k]
            elif k=="Password":
                self.password = settings[k]
            elif k=="Level":
                # store as int as required
                self.level = int(settings[k])
            elif k=="IsAdmin":
                # turns out I couldn't just go bool(settings[k]), it always 
                # returned True (presumably because it contained _something_.
                if settings[k]=="True": self.isAdmin = True
                if settings[k]=="False": self.isAdmin = False
            elif k=="Room":
                # there may be a faster way to do this, rather than looping
                # through every single room until we find it.
                for r in self.server.world.rList:
                    if r.id==int(settings[k]):                   
                        self.room = int(settings[k])
            elif k=='I':
                # this line creates an object and appends it to the player's
                # inventory.
                self.inventory.append(objects.Object(self,settings[k]))         
        # set admin commands
        if self.isAdmin:
            self.cmds['dump'] = self.parse_dump
        
    def clearOutbuf(self):
        ''' Clears the player's output buffer. Unused as far as I can remember.
        '''
        self.outBuf = ''

    def kill(self):
        ''' Removes a player from their current room, and sets killed to true,
            which should trigger other removal processes in the main loop.
        '''
        # I don't remember why I put this in a try/except. Perhaps it was
        # throwing errors when a player was not in a room, fairly obviously. My
        # first though when looking at this block was "that could be bad if they
        # aren't in a room", but perhaps it's dealt with. If they aren't in a 
        # room, nothing needs to be done here.
        try:
            self.room.removePlayerFromRoom(self,'%s has quit.\r\n'%self.name)
        except:
            pass
        self.killed = True

    def fileno(self):
        ''' Perhaps an unnecessary function. I haven't used this, certainly. I
            forget why I included it in the first place. Consider removal.
        '''
        return self.s.fileno()
        
    def do_look(self,target=None):
        ''' If "target" is given, builds a description of the object/player/mob
            and adds it to the player's output buffer. Otherwise, looks at 
            current room.
        '''
        lookStr = ''
        # if we have a target
        if target:
            # every object should have a look string method. This is temporary,
            # in the future I would like to build custom look strings within
            # a mob/object/room/whatever. Possibilities there, and so not boring.
            lookStr += target.lookStr
        else: # no target, look at room       
            # i would like to move the bulk of this code to Room.buildLookString()
            # or something similar. But this is fine for now.
            # get title 
            lookStr += '%s'%self.room.title
            if self.isAdmin: #only see id if admin
                lookStr += '(%i)'%self.room.id
            lookStr += '\r\n' # new line
            # get description
            lookStr += '%s\r\n'%self.room.desc
            # get exits
            lookStr += 'Exits: '
            # if eFound is true after the loop, no exits were found. 
            eFound = False
            for i in range(10):
                if self.room.exits[i] != None:
                    if eFound:
                        lookStr += ', '
                    lookStr += '%s'%EXIT_STRINGS_SHORT[i]
                    eFound = True
            # no exits found, tell 'em
            if not eFound:
                lookStr += 'none'
            # down a line
            lookStr += '\r\n'
            # display players
            for p in self.room.pList:
                if p!=self: # make sure it's not the looking player
                    lookStr += '%s is here.\r\n'%p.name
            # display mobs
            for m in self.room.mList:
                lookStr += '%s is here.\r\n'%m.displayName
            # display objects
            for o in self.room.inventory:
                lookStr += '%s is on the ground.\r\n'%o.name
        # down another line
        lookStr += '\r\n'
        # send it to the output buffer
        self.outBuf += lookStr
      
    def do_say(self, sendString):
        ''' Prints a message via the say command to everyone in the room.
        '''
        # handle empty string
        if not sendString:
            self.outBuf += "Say what?\r\n"
            return
        # loop through current room's player list
        for p in self.room.pList:            
            if p != self: # it would be silly to send this to ourselves.
                p.outBuf += self.name+" said, \""+sendString+"\"\r\n"
        # gotta hear yourself, man. How else you gonna know if you said something stupid.
        self.outBuf += "You said, \""+sendString+"\"\r\n"
        
    def move(self, dir):
        ''' Attempts to move the player in the direction given by "dir", an 
            integer between 0 and 9. (See EXIT_STRINGS)
        '''
        # make sure we're in a room
        if self.room:
            # does the exit actually exist?
            if not self.room.exits[dir]:
                # tell them they're stupid.
                self.outBuf += "There's no exit there.\r\n"
                # end the function
                return
            
        # otherwise do the moving crap, starting with removing the player from
        # current room...
        self.room.removePlayerFromRoom(self,
            '%s walks to the %s.\r\n'%(self.name,EXIT_STRINGS[dir]))
        # setting the players current room to the room to dir...
        self.room = self.room.exits[dir]
        # add player to new room
        self.room.addPlayerToRoom(self,'%s walks in.'%self.name)
        # tell the player he moved successfully.
        self.outBuf += 'You walk %s.\r\n'%EXIT_STRINGS[dir]
        # take a look, it's in a book, a reading rainbooooow
        self.do_look()
        
    def do_inventory(self):
        ''' Displays to player their inventory.
        '''
        self.outBuf += 'Inventory:\r\n'
        # if inventory is empty...
        if self.inventory == []:
            # tell 'em
            self.outBuf += 'None\r\n'
        else: # has something in inventory
            # iterate through inventory
            for i in self.inventory:
                # and print the name of the object
                self.outBuf += '%s\r\n'%i.name
        # down a line
        self.outBuf += '\r\n'
        
    def do_drop(self, objectstr):
        ''' Drops an item.
        '''
        # initialize object to None for future success check
        object = None
        # iterate through inventory
        for i in self.inventory:
            # if the name matches exactly, this is temporary. This is further
            # making the case for a string matching function.
            if string.upper(i.name)==string.upper(objectstr):
                # set object to the object we found.
                object = i
        # we found it
        if object:
            # remove item from inventory
            self.inventory.remove(object)
            # add item to room's inventory
            self.room.inventory.append(object)
            # print it to the player
            self.outBuf += 'You drop %s.'%object.name
            # print it to the room
            self.actionToRoom('%s drops %s.'%(self.name,object.name))
        # we didn't find it.
        else:
            self.outBuf += 'You don\'t have "%s".'%objectstr
        self.outBuf += '\r\n'
    
    def do_get(self, objectstr):
        ''' Picks up an object from the ground. Basically the same as do_drop(),
            but with some bits switched around.
        '''
        # initialize object to None for future check.
        object = None
        # iterate through inventory
        for i in self.room.inventory:
            # more literal matching, add some fuzz please
            if string.upper(i.name)==string.upper(objectstr):
                object = i
        # found it
        if object:
            # remove from room
            self.room.inventory.remove(object)
            # add to player's inventory
            self.inventory.append(object)
            # tell 'em
            self.outBuf += 'You get %s.'%object.name
            self.actionToRoom('%s gets %s.'%(self.name, object.name))
        # didn't find it
        else:
            self.outBuf += 'There is no "%s".'%objectstr
        self.outBuf += '\r\n'
        
    def do_quit(self):
        ''' Called when player issues "quit" command.
        '''
        # save player
        self.save()
        # send goodbye to client
        self.s.send("Goodbye!\r\n")
        # kill player
        self.kill()
    
    def do_dump(self):
        ''' "dump" command, initiates a full world save (ADMIN ONLY)
        '''
        # save world        
        self.server.world.save()
    
        # loop through player list and disconnect all
        for p in self.server.pList:
            # save player first
            p.save()
        
    def save(self):  
        ''' Saves player to hard drive.
        '''
        pfile = 'players\\%s.plr'%self.name
        tempPfile = pfile+'.temp'
        # make backup of old file
        try:
            os.rename(pfile, tempPfile)
        except OSError:
            print 'Error: Renaming "%s.plr" to "%s.plr.temp". Tempfile \
                already exists.'%(self.name,self.name)
            return
        
        # open new pfile
        f = open(pfile, "w")
        
        # write hard settings
        try:
            f.write('Username:%s\n'%self.name)
            f.write('Password:%s\n'%self.password)
            f.write('IsAdmin:%s\n'%str(self.isAdmin))
            f.write('Level:%i\n'%self.level)
            f.write('Room:%i\n'%self.room.id)
        except NameError:
            print 'Error: Writing user to file, a variable doesn\'t exist (stupid)!'
            
        # loop through inventory
        for i in self.inventory:
            # write to file
            f.write('I:%i\n'%i.id)
            # save object
            i.save()
            
        f.close()
        print 'User saved.'
        # clean up temp file, all went well
        os.remove(tempPfile)
            
    def actionToRoom(self, msg):
        ''' Intended to print the results of an action to the room
        '''
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
            # strip "at"
            # does arg have spaces?
            hasSpace = arg.find(' ')
            if hasSpace != -1:
                firstWord = arg[0:hasSpace]
                if firstWord.lower()=='at':
                    # strip 'at ' and lowercase the whole thing
                    arg = arg[3:].lower()
            else:
                # lowercase the whole thing for easier comparison
                arg = arg.lower()
                
            # attempt to find name in room that matches arg
            possibleTargs = []
            targ = None
            # get copy of players in room
            objList = self.room.pList[:]
            # get copy of mobs in room
            objList += self.room.mList[:]
            # get copy of items in room
            objList += self.room.inventory[:]
            # look through list
            for o in objList:
                # compare first letter of object's name to first letter of arg
                if arg[0]==o.name[0]:
                    # if our argument matches exactly, skip the rest of loop
                    if arg==o.name:
                        targ = o
                        break
                    # doesn't match exactly, but still a possibility
                    else:
                        possibleTargs.append(o)                            
            # if we found no possibilities, it'll take care of itself as 
            # targ equals either None or the an object whose name matches exactly.           
            # if we only found one possibility
            if len(possibleTargs)==1:
                targ = possibleTargs[0]             
            else: # more than one possibility
                # attempt to narrow down possibleTargs by comparing 
                # successive letters, starting at [1].
                for i in range(1,len(arg)):
                    # iterating over a copy for safe removal
                    for p in possibleTargs[:]:
                        if first[i] != p[i]:
                            # if we run into a letter that doesn't match, remove it
                            # as a possibility
                            possibleTargs.remove(p)            
                    # this will be True if we only have one possibility, so we
                    # don't loop unnecessarily
                    if len(possibleTargs)==1: 
                        targ = possibleTargs[0]
                        break
                # we've narrowed it down all we can, let's just return the first
                # possibility if we have more than one
                if len(possibleTargs)>1: targ = possibleTargs[0]
            # we've done all we could, this is the give-up point
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
        
    def parse_dump(self, arg):
        self.do_dump()
            
    def parse(self, line):
        # if user just hits enter, blank line
        if not len(line):
            return
        
        # strip whitespace from ends
        line = line.strip()
        # count spaces
        spaces = line.count(' ')
        if not spaces:
            # if there are no spaces, we don't need to assign arguments
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
            # this will be True if we only have one possibility, removed
            # from for loop as we want that to process fully.
            if len(possibleCmds)==1: 
               cmd = possibleCmds[0]
        
        # still haven't found it, possibleCmds is 2+ or 0
        if not cmd:
            # NOTE: These returns do nothing right now.
            # too many possibilities to decide
            if len(possibleCmds)>1:
                self.outBuf += "Too many possible commands.\r\n"
                return
            # no possibilities left
            if not len(possibleCmds):
                self.outBuf += "\"%s\" is not a valid command.\r\n"%first
                return
        
        # we've found it here, otherwise we'd already have returned.
        
        # see if it's a direction, because we have to send pos instead of arg
        # as the argument to self.cmds[cmd]
        if EXIT_STRINGS.count(cmd):
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
        # send the argument to the function specified in the dictionary
        else:
            self.cmds[cmd](arg)