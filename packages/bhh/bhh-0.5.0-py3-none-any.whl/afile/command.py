import os
import json

def open_file(path: str, mode: str = "r", encoding: str = "utf-8"):
    return open(path, mode, encoding=encoding)

def delete_file(path: str) -> None:
        if os.path.exists(path):
            os.remove(path)
        else:
            raise FileNotFoundError(f"File {path} not found.")

def rename_file(old_path: str, new_path: str) -> None:
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
    else:
        raise FileNotFoundError(f"File {old_path} not found.")

def write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def read_text(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} not found.")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def read_json(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} not found.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

