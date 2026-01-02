import re

def validate_int(value, min_value=None, max_value=None):
    num = int(value)
    if min_value is not None and num < min_value:
        raise ValueError(f"value must be >= {min_value}")
    if max_value is not None and num > max_value:
        raise ValueError(f"value must be <= {max_value}")
    return num

def validate_float(value, min_value=None, max_value=None):
    num = float(value)
    if min_value is not None and num < min_value:
        raise ValueError(f"value must be >= {min_value}")
    if max_value is not None and num > max_value:
        raise ValueError(f"value must be <= {max_value}")
    return num

def validate_str(value, min_len=None, max_len=None):
    text = value.strip()
    if min_len is not None and len(text) < min_len:
        raise ValueError(f"minimum length is {min_len}")
    if max_len is not None and len(text) > max_len:
        raise ValueError(f"maximum length is {max_len}")
    return text

def validate_email(value):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, value):
        raise ValueError("invalid email format")
    return value

def validate_confirm(value):
    v = value.strip().lower()
    if v not in ("y", "yes", "n", "no"):
        raise ValueError("enter y/yes or n/no")
    return v in ("y", "yes")
def validate_choice(value, choices):
    if value not in choices:
        raise ValueError(f"choose from {choices}")
    return value

def validate_pattern(value, pattern, message="invalid format"):
    if not re.match(pattern, value):
        raise ValueError(message)
    return value

def validate_password_strength(value, min_len=8):
    if len(value) < min_len:
        raise ValueError(f"password must be at least {min_len} characters")
    if not re.search(r"[A-Z]", value):
        raise ValueError("password must contain an uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("password must contain a lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("password must contain a number")
    return value
