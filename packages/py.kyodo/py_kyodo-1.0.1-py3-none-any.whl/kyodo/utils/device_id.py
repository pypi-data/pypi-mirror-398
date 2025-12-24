from random import choices
from string import ascii_letters, digits


def random_string(length: int = 11) -> str:
    return "".join(choices(ascii_letters + digits, k=length))
