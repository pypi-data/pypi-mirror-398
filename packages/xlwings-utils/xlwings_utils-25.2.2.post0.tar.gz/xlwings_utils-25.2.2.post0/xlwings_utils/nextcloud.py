import requests
import xml.etree.ElementTree
import urllib.parse
import xlwings_utils
import os

try:
    import pyodide_http
except ImportError:
    ...

missing = object()

_url = None


def make_base_path(webdav_url: str) -> str:
    """
    Turn 'https://host/remote.php/dav/files/user%40mail.com/'
    into '/remote.php/dav/files/user@mail.com/' (decoded, with trailing slash).
    """
    p = urllib.parse.urlparse(webdav_url)
    path = urllib.parse.unquote(p.path)
    if not path.endswith("/"):
        path += "/"
    return path


def clean_href(href: str, base_path: str) -> str:
    """
    Turn href from PROPFIND into a clean relative path.
    Works whether href is absolute URL or just a server path,
    and whether it's encoded or not.
    """
    # href may be a full URL or just a path
    if "://" in href:
        href_path = urllib.parse.unquote(urllib.parse.urlparse(href).path)
    else:
        href_path = urllib.parse.unquote(href)

    # Ensure base_path is decoded and slash-normalized
    base_path = urllib.parse.unquote(base_path)
    if not base_path.endswith("/"):
        base_path += "/"

    if href_path.startswith(base_path):
        rel = href_path[len(base_path) :]
    else:
        # fallback: just strip leading slash to avoid weird output
        rel = href_path.lstrip("/")

    return rel.lstrip("/")


def init(url=missing, username=missing, password=missing, **kwargs):
    global _auth
    global _url
    try:
        import pyodide_http

        pyodide_http.patch_all()  # required to reliably use requests on pyodide platforms

    except ImportError:
        ...

    if url is missing:
        if "NEXTCLOUD.URL" in os.environ:
            url = os.environ["NEXTCLOUD.URL"]
        else:
            raise ValueError("no NEXTCLOUD.URL found in environment.")
    if username is missing:
        if "NEXTCLOUD.USERNAME" in os.environ:
            username = os.environ["NEXTCLOUD.USERNAME"]
        else:
            raise ValueError("no NEXTCLOUD.USERNAMEfound in environment.")
    if password is missing:
        if "NEXTCLOUD.PASSWORD" in os.environ:
            password = os.environ["NEXTCLOUD.PASSWORD"]
        else:
            raise ValueError("no NEXTCLOUD.PASSWORD found in environment.")
    _url = url
    _auth = (username, password)


def _login():
    global _url
    if _url is None:
        init()  # use environment


def dir(path="", recursive=False, show_files=True, show_folders=False):
    """
    returns all nextcloud files/folders in path

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
    If NEXTCLOUD.URL, NEXTCLOUD.USERNAME and NEXTCLOUD.PASSWORD environment variables are specified,
    it is not necessary to call nextcloud_init() prior to any nextcloud function.
    """
    _login()

    headers = {"Depth": "1000" if recursive else "1"}  # 1 = directory + its immediate children

    response = requests.request("PROPFIND", _url + path, auth=_auth, headers=headers)

    response.raise_for_status()
    root = xml.etree.ElementTree.fromstring(response.text)
    namespaces = {"d": "DAV:"}

    items = []

    base_path = make_base_path(_url)

    for response_el in root.findall("d:response", namespaces):
        href = response_el.find("d:href", namespaces).text
        href = clean_href(href, base_path)
        if not href.startswith("/"):
            href = "/" + href

        prop = response_el.find("d:propstat/d:prop", namespaces)
        res_type = prop.find("d:resourcetype", namespaces)
        is_dir = res_type.find("d:collection", namespaces) is not None
        if is_dir and show_folders:
            items.append(href)
        if not is_dir and show_files:
            items.append(href)
    return items


def read(path, cached=True):
    """
    read file from nextcloud

    Parameters
    ----------
    path : str or Pathlib.Path
        path to read from

    cached : bool
        if True (default), result will be cached
        
        if False, read on each call
        
    Returns
    -------
    contents of the nextcloud file : bytes

    Note
    ----
    If the file could not be read, an OSError will be raised.

    Note
    ----
    If NEXTCLOUD.URL, NEXTCLOUD.USERNAME and NEXTCLOUD.PASSWORD environment variables are specified,
    it is not necessary to call nextcloud_init() prior to any nextcloud function.
    """
    if cached:
        if path in read.cache:
            return read.cache[path]        
    else:
        read.cache={}

    _login()
    response = requests.get(_url + path, auth=_auth)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise OSError(f"file {str(path)} not found. Original message is {e}") from None
    result = response.content
    read.cache[path]=result
    return result
read.cache={}

def write(path, contents):
    """
    write to file on nextcloud

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
    If NEXTCLOUD.URL, NEXTCLOUD.USERNAME and NEXTCLOUD.PASSWORD environment variables are specified,
    it is not necessary to call nextcloud_init() prior to any nextcloud function.
    """
    _login()
    response = requests.put(_url + path, auth=_auth, data=contents, timeout=60)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise OSError(f"file {str(path)} could not be written. Original message is {e}") from None


def delete(path):
    """
    delete file nextcloud

    Parameters
    ----------
    path : str or Pathlib.Path
        path to delete

    Note
    ----
    If the file could not be deleted, an OSError will be raised.

    Note
    ----
    If NEXTCLOUD.URL, NEXTCLOUD.USERNAME and NEXTCLOUD.PASSWORD environment variables are specified,
    it is not necessary to call nextcloud_init() prior to any nextcloud function.
    """
    _login()

    response = requests.delete(_url + path, auth=_auth, timeout=30)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise OSError(f"file {str(path)} could not be deleted. Original message is {e}") from None
