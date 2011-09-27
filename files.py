#   files.py contains functions used for utility, involving (obviously)
# file manipulation

def loadFromFile(filename):
    ''' Get a file's contents and return a dictionary containing values.
       :param filename: The filename to be loaded, including full path.
    '''
    try:
        f = open(filename,'r')
    except IOError:
        # error opening file
        return None
    
    # empty dictionary to store settings from file
    settings = {}
    
    # loop through file
    while f:
        line = f.readline()
        # test for empty line, end read if found
        if line=="": break 
        # strip endline
        line = line.rstrip('\n')
        # test for comment line, discard
        if line.find('#') == 0: # comment lines start with # on first space
            continue
        # split line by colon character
        line = line.split(':')
        # store everything up to first colon as key, everything after as value
        settings[line[0]] = line[1]
    
    # close file
    f.close()
    
    # return the dictionary
    return settings