def checkEvenSeriesArray(limit):
    res = []
    for i in range(0, limit + 1):
        if i % 2 == 0:
            res.append(i)
    return res

def checkOddSeriesArray(limit):
    res = []
    for i in range(0, limit + 1):
        if i % 2 != 0:
            res.append(i)
    return res

def checkEvenRangeArray(limit1, limit2):
    res = []
    for i in range(limit1, limit2 + 1):
        if i % 2 == 0:
            res.append(i)
    return res

def checkOddRangeArray(limit1, limit2):
    res = []
    for i in range(limit1, limit2 + 1):
        if i % 2 != 0:
            res.append(i)
    return res