import os

class Object:
    def __init__(self, owner, file):
        settings = {}
        # open file
        f = open("objects\\"+file+".obj", "r")
        # iterate through file
        while f:
            line = f.readline()
            # test for empty line
            if line=="": break
            line = line.rstrip('\n')            
            # comment lines start with '#', discard line and continue
            if line.find('#')==0: continue            
            # split line into key:value
            line = line.split(':')            
            # create new value to key in dict
            settings[line[0]] = line[1]
            
        # iterate through dict
        for k in settings.keys():
            if k=="Name":
                self.name = settings[k]

        self.id = int(file)
        self.owner = owner
        
    def save(self):
        f = open("objects\\%i.obj"%self.id,'w')
        f.write('Name:%s\n'%self.name)