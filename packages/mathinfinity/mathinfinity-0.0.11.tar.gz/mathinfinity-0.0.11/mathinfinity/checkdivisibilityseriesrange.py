def checkDivisibilitySeries(limit, target):
    for i in range(0, limit + 1):
        if i % target == 0:
            print(i, end=" ")

def checkNonDivisibilitySeries(limit, target):
    for i in range(0, limit + 1):
        if i % target != 0:
            print(i, end=" ")

def checkDivisibilityRange(limit1, limit2, target):
    for i in range(limit1, limit2 + 1):
        if i % target == 0:
            print(i, end=" ")

def checkNonDivisibilityRange(limit1, limit2, target):
    for i in range(limit1, limit2 + 1):
        if i % target != 0:
            print(i, end=" ")