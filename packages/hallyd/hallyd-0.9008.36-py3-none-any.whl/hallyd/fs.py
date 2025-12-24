#  SPDX-FileCopyrightText: © 2022 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Filesystem.

See also :py:mod:`hallyd.fs_monitor`.
"""
import abc
import contextlib
import dataclasses
import enum
import errno
import grp
import io
import os
import pathlib
import pwd
import re
import stat
import subprocess
import tarfile
import typing as t
import zipfile

import hallyd.cleanup as _cleanup
import hallyd.lang as _lang


TOwnerSpec = str | int | bool | None
TOwnerGroupSpec = str | int | bool | None
TOptionalFlagSpec = bool | None
TModeSpec = str | int | bool | None
TInputPath = str | pathlib.Path


# TODO what is O_TMPFILE ?? can it improve sth?
# TODO are there things where we can do better avoiding race conditions?


def temp_dir(
    *,
    mode: TModeSpec = 0o750,
    owner: TOwnerSpec = True,
    group: TOwnerGroupSpec = True,
    readable_by_all: TOptionalFlagSpec = None,
    temp_root_path: TInputPath = "/tmp",
) -> t.ContextManager["Path"]:  # TODO docu/signature dedup?!
    """
    Create a fresh temporary directory and return its path. You must use it for a with-block; it will be removed after
    that block in usual cases. Otherwise, at a somewhat later time (usually after the process terminated). This removal
    will fail if you do not have permissions to do so.

    :param mode: The permission mode to set. See :py:meth:`change_access`.
    :param owner: The item owner. See :py:meth:`change_access`. Default: Current (effective) user.
    :param group: The item group. See :py:meth:`change_access`. Default: Current (effective) user's primary group.
    :param readable_by_all: See :py:meth:`change_access`. Default has no effect.
    :param temp_root_path: The parent directory where to create the temporary directory.
    """
    return Path.temp_dir(
        mode=mode, owner=owner, group=group, readable_by_all=readable_by_all, temp_root_path=temp_root_path
    )


def disk_usage(path: TInputPath) -> int:
    """
    Return the disk usage for a file or directory.

    :param path: The path.
    """
    path = Path(path)
    if not path.exists():
        raise IOError(errno.ENOENT, "No such file or directory", str(path))
    try:
        return int(
            re.search(r"^\d+", subprocess.check_output(["du", "--summarize", "--block-size=1", path]).decode()).group()
        )
    except subprocess.CalledProcessError:
        raise IOError(f"Unable to get disk usage for '{path}'") from None


@dataclasses.dataclass(frozen=True)
class _DiskSpaceInfo:
    total: int
    used: int
    free: int


def disk_space(fs_root_dir: TInputPath):
    df_output = subprocess.check_output(["df", "--block-size=1", fs_root_dir]).decode().split("\n")[1].split()
    return _DiskSpaceInfo(int(df_output[1]), int(df_output[2]), int(df_output[3]))


def byte_size_to_human_readable(size: int) -> str:
    """
    Return a human readable format for a size in bytes.

    :param size: The number to format in bytes.
    """
    result_unit = ""
    for unit in ["Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi", "Ri", "Qi"]:
        if size < 1024:
            break
        result_unit = unit
        size /= 1024
    return f"{round(size)} {result_unit}B"


class _Archive(abc.ABC):

    def __init__(self, archive_fileobj: io.RawIOBase):
        self._archive_fileobj = archive_fileobj

    @abc.abstractmethod
    def extract_all(self, destination: "Path") -> None:
        pass

    @classmethod
    @abc.abstractmethod
    def check_file_supported_by_begin(cls, begin: bytes) -> bool:
        pass

    @property
    @abc.abstractmethod
    def take_1st_level_default(self) -> bool:
        pass


class _ZipArchive(_Archive):

    take_1st_level_default = False

    def extract_all(self, destination):
        with zipfile.ZipFile(self._archive_fileobj) as archive:
            archive.extractall(destination)

    @classmethod
    def check_file_supported_by_begin(cls, begin):
        for zip_magic in [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"]:
            if begin.startswith(zip_magic):
                return True
        return False


class _TarArchive(_Archive):

    take_1st_level_default = True

    def extract_all(self, destination):
        with tarfile.open(fileobj=self._archive_fileobj) as archive:
            archive.extractall(destination)

    @classmethod
    def check_file_supported_by_begin(cls, begin):
        if begin[257:262] == b"ustar":
            return True

        if begin.startswith(b"\x1f\x8b"):
            try:
                import gzip

                return True
            except Exception:
                pass

        if begin.startswith(b"\x42\x5a\x68"):
            try:
                import bz2

                return True
            except Exception:
                pass

        if begin.startswith(b"\xfd\x37\x7a\x58\x5a\x00"):
            try:
                import lzma

                return True
            except Exception:
                pass

        return False


_archive_formats: t.Iterable[type[_Archive]] = (_ZipArchive, _TarArchive)


def _archive(archive_fileobj):
    begin = b""
    while True:
        c = archive_fileobj.read(1024)
        begin += c
        if c == b"" or len(begin) >= 1024:
            break
    archive_fileobj.seek(0)
    for archive_format in _archive_formats:
        if archive_format.check_file_supported_by_begin(begin):
            return archive_format(archive_fileobj)
    return None


def expand_archive(
    source: TInputPath | io.RawIOBase,
    destination: TInputPath,
    *,
    take_1st_level: bool | None = None,
    exist_ok: bool = False,
    mode: TModeSpec = True,
    owner: TOwnerSpec = True,
    group: TOwnerGroupSpec = True,
    readable_by_all: TOptionalFlagSpec = None,
    executable: TOptionalFlagSpec = None,
) -> "Path":
    """
    Expand an archive file (zip or tar-based) to a destination.

    :param source: The source archive to expand.
    :param destination: The destination path.
    :param take_1st_level: Whether to take the top-level item from the archive (must be the only one on top level)
                           and extract this one to the destination. If None: Depends on the archive format.
    :param exist_ok: Whether it is not an error if the destination path already exists (it will be removed then).
    :param mode: The permission mode to set. See :py:meth:`change_access`. Default: u=rw,g=r and also +x if the
                 source is executable.
    :param owner: The item owner. See :py:meth:`change_access`. Default: Current (effective) user.
    :param group: The item group. See :py:meth:`change_access`. Default: Current (effective) user's primary group.
    :param readable_by_all: See :py:meth:`change_access`. Default has no effect.
    :param executable: See :py:meth:`change_access`. Default has no effect.
    """
    destination = Path(destination)

    if destination.exists():
        if exist_ok:
            destination.remove()
        else:
            raise IOError(errno.EEXIST, "File exists", str(destination))

    if take_1st_level:
        with temp_dir(mode=0o700, temp_root_path=destination.parent) as temp_dir_path:
            temp_destination_path = temp_dir_path("x")
            expand_archive(
                source,
                temp_destination_path,
                take_1st_level=False,
                exist_ok=False,
                mode=mode,
                owner=owner,
                group=group,
                readable_by_all=readable_by_all,
                executable=executable,
            )
            fxf = list(temp_destination_path.iterdir())
            if len(fxf) != 1:
                raise IOError("take_1st_level was set, but there is not exactly one item on top level of the archive")
            fxf[0].move_to(destination, exist_ok=exist_ok)

    else:
        with contextlib.ExitStack() as stack:
            f_source = source
            if not hasattr(f_source, "read"):
                f_source = stack.enter_context(open(f_source, "rb"))

            with temp_dir(mode=0o700) as temp_dir_path:
                archive_fileobj = f_source
                archive_path = None
                if not (hasattr(f_source, "seekable") and f_source.seekable()):
                    archive_path = temp_dir_path("x")
                    archive_path.set_data(f_source)
                    archive_fileobj = None

                with contextlib.ExitStack() as stack_:
                    archive_fileobj_f = archive_fileobj
                    if archive_fileobj_f is None:
                        archive_fileobj_f = stack_.enter_context(open(archive_path, "rb"))
                    archive = _archive(archive_fileobj_f)
                    if not archive:
                        raise IOError(f"Does not contain a supported archive format: {source}")
                    archive_fileobj_f.seek(0)
                    if (take_1st_level is None) and archive.take_1st_level_default:
                        return expand_archive(
                            archive_fileobj_f,
                            destination,
                            take_1st_level=True,
                            exist_ok=exist_ok,
                            mode=mode,
                            owner=owner,
                            group=group,
                            readable_by_all=readable_by_all,
                            executable=executable,
                        )

                    destination.make_dir(mode=0o700)
                    archive.extract_all(destination)

            destination.change_access(
                mode=mode,
                owner=owner,
                group=group,
                readable_by_all=readable_by_all,
                executable=executable,
                recursive=True,
            )

    return destination


class OnRemovePassingFileSystemBoundary(enum.Enum):
    ERROR = enum.auto()
    CONTINUE_REMOVING_BEHIND_BOUNDARY = enum.auto()
    TRY_UNMOUNTING = enum.auto()
    TRY_UNMOUNTING_FORCEFULLY = enum.auto()


class OnRemoveError(enum.Enum):
    SKIP_AND_IGNORE = enum.auto()
    SKIP_AND_FAIL_LATER = enum.auto()
    FAIL_INSTANTLY = enum.auto()


class Path(pathlib.PosixPath):

    def expand_archive_to(
        self,
        destination: TInputPath,
        *,
        take_1st_level: bool = False,
        exist_ok: bool = False,
        mode: TModeSpec = True,
        owner: TOwnerSpec = True,
        group: TOwnerGroupSpec = True,
        readable_by_all: TOptionalFlagSpec = None,
        executable: TOptionalFlagSpec = None,
    ) -> "Path":
        """
        Expand this archive file (zip or tar-based) to a destination.

        :param destination: The destination path.
        :param take_1st_level: Whether to take the top-level item from the archive (must be the only one on top level)
                               and extract this one to the destination.
        :param exist_ok: Whether it is not an error if the destination path already exists (it will be removed then).
        :param mode: The permission mode to set. See :py:meth:`change_access`. Default: u=rw,g=r and also +x if the
                     source is executable.
        :param owner: The item owner. See :py:meth:`change_access`. Default: Current (effective) user.
        :param group: The item group. See :py:meth:`change_access`. Default: Current (effective) user's primary group.
        :param readable_by_all: See :py:meth:`change_access`. Default has no effect.
        :param executable: See :py:meth:`change_access`. Default has no effect.
        """
        return expand_archive(
            self,
            destination,
            take_1st_level=take_1st_level,
            exist_ok=exist_ok,
            mode=mode,
            owner=owner,
            group=group,
            readable_by_all=readable_by_all,
            executable=executable,
        )

    @classmethod
    def home_dir(cls, user: str | None = None) -> "Path":
        return cls(f"~{user or ''}").expanduser()

    @classmethod
    @contextlib.contextmanager
    def temp_dir(
        cls,
        *,
        mode: TModeSpec = 0o750,
        owner: TOwnerSpec = True,
        group: TOwnerGroupSpec = True,
        readable_by_all: TOptionalFlagSpec = None,
        temp_root_path: TInputPath = "/tmp",
    ) -> t.ContextManager["t.Self"]:
        """
        Create a fresh temporary directory and return its path. You must use it for a with-block; it will be removed
        after that block in usual cases. Otherwise at a somewhat later time (usually after the process terminated). This
        removal will fail if you do not have permissions to do so.

        :param mode: The permission mode to set. See :py:meth:`change_access`.
        :param owner: The item owner. See :py:meth:`change_access`. Default: Current (effective) user.
        :param group: The item group. See :py:meth:`change_access`. Default: Current (effective) user's primary group.
        :param readable_by_all: See :py:meth:`change_access`. Default has no effect.
        :param temp_root_path: The parent directory where to create the temporary directory.
        """
        temp_dir_path = cls(temp_root_path, _lang.unique_id()).make_dir(
            mode=mode, owner=owner, group=group, readable_by_all=readable_by_all
        )
        cleanup = _cleanup.add_cleanup_task(Path.remove, temp_dir_path, not_exist_ok=True)
        try:
            yield temp_dir_path
        finally:
            cleanup()

    def non_existent(self) -> bool:
        try:
            self.lstat()
            return False
        except IOError as ex:
            if ex.errno == errno.ENOENT:
                return True
            raise

    def change_access(
        self,
        mode: TModeSpec = None,
        *,
        follow_symlinks: bool = True,
        recursive: bool = False,
        owner: TOwnerSpec = None,
        group: TOwnerGroupSpec = None,
        readable_by_all: TOptionalFlagSpec = None,
        executable: TOptionalFlagSpec = None,
    ) -> "t.Self":
        """
        Change file permissions and ownership.

        :param mode: The permission mode to set. If `None`, leave it unchanged (unless some other flags are set).
        :param follow_symlinks: If this is a symlink, whether to change the permission settings of the target item
                                instead.
        :param recursive: Whether to apply the specified changes to the entire subtree (useful for directories).
        :param owner: The item owner.
                      If `True`, it's the (effective) current user. If `False`, leave it unchanged.
                      Otherwise either a UID or user name.
        :param group: The item group.
                      If `True`, it's the (effective) current user's primary group. If `False`, leave it unchanged.
                      Otherwise either a GID or group name.
        :param readable_by_all: If set, the mode will be extended to readable for all (and maybe executable).
        :param executable: Whether to set normal files to executable for everyone with read privileges. If `True` or
                           `False`, enable or disable this flag. If `None`, leave untouched.
        """
        if recursive and (follow_symlinks or not self.is_symlink()):
            try:
                for child_path in self.iterdir():
                    try:
                        child_path.change_access(
                            recursive=True,
                            mode=mode,
                            owner=owner,
                            group=group,
                            readable_by_all=readable_by_all,
                            executable=executable,
                            follow_symlinks=False,
                        )
                    except IOError as ex:
                        if ex.errno != errno.ENOENT:  # otherwise it was just removed meanwhile; we ignore that
                            raise
            except IOError as ex:
                if ex.errno != errno.ENOTDIR:
                    raise

        fd_stat = self.stat() if follow_symlinks else self.lstat()
        mode_int = Path.__parse_permission_mode(mode, False, fd_stat, readable_by_all, executable)
        owner_int = Path.__parse_ownership(owner, lambda name: pwd.getpwnam(name).pw_uid, os.geteuid(), -1)
        group_int = Path.__parse_ownership(group, lambda name: grp.getgrnam(name).gr_gid, os.getegid(), -1)
        aux_kwargs_dict = dict(follow_symlinks=False) if (not follow_symlinks and stat.S_ISLNK(fd_stat.st_mode)) else {}
        if mode_int != stat.S_IMODE(fd_stat.st_mode):
            Path.__change_access__call_ch_func(os.chmod, self, mode_int, **aux_kwargs_dict)
        if (owner_int not in (-1, fd_stat.st_uid)) or (group_int not in (-1, fd_stat.st_gid)):
            Path.__change_access__call_ch_func(os.chown, self, owner_int, group_int, **aux_kwargs_dict)
        return self

    def move_to(self, destination: TInputPath, *, exist_ok: bool = False) -> "Path":
        """
        Move the item at this path to a destination. Permission settings will be retained.

        :param destination: The destination path.
        :param exist_ok: Whether it is not an error if the destination path already exists (it will be removed then).
        TODO merge ?!
        """
        destination = Path(destination)

        if destination.exists():
            if exist_ok:
                destination.remove()
            else:
                raise IOError(errno.EEXIST, "File exists", str(destination))

        try:
            os.rename(self, destination)
            return destination
        except IOError as ex:
            if ex.errno != errno.EXDEV:
                raise

        Path.__copy(
            self,
            destination,
            remove_source=True,
            sparse=False,
            transfer_perms=True,
            mode=None,
            owner=None,
            group=None,
            readable_by_all=None,
            executable=None,
        )
        return destination

    def copy_to(
        self,
        destination: TInputPath,
        *,
        exist_ok: bool = False,
        merge: bool = False,
        sparse: bool = False,
        transfer_perms: bool = False,
        mode: TModeSpec = True,
        owner: TOwnerSpec = True,
        group: TOwnerGroupSpec = True,
        readable_by_all: TOptionalFlagSpec = None,
        executable: TOptionalFlagSpec = None,
    ) -> "Path":
        """
        Copy the item at this path to a destination.

        If you copy a directory, all settings (incl. permission flags, ...) are applied to the entire tree.

        :param destination: The destination path.
        :param exist_ok: Whether it is not an error if the destination path already exists (per default it will be
                         removed then).
        :param merge: Whether to merge the source directory file-wise into the destination directory, instead of relying
                      on an empty destination.
        :param sparse: If to copy in sparse mode. Usually not needed.
        :param transfer_perms: Whether to transfer the permission settings of the source file.
        :param mode: The permission mode to set. See :py:meth:`change_access`. Default: u=rw,g=r and also +x if the
                     source is executable.
        :param owner: The item owner. See :py:meth:`change_access`. Default: Current (effective) user.
        :param group: The item group. See :py:meth:`change_access`. Default: Current (effective) user's primary group.
        :param readable_by_all: See :py:meth:`change_access`. Default has no effect.
        :param executable: See :py:meth:`change_access`. Default has no effect.
        """
        destination = Path(destination)

        if destination.exists() and not merge:
            if not exist_ok:
                raise IOError(errno.EEXIST, "File exists", str(destination))
            destination.remove()

        Path.__copy(
            self,
            destination,
            remove_source=False,
            sparse=sparse,
            transfer_perms=transfer_perms,
            mode=mode,
            owner=owner,
            group=group,
            readable_by_all=readable_by_all,
            executable=executable,
        )
        return destination

    def set_data(
        self,
        data: t.AnyStr | io.RawIOBase,
        *,
        exist_ok: bool = True,
        preserve_perms: bool = False,
        mode: TModeSpec = 0o640,
        owner: TOwnerSpec = True,
        group: TOwnerGroupSpec = True,
        readable_by_all: TOptionalFlagSpec = None,
        executable: TOptionalFlagSpec = None,
    ) -> "t.Self":
        """
        Write data into a file at this path and apply some permission settings.

        Per default, those permission settings will be applied even if the file already exists (see `preserve_perms`)!

        With `readable_by_all=True` and `preserve_perms=True` this function behaves like :py:meth:`write_text` or
        :py:meth:`write_bytes`.

        :param data: The data to write.
        :param exist_ok: Whether it is okay if this file already exists.
        :param preserve_perms: Whether to leave permission settings untouched if the file already exists.
        :param mode: The permission mode to set. See :py:meth:`change_access`.
        :param owner: The item owner. See :py:meth:`change_access`. Default: Current (effective) user.
        :param group: The item group. See :py:meth:`change_access`. Default: Current (effective) user's primary group.
        :param readable_by_all: See :py:meth:`change_access`. Default has no effect.
        :param executable: See :py:meth:`change_access`. Default has no effect.
        """
        self.__set_data(
            data or b"",
            exist_ok=exist_ok,
            preserve_perms=preserve_perms,
            mode=mode,
            owner=owner,
            group=group,
            readable_by_all=readable_by_all,
            executable=executable,
        )
        return self

    def append_data(
        self,
        data: t.AnyStr | io.RawIOBase,
        *,
        exist_ok: bool = True,
        ensure_head_newline: bool = True,
        ensure_tail_newline: bool = True,
        preserve_perms: bool = False,
        mode: TModeSpec = 0o640,
        owner: TOwnerSpec = True,
        group: TOwnerGroupSpec = True,
        readable_by_all: TOptionalFlagSpec = None,
        executable: TOptionalFlagSpec = None,
    ) -> "t.Self":
        """
        Appends data to the end of the file at this path and apply some permission settings.

        Per default, those permission settings will be applied even if the file already exists (see `preserve_perms`)!

        :param data: The data to write.
        :param exist_ok: Whether it is okay if this file already exists.
        :param ensure_head_newline: For appending, whether to ensure a newline where `data` begins.
        :param ensure_tail_newline: For appending, whether to ensure a newline where `data` end.
        :param preserve_perms: Whether to leave permission settings untouched if the file already exists.
        :param mode: The permission mode to set. See :py:meth:`change_access`.
        :param owner: The item owner. See :py:meth:`change_access`. Default: Current (effective) user.
        :param group: The item group. See :py:meth:`change_access`. Default: Current (effective) user's primary group.
        :param readable_by_all: See :py:meth:`change_access`. Default has no effect.
        :param executable: See :py:meth:`change_access`. Default has no effect.
        """
        self.__set_data(
            data or b"",
            exist_ok=exist_ok,
            append=True,
            ensure_head_newline=ensure_head_newline,
            ensure_tail_newline=ensure_tail_newline,
            preserve_perms=preserve_perms,
            mode=mode,
            owner=owner,
            group=group,
            readable_by_all=readable_by_all,
            executable=executable,
        )
        return self

    def make_dir(
        self,
        *,
        until: TInputPath | None = None,
        exist_ok: bool = False,
        parent_exist_ok: bool = True,
        preserve_perms: bool = False,
        mode: TModeSpec = 0o750,
        owner: TOwnerSpec = True,
        group: TOwnerGroupSpec = True,
        readable_by_all: TOptionalFlagSpec = None,
    ) -> "Path":
        """
        Create a directory at this path.

        With `readable_by_all=True` and `preserve_perms=True` this function behaves like :py:meth:`mkdir`.

        :param until: Similar to `parents`, but only creates all super-directories up to (excluding) that one.
        :param exist_ok: Whether it is okay if this directory already exists (it will set permission related attributes
                         anyway).
        :param parent_exist_ok: Whether it is okay if a *parent* directory up to `until` already exists (it will NOT set
                                permission related attributes for them).
        :param preserve_perms: Whether to leave permission settings untouched if the directory already exists.
        :param mode: The permission mode to set. See :py:meth:`change_access`.
        :param owner: The item owner. See :py:meth:`change_access`. Default: Current (effective) user.
        :param group: The item group. See :py:meth:`change_access`. Default: Current (effective) user's primary group.
        :param readable_by_all: See :py:meth:`change_access`. Default has no effect.
        """
        if until:
            until = Path(until)
            parent_resolved = self.parent.resolve(strict=False)
            until_resolved = until.resolve(strict=False)
            if parent_resolved.is_relative_to(until_resolved) and parent_resolved != until_resolved:
                if not (self.parent.exists() and parent_exist_ok):
                    self.parent.make_dir(
                        mode=mode,
                        until=until,
                        exist_ok=parent_exist_ok,
                        parent_exist_ok=parent_exist_ok,
                        preserve_perms=preserve_perms,
                        owner=owner,
                        group=group,
                        readable_by_all=readable_by_all,
                    )

        self.__set_data(
            None,
            as_directory=True,
            exist_ok=exist_ok,
            preserve_perms=preserve_perms,
            mode=mode,
            owner=owner,
            group=group,
            readable_by_all=readable_by_all,
        )
        return self

    def make_file(
        self,
        *,
        exist_ok: bool = True,
        preserve_perms: bool = False,
        mode: TModeSpec = 0o640,
        owner: TOwnerSpec = True,
        group: TOwnerGroupSpec = True,
        readable_by_all: TOptionalFlagSpec = None,
        executable: TOptionalFlagSpec = None,
    ) -> "Path":
        """
        Create a file at this path.

        With `readable_by_all=True` and `preserve_perms=True` this function behaves like :py:meth:`touch`.

        :param exist_ok: Whether it is okay if this file already exists (it will set permission related attributes
                         anyway).
        :param preserve_perms: Whether to leave permission settings untouched if the file already exists.
        :param mode: The permission mode to set. See :py:meth:`change_access`.
        :param owner: The item owner. See :py:meth:`change_access`. Default: Current (effective) user.
        :param group: The item group. See :py:meth:`change_access`. Default: Current (effective) user's primary group.
        :param readable_by_all: See :py:meth:`change_access`. Default has no effect.
        :param executable: See :py:meth:`change_access`. Default has no effect.
        """
        self.__set_data(
            None,
            exist_ok=exist_ok,
            preserve_perms=preserve_perms,
            mode=mode,
            owner=owner,
            group=group,
            readable_by_all=readable_by_all,
            executable=executable,
        )
        return self

    def apply_substitutions(
        self,
        *substitutions: tuple[str, str],
        source: TInputPath = None,
        preserve_perms: bool = True,
        mode: TModeSpec = 0o640,
        owner: TOwnerSpec = True,
        group: TOwnerGroupSpec = True,
        readable_by_all: TOptionalFlagSpec = None,
        executable: TOptionalFlagSpec = None,
    ) -> "Path":
        """
        Apply regexp substitution patterns to this file.

        :param substitutions: Each substitution is a tuple of the match pattern and the replacement pattern.
        :param source: The source path to read the original content from. Default: This file.
        :param preserve_perms: Whether to leave permission settings untouched if the file already exists.
        :param mode: The permission mode to set. See :py:meth:`change_access`.
        :param owner: The item owner. See :py:meth:`change_access`. Default: Current (effective) user.
        :param group: The item group. See :py:meth:`change_access`. Default: Current (effective) user's primary group.
        :param readable_by_all: See :py:meth:`change_access`. Default has no effect.
        :param executable: See :py:meth:`change_access`. Default has no effect.
        """
        content = Path(source or self).read_text()
        for pattern, substitution in substitutions:
            content = re.sub(pattern, substitution, content, flags=re.MULTILINE)
        self.set_data(
            content,
            preserve_perms=preserve_perms,
            mode=mode,
            owner=owner,
            group=group,
            readable_by_all=readable_by_all,
            executable=executable,
        )
        return self

    def remove(
        self,
        *,
        not_exist_ok: bool = False,
        on_error: t.Callable | OnRemoveError = OnRemoveError.SKIP_AND_FAIL_LATER,
        on_passing_filesystem_boundary: (
            t.Callable | OnRemovePassingFileSystemBoundary
        ) = OnRemovePassingFileSystemBoundary.TRY_UNMOUNTING,
    ) -> "t.Self":
        """
        Remove the item at this path (for directories, including the entire tree).

        :param not_exist_ok: Whether it is okay if this item does not exist.
        :param on_error: How to behave when errors occur.
        :param on_passing_filesystem_boundary: How to behave when the removal of a directory tree would pass a
                                               filesystem boundary (i.e. if there is some other filesystem mounted
                                               somewhere in the tree).
        """
        # guarded against symlink races; idea stolen from shutil

        on_error = self.__remove__on_error_func(on_error)
        on_passing_filesystem_boundary = self.__remove__on_passing_filesystem_boundary_func(
            on_passing_filesystem_boundary
        )

        had_errors = [False]
        self_str = str(self)  # TODO noh what about bytes-based Path's? (see also os.fsdecode)
        self_fd, self_stat_samestat, self_stat = self.__remove__open(self_str, not_exist_ok, on_error, had_errors)
        if self_fd is None:
            return self
        self_fd_closed = False

        try:
            if self_stat_samestat and stat.S_ISDIR(self_stat.st_mode):
                self.__remove__subtree(
                    self_fd, self_stat.st_dev, self_str, on_passing_filesystem_boundary, on_error, had_errors
                )
                try:
                    os.close(self_fd)
                    self_fd_closed = True
                    os.rmdir(self_str)
                except IOError as ex:
                    had_errors[0] = had_errors[0] or on_error(self_str, ex)

            else:
                try:
                    os.unlink(self_str)
                except IOError as ex:
                    had_errors[0] = had_errors[0] or on_error(self_str, ex)

        finally:
            if not self_fd_closed:
                os.close(self_fd)

        if had_errors[0]:
            raise IOError(f"there were errors while removing {self_str!r}")

        return self

    def relative_to(self, other: TInputPath, strict: bool = True) -> "Path":
        other = Path(other)
        base = Path(".")
        if not strict:
            max_depth = min(Path.__path_depth(self), Path.__path_depth(other))
            p1 = Path.__path_trimmed_to_depth(self, max_depth)
            p2 = Path.__path_trimmed_to_depth(other, max_depth)
            while p1 != p2:
                p1 = p1.parent
                p2 = p2.parent
            common_depth = Path.__path_depth(p1)
            for _ in range(Path.__path_depth(other) - common_depth):
                base = base / ".."
            other = p1
        return base / Path(pathlib.Path(self).relative_to(other))

    def iterdir(self) -> t.Iterable["Path"]:
        """
        Iterate over the files/subdirectories/etc in this directory.

        Does not include the special items `.` and `..`.
        """
        return super().iterdir()

    def __call__(self, *paths: TInputPath) -> "Path":
        """
        Return a :py:class:`Path` for an input path. The input path will always be interpreted as relative to this
        path!

        :param paths: The input path (could also be a string or pathlib.Path). If multiple ones are specified, they
        get concatenated.
        """
        result = self
        for path in paths:
            if path:
                path = Path(path)
                if path.is_absolute():
                    path = path.relative_to("/")
                result /= path
        return result

    def __to_json_dict__(self):
        return {"s": str(self)}

    @staticmethod
    def __from_json_dict__(json_dict):
        return Path(json_dict["s"])

    @staticmethod
    def __remove__on_error_func(on_error: t.Callable | OnRemoveError) -> t.Callable:
        if callable(on_error):
            on_error_func = on_error
        elif on_error == OnRemoveError.FAIL_INSTANTLY:

            def on_error_func(path, ex):
                raise

        elif on_error == OnRemoveError.SKIP_AND_FAIL_LATER:

            def on_error_func(path, ex):
                return True

        elif on_error == OnRemoveError.SKIP_AND_IGNORE:

            def on_error_func(path, ex):
                pass

        else:
            raise ValueError(f"unsupported on_error: {on_error!r}")
        return on_error_func

    @staticmethod
    def __remove__on_passing_filesystem_boundary_func(
        on_passing_filesystem_boundary: t.Callable | OnRemovePassingFileSystemBoundary,
    ) -> t.Callable:
        if callable(on_passing_filesystem_boundary):
            on_passing_filesystem_boundary_func = on_passing_filesystem_boundary
        elif on_passing_filesystem_boundary == OnRemovePassingFileSystemBoundary.CONTINUE_REMOVING_BEHIND_BOUNDARY:

            def on_passing_filesystem_boundary_func(path):
                pass

        elif on_passing_filesystem_boundary == OnRemovePassingFileSystemBoundary.ERROR:

            def on_passing_filesystem_boundary_func(path):
                raise IOError(f"filesystem boundary passed with {path!r}")

        elif on_passing_filesystem_boundary == OnRemovePassingFileSystemBoundary.TRY_UNMOUNTING:

            def on_passing_filesystem_boundary_func(path):
                subprocess.check_call(["umount", path])

        elif on_passing_filesystem_boundary == OnRemovePassingFileSystemBoundary.TRY_UNMOUNTING_FORCEFULLY:

            def on_passing_filesystem_boundary_func(path):
                subprocess.check_call(["umount", "-f", path])

        else:
            raise ValueError(f"unsupported on_passing_filesystem_boundary: {on_passing_filesystem_boundary!r}")
        return on_passing_filesystem_boundary_func

    @staticmethod
    def __remove__subtree(dir_fd, dir_dev_id, dir_path, on_passing_filesystem_boundary, on_error, had_errors):
        # inspired by shutil
        try:
            with os.scandir(dir_fd) as _:
                children = list(_)
        except IOError as ex:
            had_errors[0] = had_errors[0] or on_error(dir_path, ex)
            return

        for child in children:
            child_path = f"{dir_path}/{child.name}"

            try:
                child_orig_stat = child.stat(follow_symlinks=False)
                if dir_dev_id != child_orig_stat.st_dev:
                    on_passing_filesystem_boundary(child_path)
            except IOError as ex:
                had_errors[0] = had_errors[0] or on_error(child_path, ex)
                continue

            try:
                child_is_dir = child.is_dir(follow_symlinks=False) and stat.S_ISDIR(child_orig_stat.st_mode)
            except IOError:
                child_is_dir = False

            if child_is_dir:
                try:
                    child_fd = os.open(child.name, os.O_RDONLY, dir_fd=dir_fd)
                    child_fd_closed = False
                except IOError as ex:
                    had_errors[0] = had_errors[0] or on_error(child_path, ex)
                else:
                    try:
                        if os.path.samestat(child_orig_stat, os.fstat(child_fd)):
                            Path.__remove__subtree(
                                child_fd,
                                child_orig_stat.st_dev,
                                child_path,
                                on_passing_filesystem_boundary,
                                on_error,
                                had_errors,
                            )
                            try:
                                os.close(child_fd)
                                child_fd_closed = True
                                os.rmdir(child.name, dir_fd=dir_fd)
                            except IOError as ex:
                                had_errors[0] = had_errors[0] or on_error(child_path, ex)
                        else:
                            try:
                                os.unlink(child.name, dir_fd=dir_fd)
                            except IOError as ex:
                                had_errors[0] = had_errors[0] or on_error(child_path, ex)
                    finally:
                        if not child_fd_closed:
                            os.close(child_fd)
            else:
                try:
                    os.unlink(child.name, dir_fd=dir_fd)
                except IOError as ex:
                    had_errors[0] = had_errors[0] or on_error(child_path, ex)

    @staticmethod
    def __remove__open(path, not_exist_ok, on_error, had_errors):
        try:
            orig_stat = os.lstat(path)
            fd = os.open(path, os.O_RDONLY)
        except Exception as ex:
            if not (not_exist_ok and isinstance(ex, IOError) and ex.errno == errno.ENOENT):
                had_errors[0] = had_errors[0] or on_error(path, ex)
            return None, None, None

        try:
            fstat = os.fstat(fd)
            return fd, os.path.samestat(fstat, orig_stat), fstat
        except Exception:
            os.close(fd)
            raise

    @staticmethod
    def __change_access__call_ch_func(func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except NotImplementedError:
            pass
        except IOError as ex:
            if ex.errno != errno.EROFS:
                raise

    @staticmethod
    def __copy(
        source: "Path",
        destination: "Path",
        *,
        remove_source: bool,
        sparse: bool,
        transfer_perms: bool,
        mode: TModeSpec,
        owner: TOwnerSpec,
        group: TOwnerGroupSpec,
        readable_by_all: TOptionalFlagSpec,
        executable: TOptionalFlagSpec,
    ) -> None:

        source_stat = source.stat(follow_symlinks=False)

        if transfer_perms:
            mode = stat.S_IMODE(source_stat.st_mode)
            owner, group = source_stat.st_uid, source_stat.st_gid
            readable_by_all = executable = None

        if source.is_symlink():
            os.symlink(os.readlink(source), destination)

        elif source.is_dir():
            destination.make_dir(exist_ok=True, mode=mode, owner=owner, group=group, readable_by_all=readable_by_all)
            for source_child in source.iterdir():
                Path.__copy(
                    source_child,
                    destination / source_child.name,
                    remove_source=remove_source,
                    sparse=sparse,
                    transfer_perms=transfer_perms,
                    mode=mode,
                    owner=owner,
                    group=group,
                    readable_by_all=readable_by_all,
                    executable=executable,
                )

        elif source.is_file():
            if sparse:
                with Path.__fallback_safely_create(
                    destination,
                    mode=mode,
                    owner=owner,
                    group=group,
                    readable_by_all=readable_by_all,
                    executable=executable,
                ):
                    destination.touch(mode=0o200, exist_ok=False)
                    subprocess.check_call(["cp", "--sparse=always", source, destination])
            else:
                with open(source, "rb") as source_f:
                    destination.set_data(
                        source_f,
                        exist_ok=True,
                        mode=mode,
                        owner=owner,
                        group=group,
                        readable_by_all=readable_by_all,
                        executable=executable,
                    )

        elif source.is_char_device() or source.is_block_device():
            with Path.__fallback_safely_create(
                destination, mode=mode, owner=owner, group=group, readable_by_all=readable_by_all, executable=executable
            ):
                os.mknod(
                    destination,
                    mode=0o200 | (stat.S_IFBLK if source.is_block_device() else stat.S_IFCHR),
                    device=source_stat.st_rdev,
                )
        elif source.is_fifo():
            with Path.__fallback_safely_create(
                destination, mode=mode, owner=owner, group=group, readable_by_all=readable_by_all, executable=executable
            ):
                os.mkfifo(destination, mode=0o200)
        elif source.is_socket():
            pass

        else:
            raise IOError(f"unsupported filesystem item kind {source!r}")

        if remove_source:
            source.remove()

    @staticmethod
    @contextlib.contextmanager
    def __fallback_safely_create(
        destination: "Path",
        *,
        mode: TModeSpec = 0o640,
        owner: TOwnerSpec = True,
        group: TOwnerGroupSpec = True,
        readable_by_all: TOptionalFlagSpec = None,
        executable: TOptionalFlagSpec = None,
    ):
        destination.remove(not_exist_ok=True)
        try:
            yield destination
        except Exception:
            destination.remove(not_exist_ok=True)
            raise
        finally:
            destination.change_access(
                mode, owner=owner, group=group, readable_by_all=readable_by_all, executable=executable
            )

    def __set_data(
        self,
        data: t.AnyStr | io.RawIOBase | None,
        *,
        as_directory: bool = False,
        exist_ok: bool = True,
        not_exist_ok: bool = True,
        append: bool = False,
        ensure_head_newline: bool = True,
        ensure_tail_newline: bool = True,
        preserve_perms: bool = False,
        mode: TModeSpec = 0o640,
        owner: TOwnerSpec = True,
        group: TOwnerGroupSpec = True,
        readable_by_all: TOptionalFlagSpec = None,
        executable: TOptionalFlagSpec = None,
    ) -> None:
        fd, was_created, is_readonly = self.__open(
            exist_ok=exist_ok, not_exist_ok=not_exist_ok, create_directory=as_directory
        )
        try:
            fd_stat = os.fstat(fd)
            if as_directory and stat.S_ISREG(fd_stat.st_mode):
                raise IOError(errno.ENOTDIR, "Not a directory", str(self))
            mode_int = Path.__parse_permission_mode(mode, was_created, fd_stat, readable_by_all, executable)
            owner_int = Path.__parse_ownership(
                owner, lambda name: pwd.getpwnam(name).pw_uid, os.geteuid(), fd_stat.st_uid
            )
            group_int = Path.__parse_ownership(
                group, lambda name: grp.getgrnam(name).gr_gid, os.getegid(), fd_stat.st_gid
            )
            if was_created or not preserve_perms:
                mode_actually_changes = mode_int != stat.S_IMODE(fd_stat.st_mode)
                user_or_group_actually_changes = owner_int != fd_stat.st_uid or group_int != fd_stat.st_gid
                try:
                    if not was_created and mode_actually_changes and user_or_group_actually_changes:
                        os.fchmod(fd, 0)
                    if user_or_group_actually_changes:
                        os.fchown(fd, owner_int, group_int)
                    if mode_actually_changes:
                        os.fchmod(fd, mode_int)
                except IOError as ex:
                    if ex.errno != errno.EACCES:
                        raise
            if data is not None:
                if is_readonly:
                    raise IOError(errno.EACCES, "Permission denied", str(self))
                if not append:
                    os.ftruncate(fd, 0)

                if isinstance(data, str):
                    data = data.encode()
                if isinstance(data, bytes):
                    data = io.BytesIO(data)

                had_read_data = False
                ends_with_newline = append and Path.__file_ends_with_newline(fd)
                while True:
                    buffer = data.read(32 * 1024**2)
                    if isinstance(buffer, str):
                        buffer = buffer.encode()
                    if buffer == b"":
                        break
                    if buffer:
                        if (
                            not had_read_data
                            and append
                            and ensure_head_newline
                            and not (buffer.startswith(b"\n") or ends_with_newline)
                        ):
                            os.write(fd, b"\n")
                        had_read_data = True
                        os.write(fd, buffer)
                        ends_with_newline = append and buffer.endswith(b"\n")
                if append and ensure_tail_newline and not ends_with_newline:
                    os.write(fd, b"\n")
        finally:
            os.close(fd)

    def __open(self, *, exist_ok: bool, not_exist_ok: bool, create_directory: bool) -> tuple[int, bool, bool]:
        was_created = False
        while True:
            if not self.parent.exists():
                raise IOError(errno.ENOENT, "No such file or directory", str(self))

            if not_exist_ok:
                if create_directory:
                    try:
                        was_created = not self.is_dir() or self.is_symlink()
                        if was_created or not exist_ok:
                            self.mkdir(0o700, parents=False, exist_ok=exist_ok)
                        exist_ok = True
                    except IOError as ex:
                        if ex.errno != errno.EEXIST:
                            raise
                else:
                    try:
                        return (
                            os.open(self, os.O_CLOEXEC | os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0),
                            True,
                            False,
                        )
                    except IOError as ex:
                        if ex.errno != errno.EEXIST:
                            raise

            try:
                result = os.open(self, os.O_CLOEXEC | os.O_RDWR, 0), False, False
                if not exist_ok:
                    os.close(result[0])
                    raise IOError(errno.EEXIST, "File exists", str(self))
                return result
            except IOError as ex:
                if (ex.errno == errno.EISDIR) or (ex.errno == errno.ENXIO):
                    if not exist_ok:
                        raise IOError(errno.EEXIST, "File exists", str(self)) from None
                    try:
                        return os.open(self, os.O_CLOEXEC | os.O_RDONLY, 0), was_created, True
                    except IOError as ex_:
                        if (ex_.errno != errno.ENOENT) or not not_exist_ok:
                            raise

                if (ex.errno != errno.ENOENT) or not not_exist_ok:
                    raise

    @staticmethod
    def __file_ends_with_newline(fd: int) -> bool:
        try:
            os.lseek(fd, -1, os.SEEK_END)
            return os.read(fd, 1) == b"\n"
        except IOError as ex:
            if ex.errno != errno.EINVAL:
                raise
        return False

    @staticmethod
    def __parse_permission_mode(
        mode: TModeSpec,
        was_created: bool,
        fd_stat: os.stat_result,
        readable_by_all: TOptionalFlagSpec,
        executable: TOptionalFlagSpec,
    ) -> int:
        if isinstance(mode, str):
            try:
                mode = int(mode, 8)
            except ValueError:
                pass

        if mode is None or mode is False or isinstance(mode, str):
            result = 0o640 if was_created else stat.S_IMODE(fd_stat.st_mode)
            if isinstance(mode, str):
                result = Path.__parse_permission_mode__str_helper(mode, result, stat.S_ISDIR(fd_stat.st_mode))

        elif mode is True:
            if stat.S_IMODE(fd_stat.st_mode) & stat.S_IXUSR:
                result = 0o750
            else:
                result = 0o640

        elif isinstance(mode, int):
            # chmod manpage about setuid/setgid bits: you can set (but not clear) the bits with a numeric mode
            result = mode | (stat.S_IMODE(fd_stat.st_mode) & 0o6000)

        else:
            raise ValueError(f"unsupported file permissions value type {mode!r}")

        if readable_by_all is not None:
            if not readable_by_all:
                raise ValueError("readable_by_all=False unsupported")
            result |= stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
            if result & stat.S_IXUSR:
                result |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

        if executable is not None:
            if executable:
                if result & stat.S_IRUSR:
                    result |= stat.S_IXUSR
                if result & stat.S_IRGRP:
                    result |= stat.S_IXGRP
                if result & stat.S_IROTH:
                    result |= stat.S_IXOTH
            else:
                result &= ~0o111

        return result

    @staticmethod
    def __parse_permission_mode__str_helper(mode_str: str, current_mode: int, is_directory: bool) -> int:
        result = current_mode
        for part in filter(None, [x.strip() for x in mode_str.split(",")]):
            part_match = Path.__parse_permission_mode__part_re.match(part)
            if not part_match:
                raise ValueError(f"invalid file permissions value part {part!r}")
            lvalue, operator, rvalue = part_match.groups()
            if not operator:
                lvalue, operator, rvalue = "", "=", lvalue + rvalue
            lvalue = lvalue or "a"
            lmask = Path.__parse_permission_mode__str_helper__lmask(lvalue)
            rmask = Path.__parse_permission_mode__str_helper__rmask(rvalue, result, is_directory)
            if operator == "+":
                result = result | (lmask & rmask)
            elif operator == "-":
                result = result & ~(lmask & rmask)
            elif operator == "=":
                # chmod manpage: chmod preserves a directory's set-user-ID and set-group-ID bits unless you explicitly
                # specify otherwise
                preserve_s = 0 if (is_directory and ("s" in rvalue)) else (result & 0o6000)
                result = result & ~lmask | preserve_s | (lmask & rmask)
        return result

    __parse_permission_mode__part_re = re.compile("([ugoa]*)([+=-]?)([ugorwxXst]*)")

    @staticmethod
    def __parse_permission_mode__str_helper__lmask(lvalue: str) -> int:
        result = 0
        for lchar in lvalue:
            if lchar == "u":
                result |= 0o4700
            elif lchar == "g":
                result |= 0o2070
            elif lchar == "o":
                result |= 0o1007
            elif lchar == "a":
                result |= 0o7777
            else:
                raise ValueError(f"invalid character {lchar!r} in file permissions lvalue {lvalue!r}")
        return result

    @staticmethod
    def __parse_permission_mode__str_helper__rmask(rvalue: str, current_mode: int, is_directory: bool) -> int:
        result = 0
        for rchar in rvalue:
            if rchar in "ugo":
                result |= Path.__parse_permission_mode__str_helper__expand(current_mode, rchar)
            elif rchar == "X":
                if is_directory or (current_mode & 0o111):
                    result |= 0o111
            else:
                result |= Path.__parse_permission_mode__rmask_for_letters[rchar]
        return result

    __parse_permission_mode__rmask_for_letters = {
        "r": 0o444,
        "w": 0o222,
        "x": 0o111,
        "s": 0o6000,
        "t": 0o1000,
    }

    @staticmethod
    def __parse_permission_mode__str_helper__expand(mode: int, lvalue: str) -> int:
        result = Path.__parse_permission_mode__str_helper__lmask(lvalue) & mode
        for i in range(3):
            i_val = 2**i
            is_set = False
            for j in range(3):
                j_val = 8**j
                ji_val = j_val * i_val
                is_set = result & ji_val
                if is_set:
                    break
            if is_set:
                for j in range(3):
                    j_val = 8**j
                    ji_val = j_val * i_val
                    result |= ji_val
        return result

    @staticmethod
    def __parse_ownership(
        owner: TOwnerSpec | TOwnerGroupSpec, lookup_func: t.Callable, true_result: int, none_result: int
    ) -> int:
        if owner is None:
            return none_result
        if owner is True:
            return true_result
        if isinstance(owner, int):
            return owner
        if isinstance(owner, str):
            return lookup_func(owner)
        raise ValueError(f"unsupported file owner/group value type {owner!r}")

    @staticmethod
    def __path_depth(path: pathlib.Path) -> int:
        if path == path.parent:
            return 0
        return Path.__path_depth(path.parent) + 1

    @staticmethod
    def __path_trimmed_to_depth(path: pathlib.Path, max_depth: int) -> "Path":
        for _ in range(Path.__path_depth(path) - max_depth):
            path = path.parent
        return path
