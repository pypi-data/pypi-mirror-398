
# dotgesture/__init__.py

#- Imports -----------------------------------------------------------------------------------------

from .v1 import read_file as v1


#- Export ------------------------------------------------------------------------------------------

GESTURE_VERSION: int = 1

version_readers = {
    1: v1,
}

__all__ = [
    "version_readers", "GESTURE_VERSION"
]

