from constants import *
class Room:
    def __init__(self, id, title, desc, exits):
        self.id = id
        self.title = title
        self.desc = desc
        self.exits = exits
        self.pList = []
        self.inventory = []
    
    def printToRoom(self,message):
        for p in self.pList:
            p.outBuf += '%s\r\n'%message       
    
    def removePlayerFromRoom(self,player,message):
        self.pList.remove(player)
        for p in self.pList:
            p.outBuf += message
        
    def addPlayerToRoom(self, player, message):
        for p in self.pList:
            p.outBuf += message
        self.pList.append(player)
        
    def save(self):
        print 'saving room #%i...'%self.id
        # open file
        f = open("world\\rooms\\%i.room"%self.id, "w")
        
        # write hard settings
        f.write('ID:%i\n'%self.id)
        f.write('Title:%s\n'%self.title)
        f.write('Desc:%s\n'%self.desc)
        
        # write exits
        for i in range(len(self.exits)):
            if self.exits[i] != None:
                f.write('%s:%i\n'%(EXIT_STRINGS_SHORT[i],self.exits[i].id))
        
        # loop through inventory
        for i in self.inventory:
            # write to file
            f.write('I:%i\n'%i.id)
            # save object
            i.save()
            print '    item #%i saved'%i.id
            
        f.close()
        
        