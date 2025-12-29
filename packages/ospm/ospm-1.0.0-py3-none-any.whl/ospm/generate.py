from secrets import choice
from string import ascii_letters, digits

chars = ascii_letters + digits


def generate_password(length: int = 16):
    return ''.join(choice(chars) for _ in range(length))