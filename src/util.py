
import os

CACHE_DIR = "cache/"


def create_cache_dir():
    """
    Create cache dir at `CACHE_DIR` if doesn't already exists
    """
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)


def cache(file_name):
    return CACHE_DIR + file_name
