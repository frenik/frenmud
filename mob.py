import mobs.zombie
import files

mobTypes = {'Zombie':mobs.zombie.Zombie}

class Mob():
    def __init__(self,id):
        ''' Load a mob from a given id '''
        # initialize variables (not necessary but for my convenience)
        self.id = id
        self.room = None
        self.displayName = None
        self.shortName = None
        self.lookStr = None
        self.type = None
        self.moveRate = 0
        self.thinkAgain = 0
        
        settings = files.loadFromFile('world\\mobs\\%i.mob'%id)
            
        for k in settings.keys():
            if k == 'DisplayName':
                self.displayName = settings[k]
            elif k == 'ShortName':
                self.shortName = settings[k]
            elif k == 'MoveRate':
                self.moveRate = int(settings[k])
            elif k == 'Look':
                self.lookStr = settings[k]
            elif k == 'Type':
                self.type = settings[k]
        
        # load "personality"
        typeFound = False
        for k,v in mobTypes.items():
            if self.type == k:
                print 'Mob Personality = %s (%s)'%(k,v)
                self.type = v(self)
                print self.type
                typeFound = True
        if not typeFound:
            print 'Error loading mob: personality not found.'
        
        # just an alias for parse_look
        self.name = self.shortName
        
    def think(self):
        if self.type:
            # pass a reference to ourself
            self.type.think()
        else:
            # zombie behavior by default
            # we're not ready to think yet
            if self.thinkAgain:
                self.thinkAgain -= 1
                return
                
            # zombies always look for targets
            target = None
            
            # look for a player target in current room
            for p in self.room.pList:
                # in here we'll figure out who is the best target
                # or perhaps pick one at random. For now, we'll just
                # target the first poor Player he sees
                target = p
                break
                
            if not target:
                # look in adjacent rooms for targets
                for e in self.room.exits:
                    if e:
                        if len(e.pList):
                            self.move(e)
                            self.thinkAgain = 10
            else:
                self.attack(target)          
                self.thinkAgain = 10
        
    def move(self,room):
        self.room.printToRoom('%s %s'%(self.displayName,self.type.strings['moveOut']))
        self.room.mList.remove(self)
        self.room = room
        self.room.mList.append(self)
        self.room.printToRoom('%s %s'%(self.displayName,self.type.strings['moveIn']))
        
    def attack(self,target):
        target.outBuf += '%s wants to attack you, but '%self.displayName
        target.outBuf += 'can\'t.\r\n'
        
    def say(self,sayString):
        self.room.printToRoom('%s %s, "%s"\r\n'%
            (self.displayName,self.type.strings['sayStr'],sayString))