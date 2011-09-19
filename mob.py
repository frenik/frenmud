class Mob():
    def __init__(self,id):
        ''' Load a mob from a given id '''
        # initialize variables (not necessary but for my convenience)
        self.id = id
        self.room = None
        self.displayName = None
        self.shortName = None
        self.moveRate = 0
        self.thinkAgain = 0
   
        # open file
        f = open('world\\mobs\\%i.mob'%id,'r')
        
        settings = {}
        
        while f:
            line = f.readline()
            if line=="": break # empty line, stop reading
            line = line.rstrip('\n') # strip endlines
            if line.find('#')==0: continue # comment
            line = line.split(':')
            settings[line[0]] = line[1]
            
        for k in settings.keys():
            if k == 'DisplayName':
                self.displayName = settings[k]
            elif k == 'ShortName':
                self.shortName = settings[k]
            elif k == 'MoveRate':
                self.moveRate = int(settings[k])
        
        f.close()
        
    def think(self):
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
        self.room.printToRoom('%s shuffles out.'%self.displayName)
        self.room.mList.remove(self)
        self.room = room
        self.room.mList.append(self)
        self.room.printToRoom('%s shuffles in.'%self.displayName)
        
    def attack(self,target):
        target.outBuf += '%s wants to attack you, but '%self.displayName
        target.outBuf += 'can\'t.\r\n'
        
    def say(self,sayString):
        self.room.printToRoom('%s says, "%s"\r\n'%(self.displayName,sayString))