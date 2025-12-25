import unittest
import sys
import os

# Добавляем путь к проекту для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptocoreedu.csprng import generate_random_bytes


class TestCsprng(unittest.TestCase):
    """Unit тесты для криптографически стойкого генератора случайных чисел."""

    def test_generate_random_bytes_valid_length(self):
        """Тест генерации случайных байтов валидной длины."""
        # Тест 1: Генерация 16 байт
        result = generate_random_bytes(16)
        self.assertEqual(len(result), 16)
        self.assertIsInstance(result, bytes)

        # Тест 2: Генерация 32 байта
        result = generate_random_bytes(32)
        self.assertEqual(len(result), 32)
        self.assertIsInstance(result, bytes)

        # Тест 3: Генерация 1 байта
        result = generate_random_bytes(1)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result, bytes)

        # Тест 4: Генерация 0 байт
        result = generate_random_bytes(0)
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, bytes)

        # Тест 5: Генерация 1024 байт (большой размер)
        result = generate_random_bytes(1024)
        self.assertEqual(len(result), 1024)
        self.assertIsInstance(result, bytes)

    def test_generate_random_bytes_uniqueness(self):
        """Тест уникальности сгенерированных последовательностей."""
        # Генерируем несколько последовательностей и проверяем их уникальность
        sequences = [generate_random_bytes(32) for _ in range(10)]

        # Проверяем, что все последовательности уникальны
        for i in range(len(sequences)):
            for j in range(i + 1, len(sequences)):
                self.assertNotEqual(sequences[i], sequences[j],
                                    f"Случайные последовательности {i} и {j} совпадают")

    def test_generate_random_bytes_randomness(self):
        """Тест случайности сгенерированных байтов."""
        # Генерируем большую последовательность и проверяем статистические свойства
        large_sequence = generate_random_bytes(10000)

        # Проверяем, что последовательность не состоит из одних нулей
        self.assertNotEqual(large_sequence, b'\x00' * 10000,
                            "Сгенерирована последовательность из одних нулей")

        # Проверяем, что последовательность не состоит из одних одинаковых байт
        all_same = True
        for byte in large_sequence[1:]:
            if byte != large_sequence[0]:
                all_same = False
                break
        self.assertFalse(all_same, "Все байты в последовательности одинаковы")

    def test_generate_random_bytes_large_input(self):
        """Тест генерации больших объемов данных."""
        # Тест 1: 1 MB данных
        result = generate_random_bytes(1024 * 1024)
        self.assertEqual(len(result), 1024 * 1024)
        self.assertIsInstance(result, bytes)

        # Тест 2: 10 MB данных (если система позволяет)
        result = generate_random_bytes(10 * 1024 * 1024)
        self.assertEqual(len(result), 10 * 1024 * 1024)
        self.assertIsInstance(result, bytes)

    def test_generate_random_bytes_negative_length(self):
        """Тест с отрицательной длиной (должен вызывать исключение в os.urandom)."""
        with self.assertRaises(Exception):
            generate_random_bytes(-1)

    def test_generate_random_bytes_type_safety(self):
        """Тест типовой безопасности - проверка, что функция возвращает правильный тип."""
        for length in [0, 1, 16, 32, 256, 1024]:
            result = generate_random_bytes(length)
            self.assertIsInstance(result, bytes,
                                  f"Для длины {length} возвращен неверный тип: {type(result)}")

    def test_generate_random_bytes_deterministic_test(self):
        """Тест для демонстрации недетерминированности генерации."""
        # Этот тест не проверяет конкретное значение, только что функция работает
        result1 = generate_random_bytes(16)
        result2 = generate_random_bytes(16)

        # Мы не можем утверждать, что они разные (теоретически могут совпасть),
        # но мы можем проверить, что функция не падает
        self.assertEqual(len(result1), 16)
        self.assertEqual(len(result2), 16)
        self.assertIsInstance(result1, bytes)
        self.assertIsInstance(result2, bytes)


if __name__ == '__main__':
    # Создаем тестовый набор
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCsprng)

    # Запускаем тесты с подробным выводом
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Выход с кодом ошибки, если тесты не прошли
    sys.exit(0 if result.wasSuccessful() else 1)