class Zombie():
    def think(self,mob):
        # we're not ready to think yet
        if mob.thinkAgain:
            mob.thinkAgain -= 1
            return
            
        # zombies always look for targets
        target = None
        
        # look for a player target in current room
        for p in mob.room.pList:
            # in here we'll figure out who is the best target
            # or perhaps pick one at random. For now, we'll just
            # target the first poor Player he sees
            target = p
            break
            
        if not target:
            # look in adjacent rooms for targets
            for e in mob.room.exits:
                if e:
                    if len(e.pList):
                        mob.move(e)
                        mob.thinkAgain = 10
        else:
            mob.attack(target)          
            mob.thinkAgain = 10