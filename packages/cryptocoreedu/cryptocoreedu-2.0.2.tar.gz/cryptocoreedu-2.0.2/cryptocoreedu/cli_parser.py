import argparse
from pathlib import Path


def create_parser():
    """
    Создание парсера аргументов командной строки для CryptoCore.

    Returns:
        argparse.ArgumentParser: Настроенный парсер аргументов.
    """
    parser = argparse.ArgumentParser(
        description='CryptoCore - Cryptographic Tool',
        prog='crypto',
        allow_abbrev=False
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Команды',
        title='subcommands',
        description='valid subcommands',
        metavar='{dgst, derive}'
    )

    # ==================== Основная команда crypto ====================
    # Для шифрования/дешифрования

    parser.add_argument('--algorithm', '-alg', choices=['aes'],
                        help='Алгоритм шифрования')
    parser.add_argument('--mode', '-m', choices=['ecb', 'cbc', 'cfb', 'ofb', 'ctr', 'gcm', 'etm'],
                        help='Режим работы')

    mode_group = parser.add_mutually_exclusive_group(required=False)
    mode_group.add_argument('--encrypt', '-enc', action='store_true',
                            help='Режим шифрования')
    mode_group.add_argument('--decrypt', '-dec', action='store_true',
                            help='Режим дешифрования')

    parser.add_argument('--key', '-k', help='Ключ шифрования (128-бит)')
    parser.add_argument('--iv',
                        help='Вектор инициализации / Nonce в hex формате')
    parser.add_argument('--nonce',
                        help='Nonce для режима GCM (алиас для --iv, 12 байт в hex)')
    parser.add_argument('--aad', type=str, default='',
                        help='Ассоциированные аутентификационные данные в hex формате')

    parser.add_argument('--input', '-i', type=Path, help='Входной файл')
    parser.add_argument('--output', '-o', type=Path, help='Выходной файл')

    # ==================== Подкоманда dgst ====================

    dgst_parser = subparsers.add_parser('dgst', help='Вычисление хеш-сумм и HMAC',
                                        allow_abbrev=False)

    dgst_parser.add_argument('--algorithm', '-alg',
                             choices=['sha256', 'sha3-256'],
                             required=True,
                             help='Алгоритм хеширования')

    dgst_parser.add_argument('--input', '-i', type=Path, required=True,
                             help='Входной файл')

    dgst_parser.add_argument('--output', '-o', type=Path,
                             help='Выходной файл для записи хеша')

    dgst_parser.add_argument('--hmac', action='store_true',
                             help='Включить режим HMAC (требует --key)')

    dgst_parser.add_argument('--key', '-k', type=str,
                             help='Секретный ключ в hex формате (обязателен для --hmac)')

    dgst_parser.add_argument('--verify', '-v', type=Path,
                             help='Файл с ожидаемым HMAC для верификации')

    # ==================== Подкоманда derive ====================

    derive_parser = subparsers.add_parser(
        'derive',
        help='Получение ключа (PBKDF2 из пароля или HKDF из мастер-ключа)',
        allow_abbrev=False
    )

    # === Аргументы для PBKDF2 ===
    derive_parser.add_argument(
        '--password', '-p',
        type=str,
        default=None,
        help='Пароль для генерации ключа (PBKDF2)'
    )

    derive_parser.add_argument(
        '--salt', '-s',
        type=str,
        default=None,
        help='Соль в hex формате (для PBKDF2, если не указана — генерируется)'
    )

    derive_parser.add_argument(
        '--iterations', '-c',
        type=int,
        default=100000,
        help='Количество итераций (для PBKDF2, по умолчанию: 100000)'
    )

    # === Аргументы для HKDF ===
    derive_parser.add_argument(
        '--master-key', '-msk',
        type=str,
        default=None,
        help='Мастер-ключ в hex формате (HKDF)'
    )

    derive_parser.add_argument(
        '--context', '-con',
        type=str,
        default=None,
        help='Контекст для деривации ключа (HKDF)'
    )

    # === Общие аргументы ===
    derive_parser.add_argument(
        '--length', '-l',
        type=int,
        default=32,
        help='Длина выходного ключа в байтах (по умолчанию: 32)'
    )

    derive_parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Файл для записи ключа (в бинарном формате)'
    )

    return parser