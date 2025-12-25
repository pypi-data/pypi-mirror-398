import hashlib
import os
import pathlib
import shutil

IMG_TYPE = ["jpg", "jpeg", "png"]


def files(f_path: str, f_ext: list[str]) -> list[str]:
    f_ext = [ext.lower() for ext in f_ext]
    if not os.path.exists(f_path):
        return []
    exts = ["." + ext for ext in f_ext]
    files: list[str] = []
    for f in os.listdir(f_path):
        ext = "".join(pathlib.Path(f).suffixes)
        if ext in exts:
            files.append(f)
    return files


def file_paths(f_path: str, f_ext: list[str]) -> list[str]:
    if not os.path.exists(f_path):
        return []
    return [os.path.join(f_path, f) for f in files(f_path, f_ext)]


def imgs(f_path: str, f_ext: list[str] = IMG_TYPE) -> list[str]:
    if not os.path.exists(f_path):
        return []
    return files(f_path, f_ext)


def img_paths(f_path: str, f_ext: list[str] = IMG_TYPE) -> list[str]:
    return file_paths(f_path, f_ext)


def file_hash(file_path: str, hash_type: str) -> str:
    if not os.path.isfile(file_path) or not os.path.exists(file_path):
        return "Invalid File"
    hash_code = "No Hash Code"
    hash_type = hash_type.upper()
    with open(file_path, "rb") as f:
        match hash_type:
            case "SHA256":
                sha256_obj = hashlib.sha256()
                sha256_obj.update(f.read())
                hash_code = sha256_obj.hexdigest()
            case "MD5":
                md5_obj = hashlib.md5()
                md5_obj.update(f.read())
                hash_code = md5_obj.hexdigest()
            case _:
                hash_code = "Invalid Hash Type"
    return hash_code
