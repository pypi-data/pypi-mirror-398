from forbiddenfruit import curse



#============================  LIST
def group(self,n):
    return [self[x:x+n] for x in range(0, len(self), n)]

curse(list, "group", group)