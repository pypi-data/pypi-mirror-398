import os
import json
from typing import Dict, Any, Union, Literal
from ..handler.client import *
from ..utils.log import *

# Supported data types
FileData = Union[Dict[str, Any], bytes, str]
# write mode
WriteMode = Literal["w", "a"]  # write mode: w=overwrite, a=append


def load_json(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(file_path: str, data: Dict[str, Any]):
    with open(file_path, 'w') as f:
        json.dump(data, f)


def _write_file(file_path: str, data: FileData, mode: WriteMode = "w") -> None:
    """
    automatically choose write mode based on data type
    
    :param file_path: file path
    :param data: data (bytes/str/dict)
    :param mode: write mode: w=overwrite, a=append
    """
    if isinstance(data, bytes):
        # binary data (image, audio, etc.)
        binary_mode = f"{mode}b"  # binary mode: wb or ab
        with open(file_path, binary_mode) as f:
            f.write(data)
    elif isinstance(data, str):
        # text data
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(data)
    elif isinstance(data, dict):
        # JSON data
        if mode == "a":
            # append mode: write JSON (JSONL format)
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        else:
            # overwrite mode
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")


def save(file_path: str, data: FileData, mode: WriteMode = "w") -> Optional[Exception]:
    """
    save file to JFS and sync
    
    :param file_path: file path
    :param data: data (bytes/str/dict)
    :param mode: write mode: w=overwrite, a=append
    """
    try:
        _write_file(file_path, data, mode)
        return None
    except Exception as e:
        return e


async def async_save_jfs(file_path: str, data: FileData, mode: WriteMode = "w") -> Optional[Exception]:
    """
    async save file to JFS and sync
    
    :param file_path: file path
    :param data: data (bytes/str/dict)
    :param mode: write mode: w=overwrite, a=append
    """
    try:
        _write_file(file_path, data, mode)
        return await async_send(Payload(path="jfs_sync", payload={"file_path": file_path}))
    except Exception as e:
        return e


def save_jfs(file_path: str, data: FileData, mode: WriteMode = "w") -> Optional[Exception]:
    """
    save file to JFS and sync
    
    :param file_path: file path
    :param data: data (bytes/str/dict)
    :param mode: write mode: w=overwrite, a=append
    """
    try:
        _write_file(file_path, data, mode)
        return send(Payload(path="jfs_sync", payload={"file_path": file_path}))
    except Exception as e:
        return e