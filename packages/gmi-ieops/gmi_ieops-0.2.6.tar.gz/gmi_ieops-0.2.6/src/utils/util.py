import random
import os

_TOKEN_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


async def arandstr(n: int):
    return ''.join(random.choices(_TOKEN_CHARS, k=n))


async def arandint(a, b):
    return int(random.random()*(b-a))+a


def randstr(n: int):
    return ''.join(random.choices(_TOKEN_CHARS, k=n))


def randint(a, b):
    return int(random.random()*(b-a))+a

APP_ID = f"{os.getenv('APP_NAME', 'ieops')}.{randstr(8)}"
