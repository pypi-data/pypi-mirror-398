import os
import requests
import json

_token = None
missing = object()


def normalize_path(path):
    path = str(path).strip()
    if path == "/":
        path = ""
    if path and not path.startswith("/"):
        path = "/" + path
    return path


def init(refresh_token=missing, app_key=missing, app_secret=missing, **kwargs):
    """
    This function may to be called prior to using any dropbox function
    to specify the request token, app key and app secret.
    If these are specified as DROPBOX.REFRESH_TOKEN, DROPBOX.APP_KEY and DROPBOX.APP_SECRET
    environment variables, it is not necessary to call dropbox_init().

    Parameters
    ----------
    refresh_token : str
        oauth2 refreshntoken

        if omitted: use the environment variable DROPBOX.REFRESH_TOKEN

    app_key : str
        app key

        if omitted: use the environment variable DROPBOX.APP_KEY


    app_secret : str
        app secret

        if omitted: use the environment variable DROPBOX.APP_SECRET

    Returns
    -------
    dropbox object
    """

    global _token
    try:
        import pyodide_http

        pyodide_http.patch_all()  # required to reliably use requests on pyodide platforms

    except ImportError:
        ...

    if refresh_token is missing:
        if "DROPBOX.REFRESH_TOKEN" in os.environ:
            refresh_token = os.environ["DROPBOX.REFRESH_TOKEN"]
        else:
            raise ValueError("no DROPBOX.REFRESH_TOKEN found in environment.")
    if app_key is missing:
        if "DROPBOX.APP_KEY" in os.environ:
            app_key = os.environ["DROPBOX.APP_KEY"]
        else:
            raise ValueError("no DROPBOX.APP_KEY found in environment.")
    if app_secret is missing:
        if "DROPBOX.APP_SECRET" in os.environ:
            app_secret = os.environ["DROPBOX.APP_SECRET"]
        else:
            raise ValueError("no DROPBOX.APP_SECRET found in environment.")

    response = requests.post(
        "https://api.dropbox.com/oauth2/token",
        data={"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": app_key, "client_secret": app_secret},
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ValueError("invalid dropbox credentials")
    _token = response.json()["access_token"]


def _login():
    if _token is None:
        init()  # use environment


def dir(path="", recursive=False, show_files=True, show_folders=False):
    """
    returns all dropbox files/folders in path

    Parameters
    ----------
    path : str or Pathlib.Path
        path from which to list all files (default: '')

    recursive : bool
        if True, recursively list files and folders. if False (default) no recursion

    show_files : bool
        if True (default), show file entries
        if False, do not show file entries

    show_folders : bool
        if True, show folder entries
        if False (default), do not show folder entries

    Returns
    -------
    files : list

    Note
    ----
    If DROPBOX.REFRESH_TOKEN, DROPBOX.APP_KEY and DROPBOX.APP_SECRET environment variables are specified,
    it is not necessary to call dropbox_init() prior to any dropbox function.
    """
    _login()

    path = normalize_path(path)

    API_RPC = "https://api.dropboxapi.com/2"
    headers = {"Authorization": f"Bearer {_token}", "Content-Type": "application/json"}
    payload = {"path": path, "recursive": recursive, "include_deleted": False}
    response = requests.post("https://api.dropboxapi.com/2/files/list_folder", headers=headers, json=payload, timeout=30)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise OSError(f"error listing dropbox. Original message is {e}") from None
    data = response.json()
    entries = data["entries"]
    while data.get("has_more"):
        response = requests.post(f"{API_RPC}/files/list_folder/continue", headers=headers, json={"cursor": data["cursor"]}, timeout=30)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise OSError(f"error listing dropbox. Original message is {e}") from None
        data = response.json()
        entries.extend(data["entries"])

    result = []
    for entry in entries:
        if show_files and entry[".tag"] == "file":
            result.append(entry["path_display"])
        if show_folders and entry[".tag"] == "folder":
            result.append(entry["path_display"] + "/")
    return result


def read(path, cached=True):
    """
    read file from dropbox

    Parameters
    ----------
    path : str or Pathlib.Path
        path to read from
        
    cached : bool
        if True (default), result will be cached
        
        if False, read on each call

    Returns
    -------
    contents of the dropbox file : bytes

    Note
    ----
    If the file could not be read, an OSError will be raised.

    Note
    ----
    If DROPBOX.REFRESH_TOKEN, DROPBOX.APP_KEY and DROPBOX.APP_SECRET environment variables are specified,
    it is not necessary to call dropbox_init() prior to any dropbox function.
    """
    if cached:
        if path in read.cache:
            return read.cache[path]        
    else:
        read.cache={}
    _login()

    path = normalize_path(path)

    headers = {"Authorization": f"Bearer {_token}", "Dropbox-API-Arg": json.dumps({"path": path})}
    with requests.post("https://content.dropboxapi.com/2/files/download", headers=headers, stream=True, timeout=60) as response:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise OSError(f"file {str(path)} not found. Original message is {e}") from None
        chunks = []
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                chunks.append(chunk)
    result= b"".join(chunks)        
    read.cache[path]=result
    return result
read.cache={}


def write(path, contents):
    """
    write to file on dropbox

    Parameters
    ----------
    path : str or Pathlib.Path
        path to write to

    contents : bytes
        contents to be written

    Note
    ----
    If the file could not be written, an OSError will be raised.

    Note
    ----
    If DROPBOX.REFRESH_TOKEN, DROPBOX.APP_KEY and DROPBOX.APP_SECRET environment variables are specified,
    it is not necessary to call dropbox_init() prior to any dropbox function.
    """
    _login()
    path = normalize_path(path)

    headers = {
        "Authorization": f"Bearer {_token}",
        "Dropbox-API-Arg": json.dumps(
            {"path": str(path), "mode": "overwrite", "autorename": False, "mute": False}  # Where it will be saved in Dropbox  # "add" or "overwrite"
        ),
        "Content-Type": "application/octet-stream",
    }
    response = requests.post("https://content.dropboxapi.com/2/files/upload", headers=headers, data=contents)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise OSError(f"file {str(path)} could not be written. Original message is {e}") from None


def delete(path):
    """
    delete file dropbox

    Parameters
    ----------
    path : str or Pathlib.Path
        path to delete

    Note
    ----
    If the file could not be deleted, an OSError will be raised.

    Note
    ----
    If DROPBOX.REFRESH_TOKEN, DROPBOX.APP_KEY and DROPBOX.APP_SECRET environment variables are specified,
    it is not necessary to call dropbox_init() prior to any dropbox function.
    """
    _login()
    path = normalize_path(path)

    headers = {"Authorization": f"Bearer {_token}", "Content-Type": "application/json"}

    data = {"path": str(path)}  # Path in Dropbox, starting with /

    response = requests.post("https://api.dropboxapi.com/2/files/delete_v2", headers=headers, data=json.dumps(data))
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise OSError(f"file {str(path)} could not be deleted. Original message is {e}") from None
