import secrets
import string

def generate_secure_password(length: int = 20, use_symbols: bool = True) -> str:
    """
    Generate a cryptographically secure random password.
    Ensures at least one character from each selected category is included.
    """
    if length < 8:
        raise ValueError("Password length should be at least 8 characters.")

    lc = string.ascii_lowercase
    uc = string.ascii_uppercase
    dg = string.digits
    sy = string.punctuation if use_symbols else ""

    alphabet = lc + uc + dg + sy
    
    password = [
        secrets.choice(lc),
        secrets.choice(uc),
        secrets.choice(dg),
    ]
    if use_symbols:
        password.append(secrets.choice(sy))

    remaining = length - len(password)
    password += [secrets.choice(alphabet) for _ in range(remaining)]

    secrets.SystemRandom().shuffle(password)
    
    return "".join(password)
