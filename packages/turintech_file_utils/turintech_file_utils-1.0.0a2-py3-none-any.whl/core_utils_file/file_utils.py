# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import filecmp
import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Generator, Iterator, List, Optional, Type, Union

from pydantic import TypeAdapter

# Core Source imports
from core_common_data_types.type_definitions import DataModelT, DataModelType, JsonT, JsonType, PathType
from core_utils_file.data_utils import serialize_data

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "read_file_version",
    "read_json",
    "read_data_model",
    "write_json",
    "get_paths_recursively",
    "get_relative_paths_gen",
    "get_files_recursively",
    "get_files_recursively_and_filter",
    "remove_file_if_exists",
    "copy_merge_files",
    "copy_merge",
    "remove_dir_if_exists",
    "cmp_dir",
    "unzip_file",
    "zip_dir",
    "zip_path",
    "get_file_name",
    "get_file_path",
    "copy_file",
]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                 Version File utils                                                   #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def read_file_version(file_path: Path) -> str:
    """
    Return the content of the file.
    """
    return file_path.read_text().strip() if file_path.is_file() else ""


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                   JSON File utils                                                    #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def read_json(file_path: PathType, encoding: Optional[str] = None, return_type: Optional[Type[JsonT]] = None) -> JsonT:
    """
    Return a JSON file data.
    """
    with Path(file_path).open("r", encoding=encoding) as file:
        data = json.load(file)
        assert return_type is None or isinstance(data, return_type)
        return data


def read_data_model(file_path: PathType, type_: Type[DataModelT], encoding: Optional[str] = None) -> DataModelT:
    """
    Return a JSON file data as `type_` format.
    """
    with Path(file_path).open("r", encoding=encoding) as file:
        return TypeAdapter(type_).validate_python(json.load(file))


def write_json(
    file_path: PathType,
    data: Union[JsonType, DataModelType],
    exclude_none: bool = False,
    by_alias: bool = True,
    by_name: bool = False,
    encoding: Optional[str] = None,
):
    """
    Export the dictionary or the data model to a JSON file.
    """
    _file_path = Path(file_path)
    _file_path.parent.mkdir(parents=True, exist_ok=True)
    with _file_path.open("w", encoding=encoding) as file:
        json.dump(
            serialize_data(data=data, by_name=by_name, exclude_none=exclude_none, by_alias=by_alias),
            file,
            indent=4,
        )


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                               Generic files utilities                                                #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def get_paths_recursively(root_path: Path, as_relative: bool = False) -> Generator[Path, None, None]:
    """Obtains the list of directories and files available in the root directory recursively.

    If as_relative is True, returns the list of paths relative to a root path.

    """
    paths = root_path.rglob("*")
    yield from get_relative_paths_gen(paths=paths, root_path=root_path) if as_relative else paths


def get_relative_paths_gen(paths: Union[List[Path], Iterator[Path]], root_path: Path) -> Generator[Path, None, None]:
    """
    Get the list of absolute paths as a list of paths relative to a root path.
    """
    yield from (path.relative_to(root_path) for path in paths)


def get_files_recursively(root_path: Path, as_relative: bool = False) -> List[Path]:
    """Obtains the list of files available in the directory recursively.

    If as_relative is True, returns the list of paths relative to a root path.

    """
    paths = [Path(os.path.join(path, name)) for path, _, files in os.walk(root_path) for name in files]
    return list(get_relative_paths_gen(paths=paths, root_path=root_path)) if as_relative else paths


def get_files_recursively_and_filter(root_path: Path, exclude: List[Path]) -> Generator[Path, None, None]:
    """
    Obtains the list of files available in the directory recursively, ignoring those files and subdirectories indicated
    in the exclusion list.
    """
    for file in root_path.iterdir():
        if file not in exclude:
            if file.is_dir():
                yield from get_files_recursively_and_filter(root_path=file, exclude=exclude)
            else:
                yield file


def copy_merge_files(src: Path, dst: Path, paths: Union[List[Path], Iterator[Path]], overwrite: bool = False):
    """Copy the list of files indicated in the desired output directory, keeping the same directory structure.

    ARgs:
        src (Path): Root directory in which all the files to be copied are located.
        dst (Path): Destination root directory.
        paths (Union[List[Path], Iterator[Path]]): List of files to be copied to
            the destination.
        overwrite (bool, default:False): If the file to be copied exists, and this
            flag takes the value:
                - False: the existing file is kept.
                - True: the existing file is overwritten.

    """
    for relative_path in get_relative_paths_gen(paths=paths, root_path=src):
        src_file = src.joinpath(*relative_path.parts)
        dst_file = dst.joinpath(*relative_path.parts)
        if not dst_file.exists() or overwrite:
            # The file is copied if it doesn't exist or if it exists, so you want to overwrite it
            if src_file.is_file():
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src_file, dst_file)
            else:
                copy_merge(src=src_file, dst=dst_file)


def remove_file_if_exists(file_path: PathType):
    """
    Remove the given path file if it exists.
    """
    if Path(file_path).is_file():
        os.remove(str(file_path))


def copy_file(src_path: PathType, dst_path: PathType) -> None:
    """Copy a file and its metadata.

    Args:
        src_path (str|Path): Source file path
        dst_path (str|Path): Destination file path

    """
    if not Path(src_path).is_file():
        raise FileNotFoundError(f"File not available: {src_path}")
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst_path)  # Copies metadata


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                 Directory utilities                                                  #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def copy_merge(src: Path, dst: Path, exclude: Optional[List[Path]] = None, overwrite: bool = False):
    """Takes all the content of `src`, and recursively copies it to `dst`

    Args:
        src (Path): Source directory
        dst (Path): Destination directory
        exclude (List[Path]): List of absolute paths to the directories and / or
            files that you do not want to include in the new directory
        overwrite (bool, default: False): If the file to be copied exists,
            and this flag takes the value:
                - False: the existing file is kept.
                - True: the existing file is overwritten.

    """
    if exclude:
        dst.mkdir(parents=True, exist_ok=True)
        paths = get_files_recursively_and_filter(root_path=src, exclude=exclude)
        copy_merge_files(src=src, dst=dst, paths=paths, overwrite=overwrite)
    elif not dst.exists():
        shutil.copytree(src=src, dst=dst)
    else:
        copy_merge_files(src=src, dst=dst, paths=get_files_recursively(root_path=src), overwrite=overwrite)


def remove_dir_if_exists(paths: List[Path]):
    """Remove all given path directories if they exist.

    Args:
        paths (List[Path]): List with the directories paths to remove.

    """
    for path in paths:
        if path.exists():
            shutil.rmtree(path)


def cmp_dir(dir1: Path, dir2: Path) -> bool:
    """Compare two directory trees content.

    Returns:
        cmp (bool): False if they differ, True if they are the same.

    """

    def _cmp_dir(dir_cmp: filecmp.dircmp):
        if dir_cmp.diff_files or dir_cmp.left_only or dir_cmp.right_only:
            return False
        for sub_dir_cmp in dir_cmp.subdirs.values():
            if not _cmp_dir(sub_dir_cmp):
                return False
        return True

    return _cmp_dir(filecmp.dircmp(dir1, dir2))


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                   .zip File utils                                                    #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def unzip_file(file_path: PathType, output_path: PathType, remove_zip: bool = False):
    """
    Unzip a given file to a given output path.
    """
    Path(output_path).mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(file_path), "r") as zip_f:
        zip_f.extractall(str(output_path))
    if remove_zip:
        os.remove(str(file_path))


def zip_dir(dir_path: Path, zip_file_path: Path):
    """
    Zips a directory and preserves the exact layout and naming of files.
    """
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zip_handle:
        for root, _, files in os.walk(str(dir_path)):
            for file_name in files:
                zip_handle.write(Path(root) / file_name, Path(root).relative_to(dir_path) / file_name)


def zip_path(path: Path, archive_format: str = "zip") -> Path:
    """Create an archive file (eg.

    zip or tar)

    """
    return Path(shutil.make_archive(str(path), archive_format, str(path)))


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                  File naming utils                                                   #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def get_file_name(base_name: str, suffix: Optional[str] = None, idx: Optional[int] = 1, extension: str = "json") -> str:
    """Composes a file name.

    Args:
        base_name: Identifying name of the file content (e.g. service_get, service_post, etc)
        suffix: Suffix to add to the file name. (e.g. BaseModel, response, expected, etc)
        idx: Index of the file in case several are generated with the same identifying name. (e.g. 1 => 001)
        extension: File extension (e.g. json, csv, txt, etc)

    Returns:
        file_name: The file name composed as: {base_name}_{idx}_{suffix}.{extension}

    """
    _idx = f"{idx:03d}" if idx else None
    name = "_".join([value for value in [base_name, _idx, suffix] if value])
    return f"{name}.{extension}"


def get_file_path(
    directory: Path, base_name: str, suffix: Optional[str] = None, idx: Optional[int] = None, extension: str = "json"
) -> Path:
    """Composes a file path.

    Args:
        directory: Root path where to find the file.
        base_name: Identifying name of the file content (e.g. service_get, service_post, etc)
        suffix: Suffix to add to the file name. (e.g. BaseModel, response, expected, etc)
        idx: Index of the file in case several are generated with the same identifying name. (e.g. 1 => 001)
        extension: File extension (e.g. json, csv, txt, etc)

    Returns:
        file_path: The file path composed as: {directory}/{base_name}_{idx}_{suffix}.{extension}

    """
    return directory / get_file_name(base_name=base_name, suffix=suffix, idx=idx, extension=extension)
