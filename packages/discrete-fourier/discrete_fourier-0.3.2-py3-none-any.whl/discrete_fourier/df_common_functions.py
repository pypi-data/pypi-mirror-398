"""
Discrete Fourier - Discrete Fourier common functions
====================================================

Author: Ricardo Marcelo Alvarez
Date: 2025-12-19
"""

import os
import sys
import threading
import time
import datetime
import string
import random
import hashlib
import io
import urllib.parse
import urllib.request
import json
import pwd
import grp
import socket
import zipfile
from typing import Dict, Any

import pprint # pylint: disable=unused-import
import yaml

def is_json(myjson):
    """
    is_json
    =======
        This function get a string or bytes and check if json return True
        if the input is a json valid string.
            :param myjson: str | bytes.

            :return bool: Return True if myjson is a str and is a json. 
    """

    result = False

    if myjson is not None and isinstance(myjson,(str,bytes)):
        try:
            json.loads(myjson)
            result = True
        except Exception: # pylint: disable=broad-except
            result = False

    return result

def is_convertible_to_json(myvar):
    """
    is_convertible_to_json
    ======================
        This function check if myvar is convertible to json string.
            :param myvar:

            :return bool: Return True if myvar is convertible to json string.
    """

    result = False
    try:
        json.dumps(myvar)
        result = True
    except Exception: # pylint: disable=broad-except
        result = False

    return result

def is_integer_string(s):
    """
    is_integer_string
    =================
    Determine if a string represents a valid integer (base 10).

    Parameters:
    -----------
    s : str
        Input string to test.

    Returns:
    --------
    bool
        True if the string can be converted to int without error, else False.
    """

    result = False
    try:
        int(s)
        result = True
    except ValueError:
        result = False

    return result

def time_to_str(t: float=None, fmt: str="%Y-%m-%d %H:%M:%S.%f") -> str:
    """
    time_to_str
    ===========
    Convert a timestamp to a formatted string.

    Parameters:
    -----------
    t : float | int, optional
        Timestamp in seconds since epoch. If None, uses current time. Defaults to None.
    fmt : str, optional
        Format string for strftime. Defaults to "%Y-%m-%d %H:%M:%S".

    Returns:
    --------
    str
        Formatted time string.
    """

    if t is None:
        t = time.time()

    return datetime.datetime.fromtimestamp(t).strftime(fmt)

def file_get_contents(filename, mode_in="", encoding='utf-8'):
    """
    file_get_contents
    =================
    This function reads the content of a file and returns it as a string.

    :param filename: str, the name of the file to read.
    :param mode_in: str, optional, the mode in which to open the file. Defaults to "".
    :param encoding: str, optional, the encoding format to use when reading the file.
                     Defaults to 'utf-8'.

    :return: str, the content of the file as a string.
    """
    result = None
    mode = "r" + mode_in

    try:
        f = open(filename, mode, encoding=encoding)
        result = f.read()
    except Exception: # pylint: disable=broad-except
        result = False

    return result

def file_put_contents(filename, data, mode_in=""):
    """
    file_put_contents
    =================
    This function writes the given data to the specified file.

    :param filename: str, the file path where data will be written.
    :param data: str, the content to write into the file.
    :param mode_in: str, optional, 'b' for binary mode. Defaults to "".

    :return: bool, returns True if the operation was successful, False otherwise.
    """
    result = False
    mode = "w"

    if len(mode_in) > 0:
        mode = mode_in
    try:
        f = open(filename, mode, encoding='utf-8')
        result = f.write(data)
        f.close()
    except Exception: # pylint: disable=broad-except
        result = False

    return result

def file_get_contents_url(url,mode="b",post_data=None,headers=None,timeout=9):
    """
    file_get_contents_url
    =====================
    This function get a url and reads into a string.

    :param url: str file URL.
    :param mode: str "b" for binary response.
    :param post_data: dict Post data in format key -> value.
    :param headers: dict headers in format key -> value.
    :param timeout: int request timeout.

    :return str: Return response data from url. 
    """

    result = None

    if headers is None:
        headers = {}

    try:
        req = None
        if post_data is not None and isinstance(post_data,dict):
            req = urllib.request.Request(url, urllib.parse.urlencode(post_data).encode(),headers)
        else:
            req = urllib.request.Request(url, None,headers)

        if req is not None:
            try:
                with urllib.request.urlopen(req, None, timeout=timeout) as response:
                    result = response.read()

            except Exception: # pylint: disable=broad-except
                result = None

        if result is not None and isinstance(result,bytes):
            result = result.decode()

    except Exception: # pylint: disable=broad-except
        result = None

    if mode != "b" and result is not None and result is not False and isinstance(result,bytes):
        result = result.decode()

    return result

def read_config_yaml(filename):
    """
    read_config_yaml
    ================
    This function reads a YAML configuration file and returns its content as a dictionary.
    
    :param filename: str File path to the YAML configuration file.
    
    :return: dict The contents of the YAML file as a dictionary.
    """
    file_raw = file_get_contents(filename)
    res = yaml.safe_load(file_raw)
    return res

def merge_common_keys(orig: dict, dest: dict) -> dict:
    """
    Merge keys from the original dictionary into the destination dictionary.
    Only keys that exist in both dictionaries are merged. If the value is a dictionary,
    the merge is performed recursively.
    Args:
        orig (dict): The original dictionary with new values.
        dest (dict): The destination dictionary to be updated.
    Returns:
        dict: The updated destination dictionary with merged values.
    Raises:
        None
    Notes:
        This function modifies the destination dictionary in place.
    """
    for k, v in orig.items():
        if k in dest:
            if isinstance(v, dict) and isinstance(dest[k], dict):
                merge_common_keys(v, dest[k])
            else:
                dest[k] = v
    return dest


def group_exists(name: str) -> bool:
    """
    Check if a group exists in the system.
    ======================================
    Args:
        name (str): Group name to check.
    Returns:
        bool: True if the group exists, False otherwise.
    Raises:
        None
    Notes:
        None
    """
    try:
        grp.getgrnam(name)
        return True
    except Exception: # pylint: disable=broad-except
        return False

def get_uid(username: str) -> int | None:
    """
    Get the user ID (UID) of a given username.
    ======================================
    Args:
        username (str): The username to look up.
    Returns:
        int | None: The UID of the user if found, None otherwise.
    Raises:
        None
    Notes:
        None
    """
    try:
        user_info = pwd.getpwnam(username)
        return user_info.pw_uid
    except Exception: # pylint: disable=broad-except
        return 0

def get_gid(groupname: str) -> int | None:
    """
    Get the group ID (GID) of a given group name.
    ======================================
    Args:
        username (str): The username to look up.
    Returns:
        int | None: The UID of the user if found, None otherwise.
    Raises:
        None
    Notes:
        None
    """
    try:
        __group_info = grp.getgrnam(groupname)
        return int(__group_info.gr_gid)

    except Exception: # pylint: disable=broad-except
        return 0

def is_port_free(port, host='localhost'):
    """
    is_port_free
    ============
    This function checks if the given port is available or already in use on the specified host.

    :param port: int The port number to check.
    :param host: str The host address (default is 'localhost').

    :return bool: Returns True if the port is free, False if it is in use.
    """
    result = False

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.close()
        result = True
    except Exception: # pylint: disable=broad-except
        result = False

    return result

def random_string(n=14):
    """
    random_string
    =============
    This function returns a random string of the specified length.

    :param n: int Length of the resulting string (default is 14).

    :return str: A randomly generated string of length 'n'.
    """
    letters = string.ascii_letters + '0123456789'
    return ''.join(random.choice(letters) for _ in range(n))

def sha256(str_in):
    """
    sha256
    ======
    This function returns the SHA-256 hash of the given string.

    :param str_in: str The input string to be hashed.

    :return str: The SHA-256 hash of the input string.
    """

    __sha = hashlib.sha256()
    __sha.update(str_in.encode('utf-8'))
    return __sha.hexdigest()

def is_valid_dir(dir_in): # pylint: disable=unused-argument
    """
    is_valid_dir
    ============

    This function takes a string and checks if it is a valid directory with write access.

    Parameters:
    -----------
    dir_in : str
        The directory path to check.

    Returns:
    --------
    bool
        Returns True if the directory is valid and writable, False otherwise.
    """

    result = False

    try:
        if not os.path.exists(dir_in):
            os.makedirs(dir_in)
            result = True
        elif not os.path.isdir(dir_in):
            result = False
        else:
            result = True

        result = result and os.access(dir_in, os.W_OK)

    except Exception: # pylint: disable=broad-except
        result = False

    return result

def is_valid_file(file_in): # pylint: disable=unused-argument
    """
    is_valid_file
    =============

    This function takes a string and checks if it is a valid file with write access.

    Parameters:
    -----------
    file_in : str
        The file path to check.

    Returns:
    --------
    bool
        Returns True if the file is valid and writable, False otherwise.
    """

    result = False

    try:
        if not os.path.exists(file_in):
            with open(file_in, 'a', encoding="utf-8") as f:
                f.write("")
            result = True
        elif not os.path.isfile(file_in):
            result = False
        else:
            result = True

        result = result and os.access(file_in, os.W_OK)

    except Exception: # pylint: disable=broad-except
        result = False

    return result

def decompress_zip_data(data):
    """
    decompress_zip_data
    ===================
    Decompress a ZIP file given as bytes and return the first entry's content as text.

    Parameters:
    -----------
    data : bytes
        Raw ZIP archive in memory.

    Returns:
    --------
    str | None
        UTF-8 decoded content of the first file inside the archive, or None on error.
    """

    result = None

    try:
        # z = zipfile.ZipFile(io.BytesIO(data))
        # result = z.read(z.infolist()[0]).decode()

        with zipfile.ZipFile(io.BytesIO(data)) as z:
            result = z.read(z.infolist()[0]).decode()

    except Exception: # pylint: disable=broad-except
        result = None

    return result

def create_dir_without_exception(dir_in):
    """
    create_dir_without_exception
    ============================
    Create a directory path if it does not already exist, ignoring exceptions.

    Parameters:
    -----------
    dir_in : str
        Directory path to create.

    Returns:
    --------
    bool | None
        True if the directory exists/was created, False on error, None if not attempted.
    """
    result = None
    try:
        if not os.path.exists(dir_in):
            os.makedirs(dir_in)
        result = True
    except Exception: # pylint: disable=broad-except
        result = False

    return result

def is_pid_running(pid):
    """
    is_pid_running
    ==============
    Check if a process with the given PID is currently running.

    Parameters:
    -----------
    pid : int
        Process ID to probe.

    Returns:
    --------
    bool
        True if the process appears to be alive, otherwise False.
    """
    result = False

    try:
        os.kill(pid, 0)
        result = True
    except OSError:
        result = False
    else:
        result = True

    return result

def load_config(config_path: str) -> Dict[str, Any]:
    """
    load_config
    ===========
    Load configuration from a YAML file.

    Parameters:
    -----------
    config_path : str
        Path to the configuration file.

    Returns:
    --------
    dict
        Mapping containing configuration data.

    Raises:
    -------
    FileNotFoundError
        If the config file does not exist.
    yaml.YAMLError
        If the config file contains invalid YAML.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config

def chg_owner_and_perms(dir_in: str = None,
                        uid: str = None,
                        gid: str = None,
                        perms_dir: int = 0o770,
                        perms_file: int = 0o660) -> bool:
    """
    chg_owner_and_perms
    ===================
    
    Recursively changes the ownership and permissions of all directories and files 
    under the specified directory.

    Args:
        dir_in (str): The base directory to start applying ownership and permissions.
        uid (int): The user ID to set as owner.
        gid (int): The group ID to set as group owner.
        perms_dir (int): Permissions to set on directories (e.g., 0o500).
        perms_file (int): Permissions to set on files (e.g., 0o400).

    Returns:
        bool: True if processing was started successfully (root privileges and valid input),
              False otherwise.
    
    Notes:
        - This function must be executed as root to change ownership.
        - If any path inside the directory fails, it prints an error but continues with others.
    """
    result = False

    if not (isinstance(uid, int) and isinstance(gid, int) and isinstance(dir_in, str)):
        return result

    if not os.path.isdir(dir_in):
        return result

    if os.geteuid() != 0:
        gid = os.getgid()


    for root, dirs, files in os.walk(dir_in):
        for d in dirs:
            path = os.path.join(root, d)
            try:
                os.chown(path, uid, gid)
                os.chmod(path, perms_dir)
                result = True
            except Exception:  # pylint: disable=broad-except
                result = False

        for f in files:
            path = os.path.join(root, f)
            try:
                os.chown(path, uid, gid)
                os.chmod(path, perms_file)
                result = True
            except Exception:  # pylint: disable=broad-except
                result = False

    return result

def safe_get(lst, index, default=None):
    """
    safe_get
    ========

    :param lst:
    :param index:
    :param default:
    :return:
    :rtype: Any
    """
    try:
        return lst[index]
    except (IndexError, TypeError):
        return default

class ReturnValueThread(threading.Thread):
    """
    ReturnValueThread
    =================
    This class extends the threading.Thread class to allow a thread to return a value.
    It captures the result of the target function and provides it when joining the thread.

    All credits to:
    https://alexandra-zaharia.github.io/posts/how-to-return-a-result-from-a-python-thread/

    :param args: Positional arguments passed to the target function.
    :param kwargs: Keyword arguments passed to the target function.
    """
    def __init__(self, *args, **kwargs):
        """
        __init__
        ========
        Initializes the ReturnValueThread.

        :param args: Positional arguments for the Thread constructor.
        :param kwargs: Keyword arguments for the Thread constructor.
        """

        super().__init__(*args, **kwargs)
        self.result = None

    def run(self):
        """
        run
        ===

        Executes the target function and captures its return value.
        If an exception occurs during the execution, it is printed to stderr.
        """

        if self._target is None:
            return  # could alternatively raise an exception, depends on the use case
        try:
            self.result = self._target(*self._args, **self._kwargs)
        except Exception as exc: # pylint: disable=broad-except
            print(f'{type(exc).__name__}: {exc}', file=sys.stderr)  # properly handle the exception

    def join(self, *args, **kwargs):
        """
        join
        ====

        Waits for the thread to finish and returns the result of the target function.

        :param args: Positional arguments for the join method.
        :param kwargs: Keyword arguments for the join method.

        :return: The result of the target function, if any.
        """


        super().join(*args, **kwargs)
        return self.result
