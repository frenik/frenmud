import room
import os
import objects

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
            inventory = []
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
                elif k=='I':
                    inventory.append(objects.Object(None,settings[k]))
            r = room.Room(id,title,desc,exits)
            r.inventory = inventory
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