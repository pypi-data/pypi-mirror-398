import sys
from pathlib import Path


def read_file(file_path: Path) -> bytes:
    """Чтение данных из файла в бинарном режиме"""
    try:
        with open(file_path, "rb") as file:
            return file.read()

    except IOError as error:
        raise IOError(f"Ошибка записи файла {file_path}: {error}")


def write_file(file_path: Path, data: bytes) -> None:
    """Запись данных в файл в бинарном режиме"""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as file:
            file.write(data)

    except IOError as error:
        raise IOError(f"Ошибка чтения файла {file_path}: {error}")


def print_error(message: str, details: str = None):
    """Единообразный вывод ошибок"""
    print(f"[ERROR] {message}", file=sys.stderr)
    if details:
        print(f"[DETAILS] {details}", file=sys.stderr)
    print()


def print_warning(message: str):
    """Единообразный вывод предупреждений"""
    print(f"[WARNING] {message}")


def print_info(message: str):
    """Вывод информационного сообщения"""
    print(f"[INFO] {message}")


def print_success(operation: str, input_path: Path, output_path: Path, mode: str):
    """Вывод успешной операции"""
    print(f"[INFO] Файл успешно {operation} в режиме {mode.upper()}")
    print(f"[INFO] Входной файл: {input_path} -> Выходной файл: {output_path}")
