def _groupByThrees(n):
    nArray = []
    everyThree = 1

    nSize = len(n)
    lastIndex = nSize
    i = nSize-1

    while i >= 0:
        if everyThree == 3:            
            nArray.insert(0, n[i:lastIndex])
            lastIndex = i
            everyThree = 1
            
        elif i == 0:
            nArray.insert(0, n[i:lastIndex])
        else:
            everyThree += 1
            
        i -= 1

    return nArray

def _joinByGroups(str):
    return '.'.join(_groupByThrees(str))