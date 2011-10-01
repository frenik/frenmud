class Zombie():
    def __init__(self,parent):
        # get a reference to our parent object
        self.parent = parent
        # establish unique strings for this mob
        self.strings = {
            # "displayName does something."
            'displayName' : 'A zombie',    
            # What a player sees when doing "look Zombie"
            'lookStr' : parent.lookStr, # temporary until detailed look
            # "A zombie shuffles out."
            'moveOut' : 'shuffles out.',
            # "A zombie shuffles in."
            'moveIn' : 'shuffles in.',
            # "A zombie groans, 'murrhrhrh'"
            'sayStr' : 'groans'
        }
        self.generateInventory()
        
    def generateInventory(self):
        ''' Generates the inventory of the mob. I don't want all mobs to spawn
            with the same setup, necessarily. Gold amounts will be varied,
            as well as items. All of that will be done here.
        '''
        pass
        
    def think(self):
        # we're not ready to think yet
        if self.parent.thinkAgain:
            self.parent.thinkAgain -= 1
            return
            
        # zombies always look for targets
        target = None
        
        # look for a player target in current room
        for p in self.parent.room.pList:
            # in here we'll figure out who is the best target
            # or perhaps pick one at random. For now, we'll just
            # target the first poor Player he sees
            target = p
            break
            
        if not target:
            # look in adjacent rooms for targets
            for e in self.parent.room.exits:
                if e:
                    if len(e.pList):
                        self.parent.move(e)
                        self.parent.thinkAgain = 10
        else:
            self.parent.attack(target)          
            self.parent.thinkAgain = 10