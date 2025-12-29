def printrange(range_value1, range_value2):
    def converttonumber(value):
        try:
            value_str = str(value).strip()
            return float(value_str) if "." in value_str else int(value_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: '{value}'")
    
    r1 = converttonumber(range_value1)
    r2 = converttonumber(range_value2)

    if r1 > r2:
        raise ValueError("Range1 Must Be Smaller Than Range2")

    r_int1 = int(r1)
    r_int2 = int(r2)

    for i in range(r_int1, r_int2 + 1):
        print(i, end=" ")
    print()

def printrangearray(range_value1, range_value2):
    def converttonumber(value):
        try:
            value_str = str(value).strip()
            return float(value_str) if "." in value_str else int(value_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: '{value}'")
    
    r1 = converttonumber(range_value1)
    r2 = converttonumber(range_value2)

    if r1 > r2:
        raise ValueError("Range1 Must Be Smaller Than Range2")

    r_int1 = int(r1)
    r_int2 = int(r2)

    result_array = list(range(r_int1, r_int2 + 1))

    return result_array