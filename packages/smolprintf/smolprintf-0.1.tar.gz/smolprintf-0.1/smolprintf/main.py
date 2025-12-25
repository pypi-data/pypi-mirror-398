def printf(string, format=None):
    if format == None:
        print(string)
    else:
        print(string % format)
