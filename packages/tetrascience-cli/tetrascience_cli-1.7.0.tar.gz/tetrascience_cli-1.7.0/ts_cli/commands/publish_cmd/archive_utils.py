import io
import os
import zipfile
from pathlib import Path
from typing import Iterable, Union

from ts_cli.util.files import copy

UNIX_PERMISSION_MASK = 0xFFFF


def abs_path_relative_to(relative_path, relative_to):
    """
    Join the two paths, and then provide the absolute path
    :param relative_path:
    :param relative_to:
    :return:
    """
    return os.path.abspath(
        Path(
            Path(relative_to).expanduser(),
            Path(relative_path).expanduser(),
        )
    )


def some_match(path, patterns, relative_to):
    """
    Returns true if there is some pattern that points to the same path as `path`
    :param path:
    :param patterns:
    :param relative_to:
    :return:
    """
    absolute_path = abs_path_relative_to(relative_to=relative_to, relative_path=path)
    matches = map(
        lambda pattern: absolute_path
        == abs_path_relative_to(relative_path=pattern, relative_to=relative_to),
        patterns,
    )
    return any(matches)


def included(path, *, inclusions, exclusions, relative_to):
    """
    Return true if file is not excluded or is explicitly included
    :param path:
    :param inclusions:
    :param exclusions:
    :param relative_to:
    :return:
    """
    return (not some_match(path, exclusions, relative_to)) or some_match(
        path, inclusions, relative_to
    )


def iterate_directory_inclusions(
    path: Union[str, Path],
    *,
    exclusions: Iterable[str],
    inclusions: Iterable[str],
):
    """
    Yields the relative file path for every file that is included
    :param path:
    :param exclusions:
    :param inclusions:
    :return:
    """
    if included(".", inclusions=inclusions, exclusions=exclusions, relative_to=path):
        for root, folders, files in os.walk(path, topdown=True):
            removals = set()
            for folder in folders:
                local_path = os.path.join(root, folder)
                relative_path = os.path.relpath(local_path, path)
                if not included(
                    relative_path,
                    inclusions=inclusions,
                    exclusions=exclusions,
                    relative_to=path,
                ):
                    removals.add(folder)
            for removal in removals:
                folders.remove(removal)

            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, os.path.join(path))
                if included(
                    relative_path,
                    inclusions=inclusions,
                    exclusions=exclusions,
                    relative_to=path,
                ):
                    yield relative_path


def copy_included_files_to(
    *,
    src_dir: str,
    dst_dir: str,
    exclusions: Iterable[str],
    inclusions: Iterable[str],
):
    """
    Copies the included files from `src_dir` to `dst_dir`
    :param src_dir:
    :param dst_dir:
    :param exclusions:
    :param inclusions:
    :return:
    """
    for relative_path in iterate_directory_inclusions(
        path=src_dir, exclusions=exclusions, inclusions=inclusions
    ):
        copy(src=Path(src_dir, relative_path), dst=Path(dst_dir, relative_path))


def write_file_to_archive(
    zip_archive: zipfile.ZipFile,
    local_path: Union[str, Path],
    relative_path: Union[str, Path],
):
    st = os.stat(local_path)
    mode = st.st_mode
    # For files: ensure all have r--, set x if set for owner
    new_mode = mode
    # Set read to all
    new_mode |= 0o444
    # Set execute for all if owner had it
    if mode & 0o100:
        new_mode |= 0o111
    zi = zipfile.ZipInfo(relative_path)
    zi.external_attr = (
        new_mode & UNIX_PERMISSION_MASK
    ) << 16  # upper 16 bits are unix permissions
    with open(local_path, "rb") as f:
        zip_archive.writestr(zi, f.read())


def write_folder_to_archive(
    zip_archive: zipfile.ZipFile,
    local_path: Union[str, Path],
    relative_path: Union[str, Path],
):
    st = os.stat(local_path)
    mode = st.st_mode
    # For dirs: ensure all have r-x
    new_mode = mode | 0o555  # add r-x for all
    zi = zipfile.ZipInfo(relative_path + "/")
    zi.external_attr = (
        new_mode & UNIX_PERMISSION_MASK
    ) << 16  # upper 16 bits are unix permissions
    zip_archive.writestr(zi, b"")


def add_directory_to_archive(
    zip_archive: zipfile.ZipFile,
    path: Union[str, Path],
) -> zipfile.ZipFile:
    """
    Copies all files under `path` to the archive
    :param zip_archive:
    :param path:
    :return:
    """
    for root, folders, files in os.walk(path, topdown=True):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, os.path.join(path))
            write_file_to_archive(zip_archive, local_path, relative_path)
        for folder in folders:
            local_path = os.path.join(root, folder)
            relative_path = os.path.relpath(local_path, os.path.join(path))
            write_folder_to_archive(zip_archive, local_path, relative_path)
    return zip_archive


def compress_directory(directory: Union[str, Path]):
    """
    Adds the directory to a zip file, and return the zip file's bytes
    :param directory:
    :return:
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, True) as zip_archive:
        add_directory_to_archive(
            zip_archive,
            directory,
        )
    return zip_buffer.getvalue()
