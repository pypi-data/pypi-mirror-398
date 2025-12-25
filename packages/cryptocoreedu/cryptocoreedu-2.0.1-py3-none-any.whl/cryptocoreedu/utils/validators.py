from pathlib import Path
import os
from ..exceptions import KeyValidationError, IVValidationError, FileValidationError


def validate_hex_key(key_str: str) -> bytes:
    """
    Валидирует hex-ключ и возвращает bytes.

    Args:
        key_str (str): Ключ в шестнадцатеричном формате.

    Returns:
        bytes: Ключ в байтовом формате.

    Raises:
        KeyValidationError: Если ключ некорректен.
    """
    try:
        key_str = key_str.strip().lower()

        if not key_str:
            raise KeyValidationError('Ключ не может быть пустым')

        if key_str.startswith('0x'):
            key_str = key_str[2:]

        if not all(c in '0123456789abcdef' for c in key_str):
            raise KeyValidationError("Ключ должен представлять собой шестнадцатеричную строку")

        if len(key_str) != 32:
            raise KeyValidationError(
                f"Ключ должен состоять из 32 шестнадцатеричных символов (16 байт), получено - {len(key_str)}")

        key_bytes = bytes.fromhex(key_str)
        return key_bytes

    except KeyValidationError:
        raise
    except ValueError as e:
        raise KeyValidationError(f"Неверный формат ключа: {e}")


def validate_hex_iv(iv_str: str) -> bytes:
    """
    Валидирует hex-IV и возвращает bytes.

    Args:
        iv_str (str): IV в шестнадцатеричном формате.

    Returns:
        bytes: IV в байтовом формате.

    Raises:
        IVValidationError: Если IV некорректен.
    """
    try:
        iv_str = iv_str.strip().lower()

        if not iv_str:
            raise IVValidationError('IV не может быть пустым')

        if iv_str.startswith('0x'):
            iv_str = iv_str[2:]

        if not all(c in '0123456789abcdef' for c in iv_str):
            raise IVValidationError("IV должен представлять собой шестнадцатеричную строку")

        if len(iv_str) != 32:
            raise IVValidationError(
                f"IV должен состоять из 32 шестнадцатеричных символов (16 байт), получено - {len(iv_str)}")

        iv_bytes = bytes.fromhex(iv_str)
        return iv_bytes

    except IVValidationError:
        raise
    except ValueError as e:
        raise IVValidationError(f"Неверный формат IV: {e}")


def validate_file_path(path: Path, for_reading: bool = True) -> Path:
    """
    Валидирует путь к файлу.

    Args:
        path (Path): Путь к файлу.
        for_reading (bool): Флаг для чтения (True) или записи (False).

    Returns:
        Path: Валидированный путь.

    Raises:
        FileValidationError: Если путь некорректен.
    """
    try:
        if for_reading:
            if not path.exists():
                raise FileValidationError(f"Входной файл {path} не существует")
            if not path.is_file():
                raise FileValidationError(f"Входной путь {path} не является файлом")
            if not os.access(path, os.R_OK):
                raise FileValidationError(f"Нет прав на чтение файла {path}")
        else:
            parent_dir = path.parent
            if parent_dir and not parent_dir.exists():
                raise FileValidationError(f"Выходная директория {parent_dir} не существует")
            if not os.access(parent_dir, os.W_OK):
                raise FileValidationError(f"Нет прав на запись в директорию {parent_dir}")
            if path.exists() and not os.access(path, os.W_OK):
                raise FileValidationError(f"Нет прав на запись в файл {path}")
        return path
    except FileValidationError:
        raise