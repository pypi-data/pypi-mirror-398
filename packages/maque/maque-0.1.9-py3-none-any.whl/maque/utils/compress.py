import shutil
from shutil import _find_unpack_format, _UNPACK_FORMATS
from pathlib import Path
from maque.utils.path import rel_to_abs, rel_path_join
import os


def pack(source_path: str, target_path=None, format='gztar'):
    """Pack or compress files.

    Parameters
    ----------
    source_path: str:
        source path
    target_path: str:
        target path
    format : str
        `format` is the archive format: one of "zip", "tar", "gztar"(default), "bztar", or "xztar".
        Or any other registered format.
    """
    if target_path is None:
        target_path = Path(source_path).name
    new_path = shutil.make_archive(target_path, format, root_dir=source_path)
    print(f"target path:\n{new_path}")


def unpack(filename: str, extract_dir=None, format=None):
    """Unpack or decompress files.

    Parameters
    ----------
    filename : str
        input source file
    extract_dir : str | None
        output dir
    format : str | None
        `format`is the archive format: one of "zip", "tar", "gztar", "bztar", or "xztar".
        If not provided, unpack_archive will use the filename extension.
    """
    name_path = Path(filename)
    if not name_path.exists():
        raise FileExistsError(f"{name_path} not exist.")
    name = name_path.name
    file_format = _find_unpack_format(filename)
    file_postfix_list = _UNPACK_FORMATS[file_format][0]
    for postfix in file_postfix_list:
        if name.endswith(postfix):
            target_name = name[:-len(postfix)]
            break
    else:
        target_name = name.replace('.', '_')

    if extract_dir is None:
        extract_dir = f"./{target_name}/"
    if not Path(extract_dir).exists():
        os.mkdir(extract_dir)
    shutil.unpack_archive(filename, extract_dir, format=format)
    print(f"extract dir:\nfile://{Path(extract_dir).absolute()}")


if __name__ == "__main__":
    # source_path = rel_to_abs('../web/', return_str=False, strict=True).name
    # pack('../web/', format='bztar')
    unpack('./web.tar.bz2')


