import struct

import numpy as np
from numba import jit, uint32, uint8


# Оптимизация работы с использованием jit компиляции
@jit(uint32(uint32, uint32), nopython=True, cache=True)
def _rotr(n, x):
    """
    Циклический сдвиг 32-битного числа вправо.

    Args:
        n (uint32): Количество бит для сдвига.
        x (uint32): Исходное 32-битное число.

    Returns:
        uint32: Результат циклического сдвига.
    """
    return (x >> n) | (x << (32 - n))


@jit(uint32(uint32, uint32), nopython=True, cache=True)
def _shr(n, x):
    """
    Логический сдвиг 32-битного числа вправо.

    Args:
        n (uint32): Количество бит для сдвига.
        x (uint32): Исходное 32-битное число.

    Returns:
        uint32: Результат логического сдвига.
    """
    return x >> n


@jit(uint32(uint32, uint32, uint32), nopython=True, cache=True)
def _ch(x, y, z):
    """
    Функция выбора (choice function) для SHA256.

    Args:
        x (uint32): Первый аргумент.
        y (uint32): Второй аргумент.
        z (uint32): Третий аргумент.

    Returns:
        uint32: Результат функции выбора.
    """
    return (x & y) ^ (~x & z)


@jit(uint32(uint32, uint32, uint32), nopython=True, cache=True)
def _maj(x, y, z):
    """
    Функция большинства (majority function) для SHA256.

    Args:
        x (uint32): Первый аргумент.
        y (uint32): Второй аргумент.
        z (uint32): Третий аргумент.

    Returns:
        uint32: Результат функции большинства.
    """
    return (x & y) ^ (x & z) ^ (y & z)


@jit(uint32(uint32), nopython=True, cache=True)
def _sigma0(x):
    """
    Сигма-функция 0 для SHA256 (для обработки).

    Args:
        x (uint32): Входное значение.

    Returns:
        uint32: Результат вычисления.
    """
    return _rotr(uint32(2), x) ^ _rotr(uint32(13), x) ^ _rotr(uint32(22), x)


@jit(uint32(uint32), nopython=True, cache=True)
def _sigma1(x):
    """
    Сигма-функция 1 для SHA256 (для обработки).

    Args:
        x (uint32): Входное значение.

    Returns:
        uint32: Результат вычисления.
    """
    return _rotr(uint32(6), x) ^ _rotr(uint32(11), x) ^ _rotr(uint32(25), x)


@jit(uint32(uint32), nopython=True, cache=True)
def _sigma0_schedule(x):
    """
    Сигма-функция 0 для SHA256 (для расписания сообщений).

    Args:
        x (uint32): Входное значение.

    Returns:
        uint32: Результат вычисления.
    """
    return _rotr(uint32(7), x) ^ _rotr(uint32(18), x) ^ _shr(uint32(3), x)


@jit(uint32(uint32), nopython=True, cache=True)
def _sigma1_schedule(x):
    """
    Сигма-функция 1 для SHA256 (для расписания сообщений).

    Args:
        x (uint32): Входное значение.

    Returns:
        uint32: Результат вычисления.
    """
    return _rotr(uint32(17), x) ^ _rotr(uint32(19), x) ^ _shr(uint32(10), x)


@jit(nopython=True, cache=True)
def _process_block_numba(block, h, K):
    """
    Обработка одного блока данных (64 байта) в SHA256.

    Args:
        block (ndarray): Блок данных для обработки.
        h (ndarray): Массив из 8 32-битных слов, представляющий текущее хэш-значение.
        K (ndarray): Массив констант SHA256.

    Returns:
        ndarray: Обновленное хэш-значение.
    """
    w = np.zeros(64, dtype=np.uint32)

    for i in range(16):
        w[i] = (block[i * 4] << 24) | (block[i * 4 + 1] << 16) | (block[i * 4 + 2] << 8) | block[i * 4 + 3]

    for i in range(16, 64):
        s0 = _sigma0_schedule(w[i - 15])
        s1 = _sigma1_schedule(w[i - 2])
        w[i] = w[i - 16] + s0 + w[i - 7] + s1

    a, b, c, d, e, f, g, h_val = h

    for i in range(64):
        S1 = _sigma1(e)
        ch = _ch(e, f, g)
        temp1 = h_val + S1 + ch + K[i] + w[i]
        S0 = _sigma0(a)
        maj = _maj(a, b, c)
        temp2 = S0 + maj

        h_val = g
        g = f
        f = e
        e = d + temp1
        d = c
        c = b
        b = a
        a = temp1 + temp2

    h[0] += a
    h[1] += b
    h[2] += c
    h[3] += d
    h[4] += e
    h[5] += f
    h[6] += g
    h[7] += h_val

    return h


class SHA256:
    """
    Реализация хэш-функции SHA256 по стандарту NIST FIPS 180-4.

    Атрибуты:
        _H0 (ndarray): Начальные значения хэша.
        _K (ndarray): Константы SHA256.
    """

    _H0 = np.array([
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    ], dtype=np.uint32)

    _K = np.array([
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ], dtype=np.uint32)

    def __init__(self):
        """Инициализация объекта SHA256."""
        self.reset()

    def reset(self):
        """
        Сброс состояния хэш-функции в начальное.

        Инициализирует хэш-значение, буфер, общую длину и флаг финализации.
        """
        self.h = self._H0.copy()
        self.buffer = bytearray()
        self.total_length = 0
        self.finalized = False

    def _rotr(self, n, x):
        """
        Обертка для функции циклического сдвига вправо.

        Args:
            n (int): Количество бит для сдвига.
            x (uint32): Исходное 32-битное число.

        Returns:
            uint32: Результат циклического сдвига.
        """
        return _rotr(np.uint32(n), x)

    def _shr(self, n, x):
        """
        Обертка для функции логического сдвига вправо.

        Args:
            n (int): Количество бит для сдвига.
            x (uint32): Исходное 32-битное число.

        Returns:
            uint32: Результат логического сдвига.
        """
        return _shr(np.uint32(n), x)

    def _ch(self, x, y, z):
        """
        Обертка для функции выбора.

        Args:
            x (uint32): Первый аргумент.
            y (uint32): Второй аргумент.
            z (uint32): Третий аргумент.

        Returns:
            uint32: Результат функции выбора.
        """
        return _ch(x, y, z)

    def _maj(self, x, y, z):
        """
        Обертка для функции большинства.

        Args:
            x (uint32): Первый аргумент.
            y (uint32): Второй аргумент.
            z (uint32): Третий аргумент.

        Returns:
            uint32: Результат функции большинства.
        """
        return _maj(x, y, z)

    def _sigma0(self, x):
        """
        Обертка для сигма-функции 0 (для обработки).

        Args:
            x (uint32): Входное значение.

        Returns:
            uint32: Результат вычисления.
        """
        return _sigma0(x)

    def _sigma1(self, x):
        """
        Обертка для сигма-функции 1 (для обработки).

        Args:
            x (uint32): Входное значение.

        Returns:
            uint32: Результат вычисления.
        """
        return _sigma1(x)

    def _sigma0_schedule(self, x):
        """
        Обертка для сигма-функции 0 (для расписания сообщений).

        Args:
            x (uint32): Входное значение.

        Returns:
            uint32: Результат вычисления.
        """
        return _sigma0_schedule(x)

    def _sigma1_schedule(self, x):
        """
        Обертка для сигма-функции 1 (для расписания сообщений).

        Args:
            x (uint32): Входное значение.

        Returns:
            uint32: Результат вычисления.
        """
        return _sigma1_schedule(x)

    def _process_block(self, block):
        """
        Обработка одного блока данных.

        Args:
            block (bytes): Блок данных размером 64 байта.
        """
        block_np = np.frombuffer(block[:64], dtype=np.uint8)
        self.h = _process_block_numba(block_np, self.h, self._K)

    def update(self, data):
        """
        Добавление данных для хэширования.

        Args:
            data (bytes): Данные для добавления.

        Raises:
            RuntimeError: Если хэш уже финализирован.
        """
        if self.finalized:
            raise RuntimeError("Hash already finalized")

        self.buffer.extend(data)
        self.total_length += len(data)

        while len(self.buffer) >= 64:
            self._process_block(bytes(self.buffer[:64]))
            del self.buffer[:64]

    def _pad_message(self):
        """
        Добавление padding к сообщению согласно стандарту SHA256.
        """
        bit_length = self.total_length * 8

        self.buffer.append(0x80)

        while (len(self.buffer) + 8) % 64 != 0:
            self.buffer.append(0x00)

        self.buffer.extend(struct.pack('>Q', bit_length))

    def digest(self):
        """
        Получение хэша в виде байтов.

        Returns:
            bytes: Хэш SHA256 в виде байтовой строки.
        """
        if not self.finalized:

            temp_buffer = self.buffer[:]
            temp_length = self.total_length

            self._pad_message()

            while len(self.buffer) >= 64:
                self._process_block(bytes(self.buffer[:64]))
                del self.buffer[:64]

            self.finalized = True

            self.buffer = temp_buffer
            self.total_length = temp_length

        result = bytearray()
        for val in self.h:
            result.extend(val.item().to_bytes(4, 'big'))
        return bytes(result)

    def hexdigest(self):
        """
        Получение хэша в виде шестнадцатеричной строки.

        Returns:
            str: Хэш SHA256 в виде шестнадцатеричной строки.
        """
        return self.digest().hex()


def sha256_file(filename, chunk_size=8192):  # 8192 * 16
    """
    Вычисление хэша SHA256 для файла.

    Args:
        filename (str): Путь к файлу для хэширования.
        chunk_size (int): Размер чанка для чтения файла.

    Returns:
        str: Хэш SHA256 в виде шестнадцатеричной строки.
    """
    sha = SHA256()

    with open(filename, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha.update(chunk)

    return sha.hexdigest()


def sha256_data(data):
    """
    Вычисление хэша SHA256 для данных.

    Args:
        data (bytes или str): Данные для хэширования.

    Returns:
        str: Хэш SHA256 в виде шестнадцатеричной строки.
    """
    sha = SHA256()

    if isinstance(data, str):
        data = data.encode('utf-8')

    sha.update(data)
    return sha.hexdigest()