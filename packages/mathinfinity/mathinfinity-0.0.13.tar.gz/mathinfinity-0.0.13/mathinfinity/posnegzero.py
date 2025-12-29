def posnegzero (input):
    def converttonumber(value):
        try:
            value_str = str(value).strip()
            return float(value_str) if "." in value_str else int(value_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: '{value}'")
    
    ip = converttonumber(input)

    if ip > 0:
        print(f"{ip} Is Positive Number.")
    elif ip < 0:
        print(f"{ip} Is Negative Number.")
    else:
        print(f"{ip} Is Zero value.")