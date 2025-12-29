def checkDivisibility(input, target):
    def converttonumber(value):
        try:
            value_str = str(value).strip()
            return float(value_str) if "." in value_str else int(value_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: '{value}'")
    
    ip = converttonumber(input)
    tg = converttonumber(target)
    
    if ip % tg == 0:
        print(f"{ip} Is Divisible By {tg}")
    else:
        print(f"{ip} Is Not Divisible By {tg}")

def checkDivisibilityArray(target=None, input=None, *args):

    # Validate target
    if target is None:
        raise ValueError("Error: target value cannot be None or empty")

    # Validate input and args
    if input is None and not args:
        raise ValueError("Error: input cannot be None or empty")

    values = []

    # Validate input
    if input is not None:
        if input == []:
            raise ValueError("Error: input list cannot be empty")

        if isinstance(input, list):
            values.extend(input)
        else:
            values.append(input)

    # Collect args
    if args:
        values.extend(args)

    if not values:
        raise ValueError("Error: no valid values provided")

    divisible_values = []

    for item in values:
        # Reject invalid string values
        if item in [None, "", "null", "undefined"]:
            raise ValueError("Error: input contains null, undefined, or empty value")

        try:
            num = int(item)  # convert numeric strings
        except (ValueError, TypeError):
            raise ValueError(f"Error: invalid non-numeric value '{item}'")

        if num % target == 0:
            divisible_values.append(num)

    return divisible_values

def checkNonDivisibilityArray(target=None, input=None, *args):
    
    # Validate target
    if target is None:
        raise ValueError("Error: target value cannot be None or empty")

    # Validate input and args
    if input is None and not args:
        raise ValueError("Error: input cannot be None or empty")

    values = []

    # Validate input
    if input is not None:
        if input == []:
            raise ValueError("Error: input list cannot be empty")

        if isinstance(input, list):
            values.extend(input)
        else:
            values.append(input)

    # Collect args
    if args:
        values.extend(args)

    if not values:
        raise ValueError("Error: no valid values provided")

    divisible_values = []

    for item in values:
        # Reject invalid string values
        if item in [None, "", "null", "undefined"]:
            raise ValueError("Error: input contains null, undefined, or empty value")

        try:
            num = int(item)  # convert numeric strings
        except (ValueError, TypeError):
            raise ValueError(f"Error: invalid non-numeric value '{item}'")

        if num % target != 0:
            divisible_values.append(num)

    return divisible_values