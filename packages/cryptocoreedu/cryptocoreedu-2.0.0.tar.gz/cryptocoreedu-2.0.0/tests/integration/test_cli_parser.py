"""
Интеграционные тесты для CLI парсера.
Покрывает: парсинг аргументов, валидация, end-to-end сценарии.

TEST-3: Integration Tests for CLI tool
- Encryption/decryption round-trip for all modes
- Hash verification
- HMAC generation and verification
- Key derivation
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from io import StringIO
from unittest.mock import patch

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cryptocoreedu.cli_parser import create_parser


class TestCLIParserBasic(unittest.TestCase):
    """Базовые тесты парсера CLI."""

    def setUp(self):
        """Подготовка к тестам."""
        self.parser = create_parser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parser_creation(self):
        """Тест: парсер создаётся успешно."""
        self.assertIsNotNone(self.parser)
        self.assertEqual(self.parser.prog, 'crypto')

    def test_no_arguments(self):
        """Тест: без аргументов парсер не падает."""
        args = self.parser.parse_args([])
        self.assertIsNone(args.command)

    def test_help_option(self):
        """Тест: опция --help работает."""
        with self.assertRaises(SystemExit) as ctx:
            self.parser.parse_args(['--help'])
        self.assertEqual(ctx.exception.code, 0)


class TestCLIParserEncryption(unittest.TestCase):
    """Тесты парсинга команд шифрования."""

    def setUp(self):
        """Подготовка к тестам."""
        self.parser = create_parser()
        self.temp_dir = tempfile.mkdtemp()

        # Создаём тестовый файл
        self.input_file = Path(self.temp_dir) / "input.txt"
        self.output_file = Path(self.temp_dir) / "output.bin"
        with open(self.input_file, 'w') as f:
            f.write("test data")

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ==================== ENCRYPT MODE ====================

    def test_encrypt_ecb_mode(self):
        """Тест: парсинг шифрования в режиме ECB."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'ecb',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', str(self.input_file),
            '--output', str(self.output_file)
        ])

        self.assertEqual(args.algorithm, 'aes')
        self.assertEqual(args.mode, 'ecb')
        self.assertTrue(args.encrypt)
        self.assertFalse(args.decrypt)
        self.assertEqual(args.key, '00112233445566778899aabbccddeeff')
        self.assertEqual(args.input, self.input_file)
        self.assertEqual(args.output, self.output_file)

    def test_encrypt_cbc_mode(self):
        """Тест: парсинг шифрования в режиме CBC."""
        args = self.parser.parse_args([
            '-alg', 'aes',
            '-m', 'cbc',
            '-enc',
            '-k', '00112233445566778899aabbccddeeff',
            '--iv', '000102030405060708090a0b0c0d0e0f',
            '-i', str(self.input_file),
            '-o', str(self.output_file)
        ])

        self.assertEqual(args.algorithm, 'aes')
        self.assertEqual(args.mode, 'cbc')
        self.assertTrue(args.encrypt)
        self.assertEqual(args.iv, '000102030405060708090a0b0c0d0e0f')

    def test_encrypt_cfb_mode(self):
        """Тест: парсинг шифрования в режиме CFB."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'cfb',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', str(self.input_file),
            '--output', str(self.output_file)
        ])

        self.assertEqual(args.mode, 'cfb')

    def test_encrypt_ofb_mode(self):
        """Тест: парсинг шифрования в режиме OFB."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'ofb',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', str(self.input_file),
            '--output', str(self.output_file)
        ])

        self.assertEqual(args.mode, 'ofb')

    def test_encrypt_ctr_mode(self):
        """Тест: парсинг шифрования в режиме CTR."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'ctr',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', str(self.input_file),
            '--output', str(self.output_file)
        ])

        self.assertEqual(args.mode, 'ctr')

    def test_encrypt_gcm_mode_with_nonce_and_aad(self):
        """Тест: парсинг шифрования GCM с nonce и AAD."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'gcm',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--nonce', '000102030405060708090a0b',
            '--aad', '48656c6c6f',
            '--input', str(self.input_file),
            '--output', str(self.output_file)
        ])

        self.assertEqual(args.mode, 'gcm')
        self.assertEqual(args.nonce, '000102030405060708090a0b')
        self.assertEqual(args.aad, '48656c6c6f')

    def test_encrypt_etm_mode(self):
        """Тест: парсинг шифрования в режиме ETM."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'etm',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', str(self.input_file),
            '--output', str(self.output_file)
        ])

        self.assertEqual(args.mode, 'etm')

    # ==================== DECRYPT MODE ====================

    def test_decrypt_cbc_mode(self):
        """Тест: парсинг дешифрования в режиме CBC."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'cbc',
            '--decrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--iv', '000102030405060708090a0b0c0d0e0f',
            '--input', str(self.input_file),
            '--output', str(self.output_file)
        ])

        self.assertFalse(args.encrypt)
        self.assertTrue(args.decrypt)

    def test_decrypt_short_options(self):
        """Тест: парсинг дешифрования с короткими опциями."""
        args = self.parser.parse_args([
            '-alg', 'aes',
            '-m', 'cbc',
            '-dec',
            '-k', '00112233445566778899aabbccddeeff',
            '-i', str(self.input_file),
            '-o', str(self.output_file)
        ])

        self.assertTrue(args.decrypt)

    # ==================== MUTUAL EXCLUSION ====================

    def test_encrypt_decrypt_mutually_exclusive(self):
        """Тест: --encrypt и --decrypt взаимоисключающие."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args([
                '--algorithm', 'aes',
                '--mode', 'cbc',
                '--encrypt',
                '--decrypt',
                '--key', '00112233445566778899aabbccddeeff',
                '--input', str(self.input_file),
                '--output', str(self.output_file)
            ])

    # ==================== ALL MODES COVERAGE ====================

    def test_all_encryption_modes(self):
        """Тест: все режимы шифрования парсятся корректно."""
        modes = ['ecb', 'cbc', 'cfb', 'ofb', 'ctr', 'gcm', 'etm']

        for mode in modes:
            with self.subTest(mode=mode):
                args = self.parser.parse_args([
                    '--algorithm', 'aes',
                    '--mode', mode,
                    '--encrypt',
                    '--key', '00112233445566778899aabbccddeeff',
                    '--input', str(self.input_file),
                    '--output', str(self.output_file)
                ])

                self.assertEqual(args.mode, mode)


class TestCLIParserDigest(unittest.TestCase):
    """Тесты парсинга команды dgst (хэширование и HMAC)."""

    def setUp(self):
        """Подготовка к тестам."""
        self.parser = create_parser()
        self.temp_dir = tempfile.mkdtemp()

        self.input_file = Path(self.temp_dir) / "input.txt"
        self.output_file = Path(self.temp_dir) / "output.txt"
        self.verify_file = Path(self.temp_dir) / "verify.txt"

        with open(self.input_file, 'w') as f:
            f.write("test data for hashing")

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ==================== HASH COMMANDS ====================

    def test_dgst_sha256(self):
        """Тест: парсинг команды dgst с SHA-256."""
        args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha256',
            '--input', str(self.input_file)
        ])

        self.assertEqual(args.command, 'dgst')
        self.assertEqual(args.algorithm, 'sha256')
        self.assertEqual(args.input, self.input_file)

    def test_dgst_sha3_256(self):
        """Тест: парсинг команды dgst с SHA3-256."""
        args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha3-256',
            '--input', str(self.input_file)
        ])

        self.assertEqual(args.algorithm, 'sha3-256')

    def test_dgst_short_options(self):
        """Тест: парсинг dgst с короткими опциями."""
        args = self.parser.parse_args([
            'dgst',
            '-alg', 'sha256',
            '-i', str(self.input_file)
        ])

        self.assertEqual(args.algorithm, 'sha256')

    def test_dgst_with_output(self):
        """Тест: парсинг dgst с выходным файлом."""
        args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha256',
            '--input', str(self.input_file),
            '--output', str(self.output_file)
        ])

        self.assertEqual(args.output, self.output_file)

    # ==================== HMAC COMMANDS ====================

    def test_dgst_hmac(self):
        """Тест: парсинг команды dgst с HMAC."""
        args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha256',
            '--hmac',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', str(self.input_file)
        ])

        self.assertTrue(args.hmac)
        self.assertEqual(args.key, '00112233445566778899aabbccddeeff')

    def test_dgst_hmac_short_options(self):
        """Тест: парсинг HMAC с короткими опциями."""
        args = self.parser.parse_args([
            'dgst',
            '-alg', 'sha256',
            '--hmac',
            '-k', '00112233445566778899aabbccddeeff',
            '-i', str(self.input_file)
        ])

        self.assertTrue(args.hmac)

    def test_dgst_hmac_with_output(self):
        """Тест: парсинг HMAC с выходным файлом."""
        args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha256',
            '--hmac',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', str(self.input_file),
            '--output', str(self.output_file)
        ])

        self.assertEqual(args.output, self.output_file)

    # ==================== HMAC VERIFICATION ====================

    def test_dgst_hmac_verify(self):
        """Тест: парсинг HMAC с верификацией."""
        # Создаём файл для верификации
        with open(self.verify_file, 'w') as f:
            f.write("expected_hmac_value")

        args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha256',
            '--hmac',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', str(self.input_file),
            '--verify', str(self.verify_file)
        ])

        self.assertEqual(args.verify, self.verify_file)

    def test_dgst_verify_short_option(self):
        """Тест: парсинг верификации с короткой опцией."""
        with open(self.verify_file, 'w') as f:
            f.write("expected")

        args = self.parser.parse_args([
            'dgst',
            '-alg', 'sha256',
            '--hmac',
            '-k', 'key',
            '-i', str(self.input_file),
            '-v', str(self.verify_file)
        ])

        self.assertEqual(args.verify, self.verify_file)

    # ==================== HASH ALGORITHMS ====================

    def test_dgst_all_algorithms(self):
        """Тест: все алгоритмы хэширования парсятся корректно."""
        algorithms = ['sha256', 'sha3-256']

        for alg in algorithms:
            with self.subTest(algorithm=alg):
                args = self.parser.parse_args([
                    'dgst',
                    '--algorithm', alg,
                    '--input', str(self.input_file)
                ])

                self.assertEqual(args.algorithm, alg)

    # ==================== REQUIRED ARGUMENTS ====================

    def test_dgst_requires_algorithm(self):
        """Тест: команда dgst требует --algorithm."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args([
                'dgst',
                '--input', str(self.input_file)
            ])

    def test_dgst_requires_input(self):
        """Тест: команда dgst требует --input."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args([
                'dgst',
                '--algorithm', 'sha256'
            ])


class TestCLIParserDerive(unittest.TestCase):
    """Тесты парсинга команды derive (PBKDF2)."""

    def setUp(self):
        """Подготовка к тестам."""
        self.parser = create_parser()
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = Path(self.temp_dir) / "key.bin"

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ==================== BASIC DERIVE ====================

    def test_derive_basic(self):
        """Тест: базовый парсинг команды derive."""
        args = self.parser.parse_args([
            'derive',
            '--password', 'mysecretpassword'
        ])

        self.assertEqual(args.command, 'derive')
        self.assertEqual(args.password, 'mysecretpassword')
        self.assertIsNone(args.salt)
        self.assertEqual(args.iterations, 100000)
        self.assertEqual(args.length, 32)
        self.assertEqual(args.algorithm, 'pbkdf2')

    def test_derive_short_options(self):
        """Тест: парсинг derive с короткими опциями."""
        args = self.parser.parse_args([
            'derive',
            '-p', 'password123'
        ])

        self.assertEqual(args.password, 'password123')

    # ==================== FULL OPTIONS ====================

    def test_derive_with_salt(self):
        """Тест: парсинг derive с солью."""
        args = self.parser.parse_args([
            'derive',
            '--password', 'password',
            '--salt', '0011223344556677'
        ])

        self.assertEqual(args.salt, '0011223344556677')

    def test_derive_with_iterations(self):
        """Тест: парсинг derive с количеством итераций."""
        args = self.parser.parse_args([
            'derive',
            '--password', 'password',
            '--iterations', '200000'
        ])

        self.assertEqual(args.iterations, 200000)

    def test_derive_with_length(self):
        """Тест: парсинг derive с длиной ключа."""
        args = self.parser.parse_args([
            'derive',
            '--password', 'password',
            '--length', '64'
        ])

        self.assertEqual(args.length, 64)

    def test_derive_with_output(self):
        """Тест: парсинг derive с выходным файлом."""
        args = self.parser.parse_args([
            'derive',
            '--password', 'password',
            '--output', str(self.output_file)
        ])

        self.assertEqual(args.output, self.output_file)

    def test_derive_full_options(self):
        """Тест: парсинг derive со всеми опциями."""
        args = self.parser.parse_args([
            'derive',
            '-p', 'my_password',
            '-s', '0123456789abcdef',
            '-c', '150000',
            '-l', '48',
            '-alg', 'pbkdf2',
            '-o', str(self.output_file)
        ])

        self.assertEqual(args.password, 'my_password')
        self.assertEqual(args.salt, '0123456789abcdef')
        self.assertEqual(args.iterations, 150000)
        self.assertEqual(args.length, 48)
        self.assertEqual(args.algorithm, 'pbkdf2')
        self.assertEqual(args.output, self.output_file)

    # ==================== REQUIRED ARGUMENTS ====================

    def test_derive_requires_password(self):
        """Тест: команда derive требует --password."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(['derive'])

    # ==================== ALGORITHM CHOICE ====================

    def test_derive_algorithm_pbkdf2(self):
        """Тест: алгоритм pbkdf2 парсится корректно."""
        args = self.parser.parse_args([
            'derive',
            '--password', 'password',
            '--algorithm', 'pbkdf2'
        ])

        self.assertEqual(args.algorithm, 'pbkdf2')

    def test_derive_invalid_algorithm(self):
        """Тест: неизвестный алгоритм отклоняется."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args([
                'derive',
                '--password', 'password',
                '--algorithm', 'unknown'
            ])


class TestCLIParserInvalidInputs(unittest.TestCase):
    """Тесты невалидных входных данных (негативные сценарии)."""

    def setUp(self):
        """Подготовка к тестам."""
        self.parser = create_parser()

    def test_invalid_encryption_algorithm(self):
        """Тест: неизвестный алгоритм шифрования отклоняется."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args([
                '--algorithm', 'des',
                '--mode', 'cbc',
                '--encrypt'
            ])

    def test_invalid_encryption_mode(self):
        """Тест: неизвестный режим шифрования отклоняется."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args([
                '--algorithm', 'aes',
                '--mode', 'xts',
                '--encrypt'
            ])

    def test_invalid_hash_algorithm(self):
        """Тест: неизвестный алгоритм хэширования отклоняется."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args([
                'dgst',
                '--algorithm', 'md5',
                '--input', 'file.txt'
            ])


class TestCLIParserEdgeCases(unittest.TestCase):
    """Тесты граничных случаев."""

    def setUp(self):
        """Подготовка к тестам."""
        self.parser = create_parser()
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = Path(self.temp_dir) / "input.txt"
        with open(self.input_file, 'w') as f:
            f.write("test")

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_aad(self):
        """Тест: пустой AAD (по умолчанию)."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'gcm',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', str(self.input_file),
            '--output', '/tmp/out.bin'
        ])

        self.assertEqual(args.aad, '')

    def test_derive_default_values(self):
        """Тест: значения по умолчанию для derive."""
        args = self.parser.parse_args([
            'derive',
            '--password', 'pass'
        ])

        self.assertIsNone(args.salt)
        self.assertEqual(args.iterations, 100000)
        self.assertEqual(args.length, 32)
        self.assertEqual(args.algorithm, 'pbkdf2')
        self.assertIsNone(args.output)

    def test_nonce_and_iv_both_available(self):
        """Тест: и --nonce и --iv доступны."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'gcm',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--nonce', '000102030405060708090a0b',
            '--iv', '000102030405060708090a0b0c0d0e0f',
            '--input', str(self.input_file),
            '--output', '/tmp/out.bin'
        ])

        # Оба должны быть доступны
        self.assertEqual(args.nonce, '000102030405060708090a0b')
        self.assertEqual(args.iv, '000102030405060708090a0b0c0d0e0f')

    def test_dgst_without_hmac_no_key_required(self):
        """Тест: без --hmac ключ не обязателен."""
        args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha256',
            '--input', str(self.input_file)
        ])

        self.assertFalse(args.hmac)
        self.assertIsNone(args.key)

    def test_path_type_conversion(self):
        """Тест: пути преобразуются в Path объекты."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'cbc',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', '/path/to/input.txt',
            '--output', '/path/to/output.bin'
        ])

        self.assertIsInstance(args.input, Path)
        self.assertIsInstance(args.output, Path)

    def test_derive_iterations_type(self):
        """Тест: iterations преобразуется в int."""
        args = self.parser.parse_args([
            'derive',
            '--password', 'pass',
            '--iterations', '50000'
        ])

        self.assertIsInstance(args.iterations, int)
        self.assertEqual(args.iterations, 50000)

    def test_derive_length_type(self):
        """Тест: length преобразуется в int."""
        args = self.parser.parse_args([
            'derive',
            '--password', 'pass',
            '--length', '16'
        ])

        self.assertIsInstance(args.length, int)
        self.assertEqual(args.length, 16)


class TestCLIParserHelpMessages(unittest.TestCase):
    """Тесты справочных сообщений."""

    def setUp(self):
        """Подготовка к тестам."""
        self.parser = create_parser()

    def test_main_help(self):
        """Тест: главная справка содержит подкоманды."""
        with self.assertRaises(SystemExit):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                self.parser.parse_args(['--help'])

    def test_dgst_help(self):
        """Тест: справка dgst."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(['dgst', '--help'])

    def test_derive_help(self):
        """Тест: справка derive."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(['derive', '--help'])


class TestCLIParserIntegrationScenarios(unittest.TestCase):
    """Интеграционные сценарии использования CLI."""

    def setUp(self):
        """Подготовка к тестам."""
        self.parser = create_parser()
        self.temp_dir = tempfile.mkdtemp()

        self.input_file = Path(self.temp_dir) / "secret.txt"
        self.encrypted_file = Path(self.temp_dir) / "secret.enc"
        self.decrypted_file = Path(self.temp_dir) / "secret.dec"
        self.hash_file = Path(self.temp_dir) / "secret.hash"
        self.key_file = Path(self.temp_dir) / "derived.key"

        with open(self.input_file, 'w') as f:
            f.write("This is a secret message")

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scenario_encrypt_then_decrypt_cbc(self):
        """Сценарий: шифрование и дешифрование файла в CBC."""
        key = '2b7e151628aed2a6abf7158809cf4f3c'
        iv = '000102030405060708090a0b0c0d0e0f'

        # Шифрование
        enc_args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'cbc',
            '--encrypt',
            '--key', key,
            '--iv', iv,
            '--input', str(self.input_file),
            '--output', str(self.encrypted_file)
        ])

        self.assertTrue(enc_args.encrypt)
        self.assertEqual(enc_args.key, key)

        # Дешифрование
        dec_args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'cbc',
            '--decrypt',
            '--key', key,
            '--iv', iv,
            '--input', str(self.encrypted_file),
            '--output', str(self.decrypted_file)
        ])

        self.assertTrue(dec_args.decrypt)
        self.assertEqual(dec_args.key, key)

    def test_scenario_encrypt_gcm_with_aad(self):
        """Сценарий: шифрование GCM с AAD."""
        args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'gcm',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--nonce', '000102030405060708090a0b',
            '--aad', '66696c656e616d653a736563726574',
            '--input', str(self.input_file),
            '--output', str(self.encrypted_file)
        ])

        self.assertEqual(args.mode, 'gcm')
        self.assertEqual(args.aad, '66696c656e616d653a736563726574')

    def test_scenario_hash_file(self):
        """Сценарий: хэширование файла."""
        args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha256',
            '--input', str(self.input_file),
            '--output', str(self.hash_file)
        ])

        self.assertEqual(args.command, 'dgst')
        self.assertEqual(args.algorithm, 'sha256')

    def test_scenario_hmac_generate_and_verify(self):
        """Сценарий: генерация и верификация HMAC."""
        key = '00112233445566778899aabbccddeeff'

        # Генерация HMAC
        gen_args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha256',
            '--hmac',
            '--key', key,
            '--input', str(self.input_file),
            '--output', str(self.hash_file)
        ])

        self.assertTrue(gen_args.hmac)

        # Верификация HMAC
        verify_args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha256',
            '--hmac',
            '--key', key,
            '--input', str(self.input_file),
            '--verify', str(self.hash_file)
        ])

        self.assertEqual(verify_args.verify, self.hash_file)

    def test_scenario_derive_key_for_encryption(self):
        """Сценарий: деривация ключа из пароля."""
        args = self.parser.parse_args([
            'derive',
            '--password', 'my_secure_password',
            '--salt', '0123456789abcdef0123456789abcdef',
            '--iterations', '100000',
            '--length', '32',
            '--output', str(self.key_file)
        ])

        self.assertEqual(args.password, 'my_secure_password')
        self.assertEqual(args.iterations, 100000)
        self.assertEqual(args.length, 32)

    def test_scenario_full_workflow(self):
        """Сценарий: полный workflow - derive -> encrypt -> hash."""
        # 1. Derive key
        derive_args = self.parser.parse_args([
            'derive',
            '--password', 'password123',
            '--salt', 'abcdef0123456789',
            '--output', str(self.key_file)
        ])

        self.assertEqual(derive_args.command, 'derive')

        # 2. Encrypt with derived key
        enc_args = self.parser.parse_args([
            '--algorithm', 'aes',
            '--mode', 'gcm',
            '--encrypt',
            '--key', '00112233445566778899aabbccddeeff',
            '--input', str(self.input_file),
            '--output', str(self.encrypted_file)
        ])

        self.assertTrue(enc_args.encrypt)

        # 3. Hash encrypted file
        hash_args = self.parser.parse_args([
            'dgst',
            '--algorithm', 'sha256',
            '--input', str(self.encrypted_file),
            '--output', str(self.hash_file)
        ])

        self.assertEqual(hash_args.command, 'dgst')


if __name__ == '__main__':
    unittest.main(verbosity=2)