from random import choice
from string import ascii_uppercase


def gen(prefix, length=16):
    """
    generates a random string of fixed length with the given prefix

    :param prefix: the prefix to add to the generated string; not included in length count
    :param length: number of random character added after prefix; default to 16
    :return: generated string
    """

    return prefix + "".join(choice(ascii_uppercase) for _ in range(length))
