def arithmeticoperation(input1, input2, choice):
    def converttonumber(value):
        try:
            value_str = str(value).strip()
            return float(value_str) if "." in value_str else int(value_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: '{value}'")
    
    ip1 = converttonumber(input1)
    ip2 = converttonumber(input2)

    if not isinstance(choice, str):
        raise ValueError("Choice must be a string.")

    choice = choice.lower().strip()

    match choice:
        case "+":
            return ip1 + ip2
        case "-":
            return ip1 - ip2
        case "*":
            return ip1 * ip2
        case "/":
            if ip2 == 0:
                raise ZeroDivisionError("Division by zero is not allowed.")
            return ip1 / ip2
        case "%":
            if ip2 == 0:
                raise ZeroDivisionError("Modulo by zero is not allowed.")
            return ip1 % ip2
        case _:
            raise ValueError("Unexpected operation encountered.")