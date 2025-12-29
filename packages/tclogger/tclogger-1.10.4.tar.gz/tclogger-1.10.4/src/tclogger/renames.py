import os
import re

from pathlib import Path
from typing import Literal

from .logs import logstr
from .decorations import brp
from .matches import logger, iterate_folder
from .types import PathType, StrsType
from .paths import norm_path
from .confirms import confirm_input


def content_match(content: str, pattern: str):
    if not content or not pattern:
        return None
    return re.search(pattern, content)


def pathname_match(path: PathType, pattern: str):
    if not path or not pattern:
        return None
    return re.search(pattern, str(path))


def basename_match(path: PathType, pattern: str):
    if not path or not pattern:
        return None
    return re.search(pattern, Path(path).name)


def sort_paths_by_depth(paths: list[PathType]) -> list[PathType]:
    """Sort paths by their depth in the file system."""
    if not paths:
        return []
    return sorted(paths, key=lambda x: len(str(x).split("/")), reverse=True)


def read_file_content(path: PathType) -> str:
    """Read the content of a file."""
    if not path:
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def log_rename(
    old: PathType,
    new: PathType,
    text_type: Literal["file", "folder", "content"],
    indent: int = 2,
):
    """Log the renaming of a file or folder."""
    with logger.temp_indent(indent):
        logger.note(f"> Renaming {text_type}:")
        logger.warn(f"  * from: {old}")
        logger.okay(f"  * to  : {new}")


def log_paths_to_rename(paths_to_rename: dict[str, list[PathType]]):
    """Log the paths that will be renamed."""
    logger.note(f"> Following paths will be renamed:")
    for text_type, paths in paths_to_rename.items():
        if not paths:
            continue
        logger.mesg(f"  * {text_type}:")
        for p in paths:
            logger.hint(f"    * {p}")


def log_match(p: PathType, text_type: Literal["content", "file", "folder"]):
    """Log the matching of a file or folder."""
    logger.hint(f"! {p} {logstr.mesg(brp(text_type))}")


def rename_texts(
    root: PathType,
    renames_dict: dict,
    includes: StrsType = None,
    excludes: StrsType = None,
    unmatch_bool: bool = True,
    use_gitignore: bool = True,
    is_rename_content: bool = True,
    is_rename_file: bool = True,
    is_rename_folder: bool = True,
    confirm_before_rename: bool = True,
    verbose: bool = True,
) -> dict[str, list[tuple[PathType, PathType]]]:
    """
    Params:
        - root: root directory to search for files and folders to rename
        - renames_dict: dict of patterns and replacements
            - keys: patterns to match
            - vals: new values to replace the matched patterns with
        - includes: list of patterns to include files/folders
        - excludes: list of patterns to exclude files/folders
        - is_rename_content: whether to rename file contents
        - is_rename_file: whether to rename file names
        - is_rename_folder: whether to rename folder names

    Rename order: content -> file -> folder
        - contents: file paths whose file content hits pattern
        - files: file paths whose basename hit pattern
        - folders: folder paths whose pathname hit pattern
    """
    root = norm_path(root)
    logger.note(f"> Renaming directory:", end=" ")
    logger.file(f"[{root}]")

    paths_to_rename = {"contents": [], "folders": [], "files": []}
    paths_renamed = {"contents": [], "folders": [], "files": []}

    for p, match_bool, level in iterate_folder(
        root,
        includes=includes,
        excludes=excludes,
        yield_folder=True,
        unmatch_bool=unmatch_bool,
        use_gitignore=use_gitignore,
        verbose=verbose,
    ):
        if not match_bool:
            continue

        # as renaming contents would not break file structure, we could do it directly
        # but to be consistent with file and folder renames, we would do it later
        if is_rename_content and p.is_file():
            content = read_file_content(p)
            for pattern, new_val in renames_dict.items():
                if content_match(content, pattern):
                    paths_to_rename["contents"].append(p)
                    log_match(p, "content")
                    break

        # as renaming files would break file structure, we would do it later
        if is_rename_file and p.is_file():
            for pattern, new_val in renames_dict.items():
                if basename_match(p, pattern):
                    paths_to_rename["files"].append(p)
                    log_match(p, "file")
                    break

        # as renaming folders would break file structure, we would do it later
        if is_rename_folder and p.is_dir():
            for pattern, new_val in renames_dict.items():
                if basename_match(p, pattern):
                    paths_to_rename["folders"].append(p)
                    log_match(p, "folder")
                    break

    if confirm_before_rename:
        log_paths_to_rename(paths_to_rename)
        if not confirm_input("rename", op_name="rename texts"):
            logger.warn("× rename_texts cancelled by user")
            return

    # rename file contents
    if is_rename_content and paths_to_rename["contents"]:
        for p in paths_to_rename["contents"]:
            new_content = read_file_content(p)
            for pattern, new_val in renames_dict.items():
                new_content = re.sub(pattern, new_val, new_content)
            log_rename(p, p, "content")
            with open(p, "w", encoding="utf-8") as wf:
                wf.write(new_content)
            paths_renamed["contents"].append((p, p))

    # rename file basenames
    if is_rename_file and paths_to_rename["files"]:
        for p in paths_to_rename["files"]:
            new_basename = Path(p).name
            for pattern, new_val in renames_dict.items():
                new_basename = re.sub(pattern, new_val, new_basename)
            new_path = Path(p).parent / new_basename
            log_rename(p, new_path, "file")
            os.rename(p, new_path)
            paths_renamed["files"].append((p, new_path))

    # rename folder basenames
    if is_rename_folder and paths_to_rename["folders"]:
        # sort folders to rename from the deepest to the shallowest
        paths_to_rename["folders"] = sort_paths_by_depth(paths_to_rename["folders"])
        for p in paths_to_rename["folders"]:
            new_basename = Path(p).name
            for pattern, new_val in renames_dict.items():
                new_basename = re.sub(pattern, new_val, new_basename)
            new_path = Path(p).parent / new_basename
            log_rename(p, new_path, "folder")
            os.rename(p, new_path)
            paths_renamed["folders"].append((p, new_path))

    return paths_renamed
