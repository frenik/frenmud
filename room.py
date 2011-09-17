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