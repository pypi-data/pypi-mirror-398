import json
import base64
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from cryptography.fernet import Fernet

from .exceptions import TypeError_


_encryption_key = None


def set_encryption_key(key: bytes):
    global _encryption_key
    _encryption_key = key


def get_encryption_key() -> bytes:
    global _encryption_key
    if _encryption_key is None:
        raise TypeError_("Encryption key not set. Call set_encryption_key() first.")
    return _encryption_key


def convert_type(value: str, type_name: str, key: str, file: str = None, line: int = None) -> Any:
    
    try:
        if type_name == "str":
            return value
        
        elif type_name == "int":
            return int(value)
        
        elif type_name == "float":
            return float(value)
        
        elif type_name == "bool":
            lower = value.lower()
            if lower in ("true", "1", "yes", "on"):
                return True
            elif lower in ("false", "0", "no", "off", ""):
                return False
            else:
                raise ValueError(f"Cannot convert '{value}' to bool")
        
        elif type_name == "json":
            return json.loads(value)
        
        elif type_name == "list":
            if not value:
                return []
            return [item.strip() for item in value.split(",")]
        
        elif type_name == "path":
            return Path(value)
        
        elif type_name == "url":
            if not value or value.strip() == "":
                return ""
            
            result = urlparse(value)
            if not result.scheme or not result.netloc:
                raise ValueError(f"Invalid URL: {value}")
            return value
        
        elif type_name == "secret":
            if value.startswith("ENC(") and value.endswith(")"):
                encrypted_data = value[4:-1]
                return decrypt_secret(encrypted_data)
            return value
        
        else:
            raise TypeError_(f"Unknown type: {type_name}", file, line)
    
    except (ValueError, json.JSONDecodeError) as e:
        raise TypeError_(
            f"Cannot convert '{value}' to {type_name} for key '{key}': {e}",
            file,
            line
        )


def encrypt_secret(plaintext: str) -> str:
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(plaintext.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt_secret(encrypted_data: str) -> str:
    key = get_encryption_key()
    f = Fernet(key)
    encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
    decrypted = f.decrypt(encrypted_bytes)
    return decrypted.decode('utf-8')
