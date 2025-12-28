from pathlib import Path
from typing import Union, List
import inspect
from glob import glob as _glob
import os
import sys


def rel_to_abs(rel_path: Union[str, Path], parents=0, return_str=True, strict=False):
    """Return absolute path relative to the called file
    args:
        parent: <int> The number of times `f_back` will be calledd.
    """
    currentframe = inspect.currentframe()
    f = currentframe.f_back
    for _ in range(parents):
        f = f.f_back
    current_path = Path(f.f_code.co_filename).parent
    pathlib_path = current_path / rel_path
    pathlib_path = pathlib_path.resolve(strict=strict)
    if return_str:
        return str(pathlib_path)
    else:
        return pathlib_path


def rel_path_join(*paths: Union[str, Path], return_str=True):
    return rel_to_abs(os.path.join(*paths), parents=1, return_str=return_str)


def ls(_dir, *patterns, relp=True, concat='extend', recursive=False) -> List[str]:
    """
    Example:
    --------
        >>> ls("./data/", "*.jpg", "*.png")
    """
    if relp:
        _dir = rel_to_abs(_dir, parents=1, return_str=True, strict=False)
    path_list = []
    for pattern in patterns:
        if concat == 'extend':
            path_list.extend(_glob(os.path.join(_dir, pattern), recursive=recursive))
        else:
            path_list.append(_glob(os.path.join(_dir, pattern), recursive=recursive))
    return path_list


def add_env_path(*rel_paths: str):
    """
    Example:
    --------
        >>> add_env_path('..')
        >>> add_env_path('..', '../..')
    """

    for i in rel_paths:
        sys.path.append(rel_to_abs(i, parents=1))
