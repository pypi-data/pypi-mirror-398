def printzerorange(range_value):
    def converttonumber(value):
        try:
            value_str = str(value).strip()
            return float(value_str) if "." in value_str else int(value_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: '{value}'")
    
    r = converttonumber(range_value)

    # Ensure the number is non-negative
    if r < 0:
        raise ValueError("Range must be zero or positive.")

    # Generate the array from 0 to r
    # If r is float, convert to int safely
    r_int = int(r)

    for i in range(0, r_int+1):
        print(i, end=" ")
    print()

def printzerorangearray(range_value):
    # Convert any input to an integer/float safely
    def converttonumber(value):
        try:
            value_str = str(value).strip()
            return float(value_str) if "." in value_str else int(value_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: '{value}'")

    # Convert the input range value
    r = converttonumber(range_value)

    # Ensure the number is non-negative
    if r < 0:
        raise ValueError("Range must be zero or positive.")

    # Generate the array from 0 to r
    # If r is float, convert to int safely
    r_int = int(r)

    result_array = list(range(0, r_int + 1))

    return result_array