import os
import shutil
from pathlib import Path
from typing import Callable, Union


def copy(
    *,
    src: Union[Path, str],
    dst: Union[Path, str],
    dst_path_transformer: Callable[[str], str] = lambda x: x,
):
    """
    :param src:
    :param dst:
    :param dst_path_transformer:
    :return:
    """

    src_path = Path(src)
    dst_path = Path(dst)
    if src_path.is_dir():
        for src_full_path in Path(src).rglob("*"):
            if not src_full_path.is_dir():
                relative_path = os.path.relpath(src_full_path, src_path)
                dst_full_path = Path(
                    os.path.join(dst_path, dst_path_transformer(relative_path))
                )
                os.makedirs(dst_full_path.parent, exist_ok=True)
                shutil.copy(src_full_path, dst_full_path)
    else:
        os.makedirs(dst_path.parent, exist_ok=True)
        shutil.copy(src_path, dst_path)
