def checkEvenSeries(limit):
    for i in range(0, limit + 1):
        if i % 2 == 0:
            print(i, end=" ")
    print()

def checkOddSeries(limit):
    for i in range(0, limit + 1):
        if i % 2 != 0:
            print(i, end=" ")
    print()

def checkEvenRange(limit1, limit2):
    for i in range(limit1, limit2 + 1):
        if i % 2 == 0:
            print(i, end=" ")
    print()

def checkOddRange(limit1, limit2):
    for i in range(limit1, limit2 + 1):
        if i % 2 != 0:
            print(i, end=" ")
    print()
