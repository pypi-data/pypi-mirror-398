from pathlib import Path

def dir(path, recursive=False, show_files=True, show_folders=False):
    """
    returns all local files/folders at given path

    Parameters
    ----------
    path : str or Pathlib.Path
        path from which to list all files (default: '')

    recursive : bool
        if True, recursively list files. if False (default) no recursion

    show_files : bool
        if True (default), show file entries
        if False, do not show file entries

    show_folders : bool
        if True, show folder entries
        if False (default), do not show folder entries

    Returns
    -------
    files, relative to path : list
    """
    path = Path(path)

    result = []
    for entry in path.iterdir():
        if entry.is_file():
            if show_files:
                result.append(str(entry))
        elif entry.is_dir():
            if show_folders:
                result.append(str(entry) + "/")
            if recursive:
                result.extend(list_local(entry, recursive=recursive, show_files=show_files, show_folders=show_folders))
    return result


def write(path, contents):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(contents)


def read(path):
    path = Path(path)
    with open(path, "rb") as f:
        contents = f.read()
    return contents
