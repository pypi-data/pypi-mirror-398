from pathlib import Path
import json
import getpass
from threading import Lock
from typing import Union

__all__ = ["APIKeyManager"]


class APIKeyManager:
    def __init__(self, api_key_file: Union[str, Path] = "./api_keys.json") -> None:
        self._api_key_file = Path(api_key_file)
        self._lock = Lock()

    def get_key(self, name: str) -> str:
        """获取API Key

        Args:
            name (str): API Key的名称

        Returns:
            str: API Key的值
        """
        api_keys: dict[str, str] = {}
        if self._api_key_file.exists():
            with self._lock:
                with open(self._api_key_file, "r") as f:
                    api_keys = json.load(f)
        if name in api_keys:
            return api_keys[name]
        else:
            value = getpass.getpass(f"请输入{name}的API Key:")
            api_keys[name] = value
            with self._lock:
                with open(self._api_key_file, "w") as f:
                    json.dump(api_keys, f, indent=4)
            return value
