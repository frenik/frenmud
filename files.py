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
    
    # get a list containing each line in the file
    lines = f.readlines()

    # iterate through lines
    for l in lines:
        # test for empty line, end read if found
        if l=='': break 
        # strip endline
        l = l.rstrip('\n')
        # test for comment line, discard
        if l.find('#') == 0: # comment lines start with # on first space
            continue
        # split line by colon character
        l = l.split(':')
        # store everything up to first colon as key, everything after as value
        settings[l[0]] = l[1]
        
    # close file
    f.close()
    
    # return the dictionary
    return settings