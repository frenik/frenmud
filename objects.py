import files
import os

class Object:
    def __init__(self, owner, file):
        settings = files.loadFromFile('objects\\%s.obj'%file)
            
        # iterate through dict
        for k in settings.keys():
            if k=="Name":
                self.name = settings[k]
            if k=="Type":
                self.type = settings[k]

        self.id = int(file)
        self.owner = owner
        
    def save(self):
        f = open("objects\\%i.obj"%self.id,'w')
        f.write('Name:%s\n'%self.name)
        f.close()