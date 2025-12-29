def checkDivisibilitySeriesArray(limit, target):
    res = []
    for i in range(0, limit + 1):
        if i % target == 0:
            res.append(i)
    print()

def checkNonDivisibilitySeriesArray(limit, target):
    res = []
    for i in range(0, limit + 1):
        if i % target != 0:
            res.append(i)
    print()

def checkDivisibilityRangeArray(limit1, limit2, target):
    res = []
    for i in range(limit1, limit2 + 1):
        if i % target == 0:
            res.append(i)
    print()

def checkNonDivisibilityRangeArray(limit1, limit2, target):
    res = []
    for i in range(limit1, limit2 + 1):
        if i % target != 0:
            res.append(i)
    print()