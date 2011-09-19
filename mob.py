class Mob():
    def __init__(self,id):
        ''' Load a mob from a given id '''
        self.id = id
        self.room = None
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
        
        f.close()
        
    def think(self):
        pass