import sys
from pathlib import Path

try:
    from ..mac.hmac import HMAC
except ImportError:
    _current_dir = Path(__file__).resolve().parent
    _project_root = _current_dir.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    from mac.hmac import HMAC


def hmac_sha256(key: bytes, message: bytes) -> bytes:
    """
    Вычисление HMAC-SHA256 для сообщения с использованием ключа.

    Args:
        key (bytes): Ключ для HMAC.
        message (bytes): Сообщение для хэширования.

    Returns:
        bytes: HMAC-SHA256 хэш.
    """
    mac = HMAC(key)
    mac.update(message)
    return mac.digest()


def pbkdf2_hmac_sha256(password, salt, iterations: int, dklen: int) -> bytes:
    """
    Реализация PBKDF2 с использованием HMAC-SHA256.

    Args:
        password: Пароль для деривации ключа.
        salt: Соль для деривации ключа.
        iterations (int): Количество итераций.
        dklen (int): Длина производного ключа.

    Returns:
        bytes: Производный ключ.

    Raises:
        ValueError: Если итераций меньше 1 или длина ключа меньше 1.
    """
    if iterations < 1:
        raise ValueError("Iterations must be at least 1")
    if dklen < 1:
        raise ValueError("Derived key length must be at least 1")

    if isinstance(password, str):
        password = password.encode('utf-8')

    if isinstance(salt, str):

        try:
            if all(c in '0123456789abcdefABCDEF' for c in salt) and len(salt) % 2 == 0:
                salt = bytes.fromhex(salt)
            else:
                salt = salt.encode('utf-8')
        except ValueError:
            salt = salt.encode('utf-8')

    hlen = 32

    blocks_needed = (dklen + hlen - 1) // hlen

    if dklen > (2 ** 32 - 1) * hlen:
        raise ValueError("Derived key too long")

    derived_key = b''

    for block_num in range(1, blocks_needed + 1):
        block = _pbkdf2_f(password, salt, iterations, block_num)
        derived_key += block

    return derived_key[:dklen]


def _pbkdf2_f(password: bytes, salt: bytes, iterations: int, block_num: int) -> bytes:
    """
    Функция F для PBKDF2 (обработка одного блока).

    Args:
        password (bytes): Пароль для деривации ключа.
        salt (bytes): Соль для деривации ключа.
        iterations (int): Количество итераций.
        block_num (int): Номер блока.

    Returns:
        bytes: Блок производного ключа.
    """
    u_prev = hmac_sha256(password, salt + block_num.to_bytes(4, 'big'))

    result = bytearray(u_prev)

    for _ in range(2, iterations + 1):
        u_curr = hmac_sha256(password, u_prev)

        for i in range(len(result)):
            result[i] ^= u_curr[i]

        u_prev = u_curr

    return bytes(result)


class PBKDF2:
    """
    Реализация PBKDF2 (Password-Based Key Derivation Function 2).

    Атрибуты:
        DEFAULT_ITERATIONS (int): Количество итераций по умолчанию.
        DEFAULT_KEY_LENGTH (int): Длина ключа по умолчанию.
        HASH_OUTPUT_SIZE (int): Размер выхода хэш-функции.
    """

    DEFAULT_ITERATIONS = 100000
    DEFAULT_KEY_LENGTH = 32
    HASH_OUTPUT_SIZE = 32

    def __init__(self, password, salt: bytes = None, iterations: int = None):
        """
        Инициализация PBKDF2.

        Args:
            password: Пароль для деривации ключа.
            salt (bytes): Соль для деривации ключа.
            iterations (int): Количество итераций.
        """
        if isinstance(password, str):
            self.password = password.encode('utf-8')
        else:
            self.password = bytes(password)

        if salt is None:
            from ..csprng import generate_random_bytes
            self.salt = generate_random_bytes(16)
        else:
            self.salt = bytes(salt)

        self.iterations = iterations or self.DEFAULT_ITERATIONS

    def derive(self, length: int = None) -> bytes:
        """
        Деривация ключа из пароля.

        Args:
            length (int): Длина производного ключа.

        Returns:
            bytes: Производный ключ.
        """
        length = length or self.DEFAULT_KEY_LENGTH
        return pbkdf2_hmac_sha256(
            self.password,
            self.salt,
            self.iterations,
            length
        )

    def derive_hex(self, length: int = None) -> str:
        """
        Деривация ключа с возвратом в шестнадцатеричном формате.

        Args:
            length (int): Длина производного ключа.

        Returns:
            str: Производный ключ в шестнадцатеричном формате.
        """
        return self.derive(length).hex()