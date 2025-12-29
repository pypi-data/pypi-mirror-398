def divisionoperation(input1, input2, input3, choice):
    # Convert input values to numbers safely
    def converttonumber(value):
        try:
            value_str = str(value).strip()
            return float(value_str) if "." in value_str else int(value_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: '{value}'")

    if not choice or not isinstance(choice, str):
        raise ValueError("Choice must be a valid string.")

    c = choice.lower()

    num1 = converttonumber(input1)
    num2 = converttonumber(input2)
    num3 = converttonumber(input3)

    # Perform operations based on choice
    if c == "quotient":
        if num3 == 0:
            raise ZeroDivisionError("Division by zero error: input3 cannot be zero when calculating quotient.")
        return (num1 - num2) // num3   # Floor division (equivalent to Math.floor)

    elif c == "dividend":
        return num1 * num2 + num3

    elif c == "divisor":
        if num2 == 0:
            raise ZeroDivisionError("Division by zero error: input2 cannot be zero when calculating divisor.")
        return (num1 - num3) / num2

    elif c == "remainder":
        return num1 - (num2 * num3)

    else:
        raise ValueError("Invalid choice. Must be 'Dividend', 'Divisor', 'Quotient', or 'Remainder'.")

def division(dividend, divisor, choice):
    # Convert any input safely into int or float
    def converttonumber(value):
        try:
            value_str = str(value).strip()
            return float(value_str) if "." in value_str else int(value_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: '{value}'")

    if not choice or not isinstance(choice, str):
        raise ValueError("Choice must be a valid string.")

    c = choice.lower()

    num1 = converttonumber(dividend)
    num2 = converttonumber(divisor)

    # Prevent division by zero for quotient and remainder
    if c in ("quotient", "remainder") and num2 == 0:
        raise ZeroDivisionError("Division by zero is not allowed.")

    # All operations
    if c == "dividend":
        return num1

    elif c == "divisor":
        return num2

    elif c == "quotient":
        return num1 / num2

    elif c == "remainder":
        return num1 % num2

    else:
        raise ValueError(
            "Invalid choice. Allowed values are: 'dividend', 'divisor', 'quotient', 'remainder'."
        )
