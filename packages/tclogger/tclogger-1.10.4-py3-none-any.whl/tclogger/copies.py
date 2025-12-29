from .matches import match_paths
from .types import PathType, PathsType
from .paths import norm_path
from .logs import TCLogger
from .confirms import confirm_input

from shutil import copyfile, rmtree
from pathlib import Path

logger = TCLogger(__name__)


def copy_file(src: PathType, dst: PathType):
    src = Path(src)
    dst = Path(dst)
    if not dst.parent.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
    copyfile(src, dst)


def copy_file_relative(src: PathType, src_root: PathType, dst_root: PathType):
    src = Path(src)
    src_root = Path(src_root)
    dst_root = Path(dst_root)
    dst = dst_root / src.relative_to(src_root)
    copy_file(src, dst)


def copy_folder(
    src_root: PathType,
    dst_root: PathType,
    includes: PathsType = None,
    excludes: PathsType = None,
    use_gitignore: bool = True,
    confirm_before_copy: bool = True,
    remove_existing: bool = True,
    confirm_before_remove: bool = True,
):
    src_root = norm_path(src_root)
    dst_root = norm_path(dst_root)

    logger.note(f"> Copying folder:")
    logger.file(f"  * src: {src_root}")
    logger.file(f"  * dst: {dst_root}")

    if not src_root.exists():
        logger.warn(f"× src not found: {src_root}")
        return

    if confirm_before_copy:
        if not confirm_input("copy", op_name="copy folder"):
            logger.warn("× copy_folder cancelled by user")
            return

    if dst_root.exists():
        logger.warn(f"  × dst exists: {dst_root}")
        if not confirm_input("force", op_name="force copy to existing folder"):
            logger.warn("× copy_folder cancelled as dst exists")
            return
        if remove_existing:
            if confirm_before_remove:
                if not confirm_input(
                    "remove", op_name="remove existing dst folder before copy"
                ):
                    logger.warn("× remove_folder cancelled by user")
                    return
            logger.warn(f"  * remove existing folder: {dst_root}")
            rmtree(dst_root)

    src_files = match_paths(
        src_root,
        includes=includes,
        excludes=excludes,
        use_gitignore=use_gitignore,
    ).get("includes", [])

    for src_file in src_files:
        copy_file_relative(src=src_file, src_root=src_root, dst_root=dst_root)
