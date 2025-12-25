import os
import shutil
from pathlib import Path
from typing import Callable, List, Union


def get_conflicts(
    *,
    src: Union[Path, str],
    dst: Union[Path, str],
    preserve_templates: bool,
    dst_path_transformer: Callable[[str], str] = lambda x: x,
) -> List[Path]:
    dst = Path(dst)
    if not dst.exists():
        return []
    if not dst.is_dir():
        return [dst]
    conflicts = []
    for entry_path in Path(src).rglob("*"):
        if entry_path.is_dir():
            local_folder_path = os.path.relpath(entry_path, src)
            path = Path(os.path.join(dst, dst_path_transformer(local_folder_path)))
            if path.exists() and not path.is_dir():
                conflicts.append(path)
        else:
            local_file_path = os.path.relpath(entry_path, src)
            path = Path(os.path.join(dst, dst_path_transformer(local_file_path)))
            if entry_path.suffix == ".template":
                if preserve_templates and path.exists():
                    conflicts.append(path)
                path = path.with_name(path.stem)
            if path.exists():
                conflicts.append(path)
    return conflicts


def delete(*files: Union[Path, str]):
    for file in files:
        path = Path(file)
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
