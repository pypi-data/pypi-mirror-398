import numpy as np
from numba import jit, uint64, uint8, types

RHO_OFFSETS = np.array([
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14]
], dtype=np.uint64)

RC = np.array([
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008
], dtype=np.uint64)


@jit(uint64(uint64, uint64), nopython=True, cache=True)
def _rotl64(x, n):
    """
    Циклический сдвиг 64-битного числа влево.

    Args:
        x (uint64): Исходное 64-битное число.
        n (uint64): Количество бит для сдвига.

    Returns:
        uint64: Результат циклического сдвига.
    """
    n = n % 64
    return ((x << n) | (x >> (64 - n))) & 0xFFFFFFFFFFFFFFFF


@jit(nopython=True, cache=True)
def _keccak_f1600(state, RC):
    """
    Выполнение преобразования Keccak-f[1600] над состоянием.

    Args:
        state (ndarray): Массив 5x5 64-битных слов, представляющий состояние.
        RC (ndarray): Массив круглых констант.

    Returns:
        ndarray: Преобразованное состояние.
    """
    for round_idx in range(24):

        C = np.zeros(5, dtype=np.uint64)
        for x in range(5):
            C[x] = state[x, 0] ^ state[x, 1] ^ state[x, 2] ^ state[x, 3] ^ state[x, 4]

        D = np.zeros(5, dtype=np.uint64)
        for x in range(5):
            D[x] = C[(x - 1) % 5] ^ _rotl64(C[(x + 1) % 5], uint64(1))

        for x in range(5):
            for y in range(5):
                state[x, y] ^= D[x]

        B = np.zeros((5, 5), dtype=np.uint64)
        for x in range(5):
            for y in range(5):
                B[y, (2 * x + 3 * y) % 5] = _rotl64(state[x, y], RHO_OFFSETS[x, y])

        for x in range(5):
            for y in range(5):
                state[x, y] = B[x, y] ^ ((~B[(x + 1) % 5, y]) & B[(x + 2) % 5, y])

        state[0, 0] ^= RC[round_idx]

    return state


@jit(nopython=True, cache=True)
def _absorb_block(state, block, rate_bytes):
    """
    Поглощение блока данных в состояние sponge-функции.

    Args:
        state (ndarray): Массив 5x5 64-битных слов, представляющий состояние.
        block (ndarray): Блок данных для поглощения.
        rate_bytes (int): Размер поглощающей части (rate) в байтах.

    Returns:
        ndarray: Обновленное состояние.
    """
    rate_lanes = rate_bytes // 8

    for i in range(rate_lanes):
        x = i % 5
        y = i // 5

        lane = uint64(0)
        for j in range(8):
            if i * 8 + j < len(block):
                lane |= uint64(block[i * 8 + j]) << uint64(j * 8)
        state[x, y] ^= lane

    return state


@jit(nopython=True, cache=True)
def _squeeze(state, output_bytes):
    """
    Извлечение хэша из состояния sponge-функции.

    Args:
        state (ndarray): Массив 5x5 64-битных слов, представляющий состояние.
        output_bytes (int): Размер выходного хэша в байтах.

    Returns:
        ndarray: Байтовый массив с хэшем.
    """
    output = np.zeros(output_bytes, dtype=np.uint8)

    idx = 0
    for i in range(output_bytes // 8 + 1):
        if idx >= output_bytes:
            break
        x = i % 5
        y = i // 5
        lane = state[x, y]
        for j in range(8):
            if idx < output_bytes:
                output[idx] = uint8((lane >> uint64(j * 8)) & uint64(0xFF))
                idx += 1

    return output


@jit(nopython=True, cache=True)
def _process_absorb(state, data, rate_bytes, RC):
    """
    Обработка поглощения всех полных блоков данных.

    Args:
        state (ndarray): Массив 5x5 64-битных слов, представляющий состояние.
        data (ndarray): Входные данные для хэширования.
        rate_bytes (int): Размер поглощающей части (rate) в байтах.
        RC (ndarray): Массив круглых констант.

    Returns:
        ndarray: Обновленное состояние.
    """
    num_blocks = len(data) // rate_bytes

    for block_idx in range(num_blocks):
        start = block_idx * rate_bytes
        block = data[start:start + rate_bytes]
        state = _absorb_block(state, block, rate_bytes)
        state = _keccak_f1600(state, RC)

    return state


@jit(nopython=True, cache=True)
def _finalize_and_squeeze(state, padded_last_block, rate_bytes, output_bytes, RC):
    """
    Финализация хэширования и извлечение результата.

    Args:
        state (ndarray): Массив 5x5 64-битных слов, представляющий состояние.
        padded_last_block (ndarray): Последний блок данных с добавлением padding.
        rate_bytes (int): Размер поглощающей части (rate) в байтах.
        output_bytes (int): Размер выходного хэша в байтах.
        RC (ndarray): Массив круглых констант.

    Returns:
        ndarray: Байтовый массив с хэшем.
    """
    state = _absorb_block(state, padded_last_block, rate_bytes)
    state = _keccak_f1600(state, RC)
    return _squeeze(state, output_bytes)


class SHA3_256:
    """
    Реализация хэш-функции SHA3-256 по стандарту NIST FIPS 202, используя конструкцию Keccak sponge.

    Атрибуты:
        RATE_BITS (int): Размер поглощающей части (rate) в битах.
        RATE_BYTES (int): Размер поглощающей части (rate) в байтах.
        CAPACITY_BITS (int): Размер емкостной части (capacity) в битах.
        OUTPUT_BYTES (int): Размер выходного хэша в байтах.
        DOMAIN_SUFFIX (int): Суффикс домена для SHA3-256.
    """

    # SHA3-256 параметры
    RATE_BITS = 1088
    RATE_BYTES = 136
    CAPACITY_BITS = 512
    OUTPUT_BYTES = 32

    DOMAIN_SUFFIX = 0x06

    def __init__(self):
        """Инициализация объекта SHA3-256."""
        self.reset()

    def reset(self):
        """
        Сброс состояния хэш-функции в начальное.

        Инициализирует состояние, буфер и флаг финализации.
        """
        self.state = np.zeros((5, 5), dtype=np.uint64)
        self.buffer = bytearray()
        self.finalized = False

    def update(self, data):
        """
        Добавление данных для хэширования.

        Args:
            data (bytes или str): Данные для добавления. Строки кодируются в UTF-8.

        Raises:
            RuntimeError: Если хэш уже финализирован.
        """
        if self.finalized:
            raise RuntimeError("Hash already finalized")

        if isinstance(data, str):
            data = data.encode('utf-8')

        self.buffer.extend(data)

        while len(self.buffer) >= self.RATE_BYTES:
            block = np.frombuffer(bytes(self.buffer[:self.RATE_BYTES]), dtype=np.uint8)
            self.state = _absorb_block(self.state, block, self.RATE_BYTES)
            self.state = _keccak_f1600(self.state, RC)
            del self.buffer[:self.RATE_BYTES]

    def _pad_message(self, data_len):
        """
        Добавление padding к сообщению согласно стандарту SHA3.

        Args:
            data_len (int): Длина данных в буфере.

        Returns:
            bytearray: Байтовый массив с padding.
        """
        remaining = bytearray(self.buffer)
        pad_len = self.RATE_BYTES - len(remaining)

        if pad_len == 1:

            remaining.append(0x86)
        else:

            remaining.append(self.DOMAIN_SUFFIX)

            remaining.extend(b'\x00' * (pad_len - 2))

            remaining.append(0x80)

        return remaining

    def digest(self):
        """
        Получение хэша в виде байтов.

        Returns:
            bytes: Хэш SHA3-256 в виде байтовой строки.
        """
        if not self.finalized:
            saved_state = self.state.copy()
            saved_buffer = bytearray(self.buffer)

            padded = self._pad_message(len(self.buffer))
            padded_np = np.frombuffer(bytes(padded), dtype=np.uint8)

            result = _finalize_and_squeeze(
                self.state, padded_np, self.RATE_BYTES, self.OUTPUT_BYTES, RC
            )

            self._digest_cache = bytes(result)
            self.finalized = True

            self.state = saved_state
            self.buffer = saved_buffer

        return self._digest_cache

    def hexdigest(self):
        """
        Получение хэша в виде шестнадцатеричной строки.

        Returns:
            str: Хэш SHA3-256 в виде шестнадцатеричной строки.
        """
        return self.digest().hex()

    def copy(self):
        """
        Создание копии объекта хэш-функции.

        Returns:
            SHA3_256: Новая копия объекта с текущим состоянием.
        """
        new_hash = SHA3_256()
        new_hash.state = self.state.copy()
        new_hash.buffer = bytearray(self.buffer)
        new_hash.finalized = self.finalized
        if self.finalized:
            new_hash._digest_cache = self._digest_cache
        return new_hash


def sha3_256_data(data):
    """
    Вычисление хэша SHA3-256 для данных.

    Args:
        data (bytes или str): Данные для хэширования.

    Returns:
        str: Хэш SHA3-256 в виде шестнадцатеричной строки.
    """
    sha = SHA3_256()

    if isinstance(data, str):
        data = data.encode('utf-8')

    sha.update(data)
    return sha.hexdigest()


def sha3_256_file(filename, chunk_size=8192):  # 131072
    """
    Вычисление хэша SHA3-256 для файла.

    Args:
        filename (str): Путь к файлу для хэширования.
        chunk_size (int): Размер чанка для чтения файла.

    Returns:
        str: Хэш SHA3-256 в виде шестнадцатеричной строки.
    """
    sha = SHA3_256()

    chunk_size = (chunk_size // sha.RATE_BYTES) * sha.RATE_BYTES
    if chunk_size == 0:
        chunk_size = sha.RATE_BYTES

    with open(filename, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha.update(chunk)

    return sha.hexdigest()