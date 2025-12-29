import inspect
import logging
import os
import paramiko
import posixpath
from functools import partial
from paramiko import sftp, sftp_attr
from pathlib import PurePath, Path
from pathlib_abc import JoinablePath, ReadablePath, WritablePath, PathInfo, PathParser
# docs: https://pathlib-abc.readthedocs.io/en/latest/api.html#abstract-base-classes
from stat import S_ISDIR, S_ISREG
from typing import TypedDict
from urllib.parse import urljoin, urlsplit, urlunsplit
from functools import reduce

__version__ = "0.5.5"
logger = logging.getLogger(__name__)
# _CACHED_CLIENT = None

# region config
APP_DIRECTORY = {
    "win32": "AppData/Roaming",
    "linux": ".local/share",
    "darwin": "Library/Application Support",
}

CACHING = True
CACHED_CONFIGS = {}
CACHED_CLIENTS = {}


# Ugly, but paramiko.SSHClient.connect.__annotations__ is empty.
Config = TypedDict("Config", {**{"root": str}, **{
    key: type(value.default)
        if value.default not in (None, inspect._empty)
        else object
    for key, value
    in inspect.signature(paramiko.SSHClient.connect).parameters.items()
    if key != "self"
}})


def load_client(config: Config):
    config = config.copy()
    root = config.pop("root", "/")
    ssh_client = paramiko.SSHClient()
    if (key not in config for key in ("pkey", "key_filename")):
        # Uses the file ~/.ssh/known_hosts
        ssh_client.load_system_host_keys()
    ssh_client.connect(**config)
    sftp_client = paramiko.sftp_client.SFTPClient.from_transport(
        ssh_client.get_transport())

    # Monkey patch the close() method.
    # This is simpler than making a new SSHSFTPClient class.
    _close = sftp_client.close
    def close(*args, **kwargs):
        _close()
        ssh_client.close()
    sftp_client.close = close

    # Root directory
    # sftp_client.chdir(root)
    sftp_client.root = root

    return sftp_client


def get_config_path():
    # https://stackoverflow.com/questions/19078969/python-getting-appdata-folder-in-a-cross-platform-way
    import sys
    from pathlib import Path

    home = Path.home()

    try:
        app_directory = APP_DIRECTORY[sys.platform]
    except KeyError as e:
        raise OSError(f"Unsupported system '{sys.platform}'.") from e

    return home / app_directory / "sftppathlib" / "config.ini"


def load_configs(config_path):
    import configparser
    reader = configparser.ConfigParser()

    with open(config_path, mode="r", encoding="utf-8") as f:
        reader.read_file(f)

    return {
        site: dict(attrs) for site, attrs in reader.items()
        if site is not configparser.DEFAULTSECT}


def get_accessor(authority):
    if authority in CACHED_CLIENTS:
        client = CACHED_CLIENTS[authority]
    else:
        if authority in CACHED_CONFIGS:
            config = CACHED_CONFIGS[authority]
        elif CACHING is True:
            CACHED_CONFIGS.update(load_configs(get_config_path()))
            config = CACHED_CONFIGS[authority]
        else:
            configs = load_configs(get_config_path())
            config = configs[authority]

        client = load_client(config)
        if CACHING is True:
            CACHED_CLIENTS[authority] = client

    return client


class PathBase(ReadablePath, WritablePath, PathInfo):
    # https://github.com/barneygale/pathlib-abc/blob/0.2.0/pathlib_abc/__init__.py
    def exists(self, *, follow_symlinks=True):
        """
        Whether this path exists.

        This method normally follows symlinks; to check whether a symlink exists,
        add the argument follow_symlinks=False.
        """
        try:
            self.stat(follow_symlinks=follow_symlinks)
        except OSError as e:
            return False
        except ValueError:
            # Non-encodable path
            return False
        return True

    def is_dir(self, *, follow_symlinks=True):
        """
        Whether this path is a directory.
        """
        try:
            return S_ISDIR(self.stat(follow_symlinks=follow_symlinks).st_mode)
        except OSError as e:
            # Path doesn't exist or is a broken symlink
            # (see http://web.archive.org/web/20200623061726/https://bitbucket.org/pitrou/pathlib/issues/12/ )
            return False
        except ValueError:
            # Non-encodable path
            return False

    def is_file(self, *, follow_symlinks=True):
        """
        Whether this path is a regular file (also True for symlinks pointing
        to regular files).
        """
        try:
            return S_ISREG(self.stat(follow_symlinks=follow_symlinks).st_mode)
        except OSError as e:
            # Path doesn't exist or is a broken symlink
            # (see http://web.archive.org/web/20200623061726/https://bitbucket.org/pitrou/pathlib/issues/12/ )
            return False
        except ValueError:
            # Non-encodable path
            return False

    def is_symlink(self):
        """
        Whether this path is a symbolic link.
        """
        try:
            return S_ISLNK(self.lstat().st_mode)
        except OSError as e:
            # Path doesn't exist
            return False
        except ValueError:
            # Non-encodable path
            return False


class URLParser(PathParser):
    sep = posixpath.sep
    altsep = posixpath.altsep
    normcase = posixpath.normcase
    join = posixpath.join

    def split(path):
        parts = urlsplit(path)
        path_parts = posixpath.split(parts.path)
        head = urlunsplit(parts._replace(path=path_parts[0], query="", fragment=""))
        tail = urlunsplit(parts._replace(path=path_parts[1], netloc="", scheme=""))
        return head, tail

    # def join(a, *p):
    #     return reduce(urljoin, p, a)



class SFTPPath(PathBase):
    """Partially copies the interface of pathlib.Path"""

    __slots__ = ("_accessor",)
    # pathmod = posixpath
    parser = URLParser

    # Everywhere with self.as_posix() should be removed once paramiko supports
    # the Path interface. Then we can pass self.

    def __init__(self, *args, accessor=None):
        # Reference to the sftp handler is necessary; in pathlib this is
        # equivalent to a reference to the os module; but this module is
        # assumed to be a singleton since it's unexpected for the os to
        # change when running a Python script. In comparison an sftppath
        # can refer to different servers.

        # In pathlib _accessor is a union of io and os. open() uses the io
        # module, while mkdir() and touch() uses os.
        # self._path = path
        # super().__init__(path, *paths)

        paths = []
        for arg in args:
            if isinstance(arg, JoinablePath):
                paths.append(arg.__vfspath__())
            elif isinstance(arg, PurePath):
                paths.append(arg.__fspath__())
            elif isinstance(arg, str):
                paths.append(arg)
            else:
                raise TypeError("Invalid type {type(arg)}.")

        self._raw_path = self.parser.join(*paths)


        if accessor is None:
            self._accessor = get_accessor(urlsplit(self._raw_path).netloc)
        else:
            self._accessor = accessor

    # @property
    # def _raw_path(self):
    #     paths = self._raw_paths
    #     if len(paths) == 1:
    #         return paths[0]
    #     elif paths:
    #         # Join path segments from the initializer.
    #         return self.parser.join(*paths)
    #     else:
    #         return ''

    @classmethod
    def from_config(cls, path, *paths, config: Config):
        return cls(path, *paths, accessor=load_client(config))

    # @classmethod
    # def _parse_path(cls, path):
    #     if not path:
    #         return '', '', []
    #     sep = cls.parser.sep
    #     altsep = cls.parser.altsep
    #     if altsep:
    #         path = path.replace(altsep, sep)
    #     drv, root, rel = cls.parser.splitroot(path)
    #     if not root and drv.startswith(sep) and not drv.endswith(sep):
    #         drv_parts = drv.split(sep)
    #         if len(drv_parts) == 4 and drv_parts[2] not in '?.':
    #             # e.g. //server/share
    #             root = sep
    #         elif len(drv_parts) == 6:
    #             # e.g. //?/unc/server/share
    #             root = sep
    #     # This part breaks urls since they contain //
    #     # return drv, root, [x for x in rel.split(sep) if x and x != '.']
    #     return drv, root, [x for x in rel.split(sep)]

    def info(self): return self

    def with_segments(self, *pathsegments):
        # Need to overload this one since it's used to construct new classes
        # and we need to pass down the accessor object.
        return type(self)(*pathsegments, accessor=self._accessor)

    def stat(self, *, follow_symlinks=True) -> sftp_attr.SFTPAttributes:
        logger.warning("Argument 'follow_symlinks' ignored.")
        return self._accessor.stat(self.__sftppath__())

    def open(self, mode="rb", buffering=-1, encoding=None,
             errors=None, newline=None):
        return FileHandler(
            self._accessor.open(self.__sftppath__(), mode=mode, bufsize=buffering),
            encoding, errors, newline)

    vfsopen = open

    def __open(self, mode, buffering=-1):
        return self._accessor.open(self.__sftppath__(), mode=mode, bufsize=buffering)

    __open_reader__ = partial(__open, mode="r")
    __open_writer__ = __open

    def iterdir(self):
        for path in self._accessor.listdir(self.__sftppath__()):
            yield type(self)(self._raw_path, path, accessor=self._accessor)

    def absolute(self):
        path = self.parser.normcase(self.as_posix())
        if not self.parser.isabs(path):
            # It's not possible to change directory (chdir) with the Path API
            # so getcwd() should always be None, and cwd will be "/".
            cwd = self._accessor.getcwd()
            if cwd is None:
                cwd = "/"
            path = self.parser.join(cwd, path)
        return self.parser.normpath(path)

    # Unsupported
    # def expanduser(): pass

    def readlink(self):
        raise NotImplementedError

    def symlink_to(self, target, target_is_directory=None):
        logger.warning("Argument 'target_is_directory' ignored.")
        self.symlink_to(
            type(self)(target, accessor=self._accessor),
            self.__sftppath__()
        )

    def hardlink_to(self, target):
        raise NotImplementedError

    def touch(self, mode=0o666, exist_ok=True):
        # Apparently there's no such thing as touch, only open
        # Note that exist_ok is True for touch, but False for mkdir

        flags = sftp.SFTP_FLAG_CREATE | sftp.SFTP_FLAG_WRITE
        if not exist_ok:
            flags |= sftp.SFTP_FLAG_EXCL

        attrblock = sftp_attr.SFTPAttributes()
        t, msg = self._accessor._request(
            sftp.CMD_OPEN, self.__sftppath__(), flags, attrblock)

        if t != sftp.CMD_HANDLE:
            raise sftp.SFTPError("Expected handle")

        handle = msg.get_binary()

        try:
            self._accessor._request(sftp.CMD_CLOSE, handle)
        except Exception as e:
            pass

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        try:
            self._accessor.mkdir(self.__sftppath__(), mode)
        except FileNotFoundError:
            if not parents or self.parent == self:
                raise
            self.parent.mkdir(parents=True, exist_ok=True)
            self.mkdir(self.__sftppath__(), mode, parent=False, exist_ok=exist_ok)
        except OSError:
            if not exist_ok or not self.is_dir():
                raise

    def rename(self, target):
        self._accessor.rename(
            self.__sftppath__(),
            type(self)(target, accessor=self._accessor).__sftppath__(),
        )

    # Unsupported
    # def replace(): pass

    def chmod(self, mode, *, follow_symlinks=None):
        logger.warning("Argument 'follow_symlinks' ignored.")
        self._accessor.chmod(self.__sftppath__(), mode)

    def unlink(self):
        self._accessor.remove(self.__sftppath__())

    def rmdir(self):
        self._accessor.rmdir(self.__sftppath__())

    # Unsupported
    # def owner(): pass

    # Unsupported
    # def group(): pass

    # Unsupported
    # def from_uri(): pass

    # Unsupported
    # def as_uri(): pass

    def as_posix(self):
        """Return the string representation of the path with forward (/)
        slashes."""
        return self._raw_path

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            self._accessor == other._accessor
            and self.parser is other.parser
            and self.parser.normcase(str(self)) == other.parser.normcase(str(other))
            )

    def __str__(self):
        return self.as_posix().rstrip(self.parser.sep)

    def __repr__(self):
        return f"{type(self).__name__}('{self.as_posix()}')"

    def __sftppath__(self):
        path = self.as_posix()
        parts = urlsplit(path)
        return urlunsplit(parts._replace(
            scheme="",
            netloc="",
            path=self.parser.join(
                self._accessor.root, parts.path.lstrip(self.parser.sep))
        ))

    # Required for PathLike objects
    def __vfspath__(self):
        return self.as_posix()

    # __fspath__ = __vfspath__

    # Python 3.14
    # def copy(): pass
    # def copy_into(): pass
    # def move(self): raise NotImplementedError
    # def move_into(self): raise NotImplementedError


PathBase.register(SFTPPath)


# Overload paramiko.sftp_file.SFTPFile?
# That is tricky because the constructor is paramiko.sftp_client.SFTPClient.open
# Instead we put it in a simple wrapper to handle encoding.
# This class can probably be replaced with io.TextIOWrapper
class FileHandler:
    def __init__(self, file_handler, encoding, errors, newline):
        self.file_handler = file_handler
        self.encoding = encoding
        self.errors = errors
        self.newline = newline

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        self.close()

    @property
    def prefetch(self):
        return self.file_handler.prefetch

    @property
    def _is_binary(self):
        return self.file_handler._flags & self.file_handler.FLAG_BINARY

    def close(self):
        self.file_handler.close()

    def read(self, size=None):
        # SFTPFile ignores binary/text flag, so we have to check it ourself
        text = self.file_handler.read(size)

        if not self._is_binary:
            text = text.decode(self.encoding)

        return text

    def write(self, text):
        if not self._is_binary:
            text = text.encode(self.encoding)

        self.file_handler.write(text)
