import os

PACKAGE_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(PACKAGE_ROOT, "..", ".."))
VERSION_PATH = os.path.join(PROJECT_ROOT, "VERSION")

try:
    with open(VERSION_PATH, "r") as f:
        __version__ = f.read().strip()
except FileNotFoundError:
    __version__ = "0.0.0"
