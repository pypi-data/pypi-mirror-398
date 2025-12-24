import torch
from typing import Union, IO
import os

# Torch <= 2.5.X uses FILE_LIKE but newer torch versions moved to FileLike. This is a type annotation.
try:
    from torch.serialization import FileLike
except ImportError:
    try:
        from torch.serialization import FILE_LIKE as FileLike
    except ImportError:
        FileLike = Union[str, os.PathLike, IO[bytes]]

from typing import Any


def save(object: Any, path: FileLike):
    """
    Saves an object to a disk file. Safe wrapper around torch.save. Can be used to
    serialize FQIR as well as model state-dicts.

    Arguments:
        object (Any): saved object
        path: a file-like object. Typical convention is for filename to end in `.pt`
    """
    torch.save(object, path)


def load(path: FileLike, map_location="cpu"):
    """
    Loads an object serialized with :attr:`fmot.save` from disk.

    Wraps :attr:`torch.load` to maintain compatibility with loading FQIR graphs.

    Arguments:
        path: a file-like object to load
        map_location (str): device to load the object to, default :attr:`"cpu"`
    """
    obj = torch.load(path, weights_only=False, map_location=map_location)

    return obj
