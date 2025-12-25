import fnmatch
import os
import shutil
from typing import Protocol

from iker.common.utils import logger
from iker.common.utils.sequtils import last, last_or_none, tail_iter
from iker.common.utils.strutils import is_empty

__all__ = [
    "extension",
    "extensions",
    "stem",
    "expanded_path",
    "path_depth",
    "glob_match",
    "listfile",
    "copy",
    "run",
    "execute",
]


def extension(filename: str) -> str:
    """
    Extracts the filename extension from the given filename or path.

    :param filename: The specific filename or path.
    :return: The filename extension, including the leading dot (e.g., ".txt").
    """
    _, result = os.path.splitext(os.path.basename(filename))
    return result


def stem(filename: str, minimal: bool = False) -> str:
    """
    Extracts the filename stem from the given filename or path.

    :param filename: The specific filename or path.
    :param minimal: If ``True``, extracts the minimal (shortest) stem, otherwise the default stem.
    :return: The filename stem.
    """
    base = os.path.basename(filename)
    if not minimal:
        result, _ = os.path.splitext(base)
        return result
    else:
        maximal_extension = last_or_none(extensions(base))
        if is_empty(maximal_extension):
            return base
        else:
            return base[:-len(maximal_extension)]


def extensions(filename: str) -> list[str]:
    """
    Extracts all filename extensions and compound extensions from the given filename or path.

    :param filename: The specific filename or path.
    :return: List of all extensions, ordered from shortest to longest, each including the leading dot.
    """
    base = os.path.basename(filename)
    results = [""]
    while True:
        fn, ext = os.path.splitext(base)
        base = fn
        if is_empty(ext):
            break
        results.append(ext + last(results))
    return list(tail_iter(results))


def expanded_path(path: str) -> str:
    """
    Returns the absolute expanded path, expanding environment variables and the home tilde.

    :param path: The given path.
    :return: The absolute canonical path.
    """
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def path_depth(root: str, child: str) -> int:
    """
    Returns the relative path depth from the given ``child`` to the ``root``.

    :param root: The root path.
    :param child: The child path.
    :return: Relative depth, or -1 if ``child`` is not under ``root``.
    """
    root_expanded = expanded_path(root)
    child_expanded = expanded_path(child)
    if not child_expanded.startswith(root_expanded):
        return -1
    return child_expanded[len(root_expanded):].count(os.sep)


def glob_match(
    names: list[str],
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> list[str]:
    """
    Applies the given inclusive and exclusive glob patterns to the given ``names`` and returns the filtered result.

    :param names: Names to apply the glob patterns to.
    :param include_patterns: Inclusive glob patterns.
    :param exclude_patterns: Exclusive glob patterns.
    :return: Filtered names matching the patterns.
    """
    ret = set()
    for pat in (include_patterns or []):
        ret.update(fnmatch.filter(names, pat))
    if include_patterns is None or len(include_patterns) == 0:
        ret.update(names)
    for pat in (exclude_patterns or []):
        ret.difference_update(fnmatch.filter(names, pat))
    return list(ret)


class CopyFuncProtocol(Protocol):
    def __call__(self, src: str, dst: str, **kwargs) -> None: ...


def listfile(
    path: str,
    *,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    depth: int = 0,
) -> list[str]:
    """
    Recursively scans the given ``path`` and returns a list of files whose names satisfy the given name patterns and the
    relative depth of their folders to the given root path is not greater than the specified ``depth`` value.

    :param path: The root path to scan.
    :param include_patterns: Inclusive glob patterns applied to the filenames.
    :param exclude_patterns: Exclusive glob patterns applied to the filenames.
    :param depth: Maximum depth of the subdirectories included in the scan.
    :return: List of file paths matching the criteria.
    """
    if os.path.exists(path) and not os.path.isdir(path):
        if len(glob_match([os.path.basename(path)], include_patterns, exclude_patterns)) == 0:
            return []
        return [path]

    ret = []
    for parent, dirs, filenames in os.walk(path):
        if 0 < depth <= path_depth(path, parent):
            continue
        for filename in glob_match(filenames, include_patterns, exclude_patterns):
            ret.append(os.path.join(parent, filename))
    return ret


def copy(
    src: str,
    dst: str,
    *,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    depth: int = 0,
    follow_symlinks: bool = False,
    ignore_dangling_symlinks: bool = False,
    dirs_exist_ok: bool = False,
    copy_func: CopyFuncProtocol = shutil.copy2
):
    """
    Recursively copies the given source path to the destination path. Only copies the files whose names satisfy the
    given name patterns and the relative depth of their folders to the given source path is not greater than the
    specified ``depth`` value.

    :param src: The source path or file.
    :param dst: The destination path or file.
    :param include_patterns: Inclusive glob patterns applied to the filenames.
    :param exclude_patterns: Exclusive glob patterns applied to the filenames.
    :param depth: Maximum depth of the subdirectories included in the scan.
    :param follow_symlinks: If ``True``, create symbolic links for the symbolic links present in the source; otherwise, make a physical copy.
    :param ignore_dangling_symlinks: If ``True``, ignore errors if the file pointed by the symbolic link does not exist.
    :param dirs_exist_ok: If ``True``, ignore errors if the destination directory and subdirectories exist.
    :param copy_func: Copy function to use for copying files.
    """
    if not os.path.isdir(src):
        if len(glob_match([os.path.basename(src)], include_patterns, exclude_patterns)) == 0:
            return
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
        copy_func(src, dst, follow_symlinks=follow_symlinks)
        return

    def ignore_func(parent, names):
        filenames = list(filter(lambda x: not os.path.isdir(os.path.join(parent, x)), names))
        ret = set(filenames)
        if 0 < depth <= path_depth(src, parent):
            return ret
        ret.difference_update(glob_match(filenames, include_patterns, exclude_patterns))
        return ret

    shutil.copytree(src,
                    dst,
                    symlinks=follow_symlinks,
                    ignore=ignore_func,
                    ignore_dangling_symlinks=ignore_dangling_symlinks,
                    dirs_exist_ok=dirs_exist_ok,
                    copy_function=copy_func)


def run(cmd: str) -> bool:
    """
    Runs the given command and returns the success status.

    :param cmd: Command to run.
    :return: ``True`` if the command has been successfully run, ``False`` otherwise.
    """
    logger.debug("Running command: %s", cmd)
    return os.system(cmd) == 0


def execute(cmd: str, strip: bool = True) -> str:
    """
    Executes the given command and returns contents collected from standard output.

    :param cmd: Command to execute.
    :param strip: If ``True``, the contents will be stripped.
    :return: The content from standard output.
    """
    logger.debug("Executing command: %s", cmd)
    if strip:
        return os.popen(cmd).read().strip()
    return os.popen(cmd).read()
