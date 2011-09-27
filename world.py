import room
import os
import objects
import mob
import files

class World:
    def __init__(self):
        """ Load world from files. """
        self.rList = []
        
        # open all files in directory world/rooms/
        fileList = os.listdir('world\\rooms\\')
        
        # find highest room number and create self.rList with that many slots
        highNum = 1
        for f in fileList:
            num = f.split('.')
            if int(num[0]) > highNum:
                highNum = int(num[0])
        self.rList = [0]*(highNum+1)
    
        for f in fileList:
            settings = files.loadFromFile('world\\rooms\\%s'%f)
            id = None
            title = None 
            desc = None            
            exits = [None]*10
            inventory = []
            mList = []
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
                elif k=='M':
                    mList.append(mob.Mob(int(settings[k])))
            r = room.Room(id,title,desc,exits)
            r.inventory = inventory
            r.mList = mList
            # update mobs knowledge of their room
            for m in r.mList:
                m.room = r
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
    
    def save(self):        
        # loop through rooms
        for r in self.rList:
            # Room.save() also saves objects within rooms
            r.save()
        # done
        print 'world saved'
        