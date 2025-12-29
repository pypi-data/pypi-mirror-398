import os


def generate_random_bytes(num_bytes: int) -> bytes:
    """Генерирует криптографически стойкую случайную байтовую строку."""
    try:
        return os.urandom(num_bytes)
    except Exception as e:
        raise Exception(f"[ERROR] Ошибка генерации случайных байтов: {str(e)}")

