from .config import NextCloudConfig
import contextlib
class NXClient:
    pass

@contextlib.contextmanager
def nx_connect(config:NextCloudConfig):
    try:
        yield 1
    finally:
        pass