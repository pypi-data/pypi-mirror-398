# CryptoCoreEdu

**CryptoCoreEdu** — утилита командной строки для блочного шифрования файлов с использованием AES-128 в различных режимах работы, включая аутентифицированное шифрование. Проект разработан в образовательных целях для демонстрации принципов работы блочных шифров и криптографической аутентификации.

## Установка

### Способ 1: Установка из PyPI (рекомендуется)
```bash
# Установите пакет
pip install cryptocoreedu

# Или конкретной версии
pip install cryptocoreedu==2.0.2
```

### Способ 2: Установка из исходного кода
```bash
# Клонируйте репозиторий
git clone https://github.com/michaaans/CryptoCoreEdu.git
cd CryptoCoreEdu
# Установите виртуальное окружение
python3 -m venv vevn
# Активируйте виртуальное окружение
source venv/bin/activate
# Установите в режиме разработки
pip install -e .
```

## Проверка установки
### Windows (PowerShell)

```shell
# Проверьте что пакет установился (Windows)
pip list | findstr cryptocoreedu

# Проверьте работу утилиты
crypto --help 
# или 
crypto -h
```

### Linux/macOS/WSL (Bash)

```bash
# Проверьте что пакет установился
pip list | grep cryptocoreedu

# Проверьте работу утилиты
crypto --help
```

## Использование

### Поддерживаемые режимы
* ECB (Electronic Codebook) - базовый режим, требует паддинг

* CBC (Cipher Block Chaining) - блочный режим с цепочкой, требует паддинг

* CFB (Cipher Feedback) - потоковый режим, без паддинга

* OFB (Output Feedback) - потоковый режим, без паддинга

* CTR (Counter) - потоковый режим, без паддинга

* GCM (Galois/Counter Mode) - аутентифицированное шифрование по стандарту NIST SP 800-38D

* ETM (Encrypt-then-MAC) - составной режим CTR + HMAC-SHA256

### Базовые команды шифрования

**Вектор инициализации (IV) генерируется автоматически с помощью криптографически стойкого генератора псевдослучайных чисел**

```shell
# ECB режим (без IV)
crypto -alg aes -m ecb -enc -k 000102030405060708090a0b0c0d0e0f -i tests/document.txt -o tests/document.enc

# CBC режим (IV генерируется автоматически)
crypto -alg aes -m cbc -enc -k 000102030405060708090a0b0c0d0e0f -i tests/document.txt -o tests/document.enc

# CFB режим (потоковый)
crypto -alg aes -m cfb -enc -k 000102030405060708090a0b0c0d0e0f -i tests/document.txt -o tests/document.enc

# OFB режим (потоковый)  
crypto -alg aes -m ofb -enc -k 000102030405060708090a0b0c0d0e0f -i tests/document.txt -o tests/document.enc

# CTR режим (потоковый)
crypto -alg aes -m ctr -enc -k 000102030405060708090a0b0c0d0e0f -i tests/document.txt -o tests/document.enc
```

```bash
# ECB режим (без IV)
crypto -alg aes -m ecb -enc -k 000102030405060708090a0b0c0d0e0f -i tests/document.txt -o tests/document.enc

# CBC режим (IV генерируется автоматически)
crypto -alg aes -m cbc -enc -k 000102030405060708090a0b0c0d0e0f -i tests/document.txt -o tests/document.enc

# CFB режим (потоковый)
crypto -alg aes -m cfb -enc -k 000102030405060708090a0b0c0d0e0f -i tests/document.txt -o tests/document.enc

# OFB режим (потоковый)
crypto -alg aes -m ofb -enc -k 000102030405060708090a0b0c0d0e0f -i tests/document.txt -o tests/document.enc

# CTR режим (потоковый)
crypto -alg aes -m ctr -enc -k 000102030405060708090a0b0c0d0e0f -i tests/document.txt -o tests/document.enc
```

### Базовые команды дешифрования

```shell
# ECB режим (без IV)
crypto -alg aes -m ecb -dec -k 000102030405060708090a0b0c0d0e0f -i tests/document.enc -o tests/document_decrypted.txt

# CBC режим (IV извлекается из файла)
crypto -alg aes -m cbc -dec -k 000102030405060708090a0b0c0d0e0f -i tests/document.enc -o tests/document_decrypted.txt

# CBC режим (IV передается явно)
crypto -alg aes -m cbc -dec -k 000102030405060708090a0b0c0d0e0f --iv AABBCCDDEEFF00112233445566778899 -i tests/document.enc -o tests/document_decrypted.txt

# Потоковые режимы (CFB, OFB, CTR) - аналогично CBC
crypto -alg aes -m cfb -dec -k 000102030405060708090a0b0c0d0e0f -i tests/document.enc -o tests/document_decrypted.txt
```

```bash
# ECB режим (без IV)
crypto -alg aes -m ecb -dec -k 000102030405060708090a0b0c0d0e0f -i tests/document.enc -o tests/document_decrypted.txt

# CBC режим (IV извлекается из файла)
crypto -alg aes -m cbc -dec -k 000102030405060708090a0b0c0d0e0f -i tests/document.enc -o tests/document_decrypted.txt

# CBC режим (IV передается явно)
crypto -alg aes -m cbc -dec -k 000102030405060708090a0b0c0d0e0f --iv AABBCCDDEEFF00112233445566778899 -i tests/document.enc -o tests/document_decrypted.txt

# Потоковые режимы (CFB, OFB, CTR) - аналогично CBC
crypto -alg aes -m cfb -dec -k 000102030405060708090a0b0c0d0e0f -i tests/document.enc -o tests/document_decrypted.txt
```

### Параметры командной строки
- `--algorithm (-alg)`: Алгоритм шифрования (`aes`)
- `--mode (-m)`: Режим работы (`ecb`, `cbc`, `cfb`, `ofb`, `ctr`, `gcm`, `etm`)  
- `--encrypt (-enc)`: Режим шифрования
- `--decrypt (-dec)`: Режим дешифрования
- `--key (-k)`: Ключ шифрования (16 байт в hex-формате, необязателен при шифровании)
- `--iv`: Вектор инициализации (16 байт в hex-формате; только в режиме дешифрования)
- `--nonce (-n)`: Nonce для GCM (12 байт в hex; алиас для --iv)
- `--aad`: Associated Authenticated Data в hex (для GCM/ETM)
- `--input (-i)`: Входной файл
- `--output (-o)`: Выходной файл

### Свойства безопасности AEAD
| Свойство | Описание |
|----------|-----------|
| Защита от подмены      | Изменение любого бита ciphertext или tag приводит к ошибке аутентификации       |
| Защита AAD      | Изменение AAD также приводит к ошибке, хотя AAD не шифруется        |
| Катастрофический отказ      | При ошибке аутентификации НЕ выводятся никакие данные        |
| Уникальность nonce      | Каждое шифрование использует уникальный случайный nonce        |


### GCM Mode (Galois/Counter Mode)
#### Описание
GCM — стандартизированный режим аутентифицированного шифрования (NIST SP 800-38D), широко используемый в TLS, IPsec, SSH.

Характеристики:
* Nonce: 12 байт (96 бит)
* Tag: 16 байт (128 бит)
* Использует умножение в поле Галуа GF(2¹²⁸)
* Формат вывода: Nonce (12) || Ciphertext || Tag (16)

```bash
   # Шифрование с AAD
   crypto -alg aes -m gcm -enc \
       -k 00112233445566778899aabbccddeeff \
       --aad 48656c6c6f576f726c64 \
       -i tests/plain.txt \
       -o tests/cipher.bin
   
   # Шифрование без AAD
   crypto -alg aes -m gcm -enc \
       -k 00112233445566778899aabbccddeeff \
       -i tests/plain.txt \
       -o tests/cipher.bin
   
   # Расшифрование (nonce читается из файла автоматически)
   crypto -alg aes -m gcm -dec \
       -k 00112233445566778899aabbccddeeff \
       --aad 48656c6c6f576f726c64 \
       -i tests/cipher.bin \
       -o tests/decrypted.txt
   
   # Расшифрование с внешним nonce (через --nonce или --iv)
   crypto -alg aes -m gcm -dec \
       -k 00112233445566778899aabbccddeeff \
       --nonce 000102030405060708090a0b \
       --aad 48656c6c6f576f726c64 \
       -i tests/ciphertext_without_nonce.bin \
       -o tests/decrypted.txt

```

```bash
   # 1. Создаём тестовый файл
   echo -n "Secret message for GCM test" > tests/gcm_plain.txt
   
   # 2. Шифруем с AAD
   crypto -alg aes -m gcm -enc \
       -k 00112233445566778899aabbccddeeff \
       --aad 4d657461646174613132333435 \
       -i tests/gcm_plain.txt \
       -o tests/gcm_cipher.bin
   # Вывод: [INFO] Файл успешно зашифрован (GCM authenticated) в режиме GCM
   
   # 3. Расшифровываем с тем же AAD
   crypto -alg aes -m gcm -dec \
       -k 00112233445566778899aabbccddeeff \
       --aad 4d657461646174613132333435 \
       -i tests/gcm_cipher.bin \
       -o tests/gcm_decrypted.txt
   # Вывод: [INFO] Файл успешно расшифрован (GCM аутентификация успешна) в режиме GCM
   
   # 4. Проверяем
   diff -s tests/gcm_plain.txt tests/gcm_decrypted.txt
   # Вывод: Files tests/gcm_plain.txt and tests/gcm_decrypted.txt are identical
```

```bash
   # Расшифровываем с НЕВЕРНЫМ AAD
   crypto -a aes -m gcm -d \
       -k 00112233445566778899aabbccddeeff \
       --aad 576f726e6741414421 \
       -i tests/gcm_cipher.bin \
       -o tests/should_not_exist.txt
   
   # Вывод:
   # [ERROR] Ошибка аутентификации
   # [DETAILS] Authentication failed: AAD mismatch or ciphertext tampered
   #          Возможные причины:
   #          - Неверный AAD
   #          - Повреждённые данные
   #          - Неверный ключ
   
   # Файл НЕ создан
   ls tests/should_not_exist.txt
   # ls: cannot access 'tests/should_not_exist.txt': No such file or directory
```

### ETM Mode (Encrypt-then-MAC)
#### Описание
ETM — составной режим аутентифицированного шифрования, комбинирующий CTR mode для шифрования и HMAC-SHA256 для аутентификации.

Характеристики:
* IV: 16 байт (128 бит)
* Tag: 32 байта (256 бит, HMAC-SHA256)
* Использует раздельные ключи для шифрования и MAC (key separation)
* Формат вывода: IV (16) || Ciphertext || HMAC Tag (32)

Конструкция:

HMAC(K_m, Ciphertext || AAD) = Tag,
где K_e, K_m = DeriveKeys(MasterKey)

```bash
   # Шифрование с AAD
   crypto -alg aes -m etm -enc \
       -k 00112233445566778899aabbccddeeff \
       --aad 616263 \
       -i tests/plain.txt \
       -o tests/cipher.bin
   
   # Шифрование без AAD
   crypto -a aes -m etm -enc \
       -k 00112233445566778899aabbccddeeff \
       -i tests/plain.txt \
       -o tests/cipher.bin
   
   # Расшифрование
   crypto -alg aes -m etm -dec \
       -k 00112233445566778899aabbccddeeff \
       --aad 616263 \
       -i tests/cipher.bin \
       -o tests/decrypted.txt
```

```bash
   # 1. Создаём тестовый файл
   echo -n "Secret message for ETM test" > tests/etm_plain.txt
   
   # 2. Шифруем
   crypto -alg aes -m etm -enc \
       -k 00112233445566778899aabbccddeeff \
       --aad 746573745f616164 \
       -i tests/etm_plain.txt \
       -o tests/etm_cipher.bin
   # Вывод: [INFO] Файл успешно зашифрован (ETM (CTR+HMAC) authenticated) в режиме ETM
   
   # 3. Расшифровываем
   crypto -alg aes -m etm -dec \
       -k 00112233445566778899aabbccddeeff \
       --aad 746573745f616164 \
       -i tests/etm_cipher.bin \
       -o tests/etm_decrypted.txt
   # Вывод: [INFO] Файл успешно расшифрован (ETM (CTR+HMAC) аутентификация успешна) в режиме ETM
   
   # 4. Проверяем
   diff -s tests/etm_plain.txt tests/etm_decrypted.txt
   # Вывод: Files tests/etm_plain.txt and tests/etm_decrypted.txt are identical****
```

### AAD (Associated Authenticated Data)
#### Что такое AAD?

AAD — это дополнительные данные, которые:
* НЕ шифруются (остаются в открытом виде)
* Аутентифицируются (защищены от подмены)
* Используются для метаданных: заголовков, ID, timestamp и т.д.

#### Формат AAD
AAD передаётся как hex-строка, например, 48656c6c6f

### Команды хэширования и HMAC

```shell
  # Хэширование без указания выходного файла (Windows)
  crypto dgst -alg sha256 -i document.pdf
  5d5b09f6dcb2d53a5fffc60c4ac0d55fb052072fa2fe5d95f011b5d5d5b0b0b5  document.pdf
  # Хэширование с указанием выходного файла
  crypto dgst -alg sha3-256 -i backup.tar -o backup.sha3
```

```bash
   # Хэширование без указания выходного файла (Linux/MacOS/WSL)
  crypto dgst -alg sha256 -i document.pdf
  5d5b09f6dcb2d53a5fffc60c4ac0d55fb052072fa2fe5d95f011b5d5d5b0b0b5  document.pdf
  # Хэширование с указанием выходного файла
  crypto dgst -alg sha3-256 -i backup.tar -o backup.sha3
```

```bash
   # HMAC без указания выходного файла (Linux/MacOS/WSL)
  crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddeeff -i tests/message.txt
  # HMAC с указанием выходного файла
  crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddeeff -i tests/message.txt -o tests/hmac.txt
  # HMAC с указанием флага для верификации
  crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddeeff -i tests/message.txt -v tests/hmac.txt
  #Вывод: [OK] Проверка HMAC успешна
```
### Параметры хэш-функций и их особенности
#### Параметры хэширования:
- `--algorithm (-alg)`: Алгоритм хэширования (`sha256`, `sha3-256`)
- `--input (-i)`: Входной файл
- `--output (-o)`: Выходной файл (опционально)
#### Параметры HMAC:
- `--algorithm (-alg)`: Алгоритм хэширования (`sha256`, `sha3-256`)
- `--hmac`: Флаг для вычисления HMAC
- `--key (-k)`: Ключ для вычисления HMAC (обязателен для флага --hmac; может быть любой длины от 1 байта)
- `--input (-i)`: Входной файл
- `--output (-o)`: Выходной файл (опционально)
- `--verify (-v)`: Флаг для проверки сообщения

**Формат вывода хэша и HMAC**:
#### 5d5b09f6dcb2d53a5fffc60c4ac0d55fb052072fa2fe5d95f011b5d5d5b0b0b5  document.pdf

#### Особенности:

1. **Алгоритм SHA256**:
   - Реализован в соответствии со стандартом NIST FIPS 180-4
   - Использует конструкцию Меркля-Дамгарда
   - корретно реализует схему дополнения
   - реализует все константы SHA-256 и функции раундов.
   - Размер чанка 8192 байт.
   - Обработка больщих файлов (>1gb)

2. **Алгоритм SHA3-256**:
   - Реализован в соответствии со стандартом NIST FIPS 202
   - Использует губчатую конструкцию Keccak
   - Размер чанка 8192 байт.
   - Обработка больщих файлов (>1gb)

3. **Алгоритм HMAC-SHA-256**:
   - Реализован в соответствии со стандартом RFC 2104
   - Использует HMAC(K, m) = H((K ⊕ opad) ∥ H((K ⊕ ipad) ∥ m))
   - Обработка больщих файлов (>1gb)
   - Полностью соответствует RFC 4231
   - constant-time сравнение для верификации
   - ключи любой длины

### Размер ключа, IV и Nonce

| Параметр           | Размер            | Режимы                       |
|--------------------|-------------------|------------------------------|
| Ключ               | 16 байт (32 hex)  | Все режимы                   |
| IV                 | 16 байт (32 hex)  | ECB, CBC, CFB, OFB, CTR, ETM |
| Nonce              | 12 байт (24 hex)  | GCM                          |


```
Правильный ключ: 000102030405060708090a0b0c0d0e0f (32 символа)
Неправильно: mykey123 (8 байт)
```
```
Правильный IV: AABBCCDDEEFF00112233445566778899 (32 символа)
Неправильно: ASFSAFSA909DAS9DA99129129DNNBN
```
```
Правильный Nonce: 000102030405060708090a0b (24 символа)
```

### Команды PBKDF2 и HKDF

#### PBKDF2 (Password-Based Key Derivation Function 2):
PBKDF2 используется для безопасного выведения криптографических ключей из паролей.

- **Назначение**: Безопасное преобразование паролей в криптографические ключи
- **Стойкость к brute-force**: Большое количество итераций замедляет атаки
- **Уникальность ключей**: Использование соли гарантирует разные ключи для одинаковых паролей
- **Рекомендации по безопасности**:
    - Минимум 100,000 итераций для современных систем
    - Использование уникальной соли для каждого ключа
    - Длина ключа не менее 32 байт (256 бит)

#### Особенности реализации:
- **Алгоритм**: PBKDF2-HMAC-SHA256
- **Стандарт**: RFC 2898
- **Функция псевдослучайности**: HMAC-SHA256
- **Соль**: 16 байт (генерируется случайно если не указана)
- **Итерации**: По умолчанию 100,000 (настраивается)
- **Длина ключа**: Произвольная (по умолчанию 32 байта)

#### Формула PBKDF2:
```
DK = PBKDF2(PRF, Password, Salt, c, dkLen)
где:
  DK = derived key (выведенный ключ)
  PRF = HMAC-SHA256
  Password = пароль
  Salt = соль
  c = количество итераций
  dkLen = длина ключа в байтах

Для каждого блока i (от 1 до l, где l = ceil(dkLen / hLen)):
  U1 = PRF(Password, Salt || INT_32_BE(i))
  U2 = PRF(Password, U1)
  ...
  Uc = PRF(Password, Uc-1)
  Ti = U1 ⊕ U2 ⊕ ... ⊕ Uc

DK = T1 || T2 || ... || Tl (обрезается до dkLen байт)
```

#### HKDF (Hierarchical Key Derivation Function):
HKDF используется для детерминированного выведения множества ключей из одного мастер-ключа.

- **Назначение**: Создание множества безопасных ключей из одного мастер-ключа
- **Использование контекста**: Уникальные идентификаторы для разных применений
- **Примеры контекстов**: `"encryption"`, `"authentication"`, `"user:michan"`
- **Преимущества**:
    - Изоляция ключей: компрометация одного ключа не затрагивает другие
    - Детерминизм: одинаковые входные данные дают одинаковые ключи
    - Гибкость: произвольная длина ключей

#### Особенности реализации:
- **Основа**: HMAC-SHA256
- **Контекст**: Уникальная строка для каждого производного ключа
- **Детерминизм**: Одинаковые входные данные дают одинаковый ключ
- **Разделение**: Разные контексты дают статистически независимые ключи

#### Формула HKDF:
```
T1 = HMAC(master_key, context || INT_32_BE(1))
T2 = HMAC(master_key, context || INT_32_BE(2))
...
Tn = HMAC(master_key, context || INT_32_BE(n))

DerivedKey = T1 || T2 || ... || Tn (обрезается до нужной длины)
```


#### Базовое выведение ключа с PBKDF2:

```bash
   # Примеры использования
   
   # Базовое получение ключа с указанием соли
    crypto derive --password "MySecurePassword123!" \
    --salt a1b2c3d4e5f601234567890123456789 \
    --iterations 100000 \
    --length 32
  # Вывод: <KEY_HEX>  a1b2c3d4e5f601234567890123456789

  # Получение ключа с автоматической генерацией соли
   crypto derive --password "AnotherPassword" \
    --iterations 500000 \
    --length 16
  # Вывод: [INFO] Сгенерирована случайная соль: <SALT_HEX>
  #        <KEY_HEX>  <SALT_HEX>
  
  # Запись ключа в файл
  crypto derive --password "app_key" \
    --salt 0123456789abcdef0123456789abcdef \
    --iterations 100000 \
    --length 32 \
    --output tests/derived_key.bin
  # Вывод: [INFO] Ключ (32 байт) записан в файл: derived_key.bin
  #        <KEY_HEX>  0123456789abcdef0123456789abcdef
  
  # С минимальными итерациями (для тестирования RFC 6070 PBKDF2-HMAC-SHA256)
  crypto derive -p "password" -s 73616c74 -c 1 -l 20
  # Вывод: 120fb6cffcf8b32c43e7225256c4f837a86548c9  73616c74
```

#### Параметры команды derive (PBKDF2):
- `--password (-p)`: Пароль для выведения ключа в виде строки
- `--salt (-s)`: Соль в формате hex-строки
- `--iterations (-c)`: Количество итераций PBKDF2
- `--length (-l)`: Длина выведенного ключа в байтах
- `--algorithm (-alg)`: Алгоритм KDF
- `--output (-o)`: Выходной файл для сохранения ключа в бинарном виде

#### Формат вывода для команды derive:
* KEY_HEX SALT_HEX (оба в hex, разделены пробелом)
* Ключ: запрошенной длины в hex
* Соль: использованная соль в hex (предоставленная или сгенерированная)
* При --output: ключ сохраняется как бинарные байты, соль не записывается

#### Иерархическое выведение ключей (HKDF):

```bash
   # Используем master_key для выделения ключей из мастер-ключа
   
python3 -c "
from cryptocoreedu.kdf.hkdf import derive_key

master = b'master_secret_key_for_testing'

key1 = derive_key(master, 'encryption', 32)
key2 = derive_key(master, 'authentication', 32)
key3 = derive_key(master, 'encryption', 32)  # Same as key1
key4 = derive_key(master, 'user:michan', 64)

print(f'Encryption key:     {key1.hex()}')
print(f'Authentication key: {key2.hex()}')
print(f'Encryption key (2): {key3.hex()}')
print(f'User key: {key4.hex()}')
print(f'Deterministic: {key1 == key3}')
print(f'Different contexts produce different keys: {key1 != key2}')
"
```

### Автоматическая генерация ключей
**При шифровании без указания ключа утилита автоматически генерирует криптографически стойкий ключ:**

```bash
    # Выполняем шифрование без указания ключа в параметре
    crypto -alg aes -m ctr -enc -i tests/plain.txt -o tests/cipher.bin
    # Вывод в консоли: 
    [INFO] Сгенерирован случайный ключ: 5fae09f459b9b496cf00c3c5f1f0b613
    [INFO] Файл успешно зашифрован в режиме CFB                            
    [INFO] Входной файл: tests\plain.txt -> Выходной файл: tests\cipher.bin
    
    # или

    # Выполняем шифрование с указанием ключа в параметре
    crypto -alg aes -m ctr -enc -k 000102030405060708090a0b0c0d0e0f -i tests/plain.txt -o tests/cipher.bin
    # Вывод в консоли: 
    [INFO] Файл успешно зашифрован в режиме CTR
    [INFO] Входной файл: tests\plain.txt -> Выходной файл: tests\cipher.bin
```

**При дешифровании параметр --key (-k) все также является обязательным:**
```bash
    # Выполняем дешифрование с указанием ключа 
    crypto -alg aes -m ctr -dec -k 5fae09f459b9b496cf00c3c5f1f0b613 -i tests/cipher.bin -o tests/plain.txt
    # Вывод в консоли: 
    [WARNING] Для режима CTR IV будет извлечен из файла
    [INFO] Файл успешно расшифрован в режиме CTR
    [INFO] Входной файл: tests\cipher.bin -> Выходной файл: tests\plain.txt
```

# Тестирование

## Запуск автотестов
```shell
# Windows
python -m unittest discover -s tests/ -p 'test_*.py' -v
```
```bash
# bash
python -m unittest discover -s tests/ -p 'test_*.py' -v
```

## Тесты на интероперабильность с OPENSSL производятся в ручном порядке

### Тестирование совместимости с OpenSSL

```bash
# 1. Шифруем своим инструментом
crypto -alg aes -m cbc -enc -k 000102030405060708090a0b0c0d0e0f -i tests/plain.txt -o tests/cipher.bin

# 2. Извлекаем IV и ciphertext
dd if=tests/cipher.bin of=tests/iv.bin bs=16 count=1
dd if=tests/cipher.bin of=tests/ciphertext_only.bin bs=16 skip=1
tests/
# 3. Дешифруем с OpenSSL
openssl enc -aes-128-cbc -d -K 000102030405060708090A0B0C0D0E0F -iv $(xxd -p tests/iv.bin | tr -d '\n') -in tests/ciphertext_only.bin -out tests/decrypted.txt

# 4. Проверяем
diff -s tests/plain.txt tests/decrypted.txt

# В выводе увидим: Files tests/plain.txt and tests/decrypted.txt are identical
```

```bash
# 1. Шифруем с OpenSSL
openssl enc -aes-128-cbc -K 000102030405060708090A0B0C0D0E0F -iv AABBCCDDEEFF00112233445566778899 -in tests/plain.txt -out tests/openssl_cipher.bin

# 2. Дешифруем своим инструментом
crypto -alg aes -m cbc -dec -k 000102030405060708090a0b0c0d0e0f --iv AABBCCDDEEFF00112233445566778899 -i tests/openssl_cipher.bin -o tests/decrypted.txt

# 3. Проверяем
diff -s tests/plain.txt tests/decrypted.txt

# В выводе увидим: Files tests/plain.txt and tests/decrypted.txt are identical
```

### Команды OpenSSL для разных режимов
* #### CBC: openssl enc -aes-128-ecb

* #### CBC: openssl enc -aes-128-cbc

* #### CFB: openssl enc -aes-128-cfb

* #### OFB: openssl enc -aes-128-ofb

* #### CTR: openssl enc -aes-128-ctr


### Тестирование CSPRNG на уникальность
    
```shell
    # 1. Переходим в корень проекта (для Windows)
    cd C:/Users/user/PycharmProjects/CryptoCoreEdu/
    # 2. Запускаем тест на проверку уникальности генерации ключей и векторов инициализации
    python -m tests.test_csprng.python
    # Ожидаемый вывод: Успешно сгенерировано 1000 уникальных ключей.
``` 

```bash
    # 1. Переходим в корень проекта (для Linux/Mac/WSL)
    cd /mnt/c/Users/user/PycharmProjects/CryptoCoreEdu
    # 2. Запускаем тест на проверку уникальности генерации ключей и векторов инициализации
    python -m tests.test_csprng.python
    # Ожидаемый вывод: Успешно сгенерировано 1000 уникальных ключей.
```

### Тестирование CSPRNG с помощью NIST Statistical Test Suite

#### Пошаговая инструкция запуска тестов:

1. **Переходим в корневую папку проекта:**
    ```bash
    cd /mnt/c/Users/user/PycharmProjects/CryptoCoreEdu
    ```
2. **Переходим в папку NIST STS:**
    ```bash
    cd sts-2.1.2/sts-2.1.2/
    ```
   
3. **Собираем тесты:**

    ```bash
    make
    ```
4. **Создаем тестовые данные (10 МБ):**
    ```bash
    python3 -c "
    from cryptocoreedu.csprng import generate_random_bytes
    data = generate_random_bytes(10000000)
    open('random_test_data.bin', 'wb').write(data)
    print('Сгенерирован файл random_test_data.bin размером 10 МБ')
    "
    ```
5. **Запускаем тесты:**
    ```bash
    ./assess 10000000
    ```

6. **Вводим параметры тестирования:**

* #### Enter Choice: 0 (Input File)

* #### User Prescribed Input File: ../../random_test_data.bin

* #### Enter Choice: 1 (All statistical tests)

* #### Select Test (0 to continue): 0 (Default parameters)

* #### How many bitstreams? 10 (Для точной оценки)

* #### Select input mode: 1 (Binary mode)

7. **Ждем выполнения тестов (5-7 минут)**


8. **Просматриваем результаты:**
    ```bash
    # (Linux/Mac/WSL)
    cat experiments/AlgorithmTesting/finalAnalysisReport.txt
    ```
9. **Ожимаемый вывод:**
    ```
    Все 15 статистических тестов NIST должны быть пройдены с показателем 10/10 и p-value ≥ 0.01
    
    ------------------------------------------------------------------------------
    RESULTS FOR THE UNIFORMITY OF P-VALUES AND THE PROPORTION OF PASSING SEQUENCES
    ------------------------------------------------------------------------------
    generator is <../../random_test_data.bin>
    ------------------------------------------------------------------------------
     C1  C2  C3  C4  C5  C6  C7  C8  C9 C10  P-VALUE  PROPORTION  STATISTICAL TEST
    ------------------------------------------------------------------------------
      0   1   1   3   3   0   1   1   0   0  0.213309     10/10      Frequency
      1   0   2   2   0   1   0   0   4   0  0.066882     10/10      BlockFrequency
      0   0   3   1   1   3   1   0   1   0  0.213309     10/10      CumulativeSums
      0   2   0   0   3   3   1   0   1   0  0.122325     10/10      CumulativeSums
      0   0   1   3   1   1   0   2   0   2  0.350485     10/10      Runs
      0   0   2   2   0   2   0   4   0   0  0.035174     10/10      LongestRun
      0   0   2   1   1   1   4   0   0   1  0.122325     10/10      Rank
      1   1   0   3   0   1   1   0   3   0  0.213309     10/10      FFT
      0   0   0   0   1   1   0   1   2   5  0.008879     10/10      NonOverlappingTemplate
      0   0   2   1   0   0   1   3   0   3  0.122325     10/10      NonOverlappingTemplate
      0   1   2   0   2   1   1   0   0   3  0.350485     10/10      NonOverlappingTemplate
      .....
    ```

### Тестирование хэш-функций

#### Тестирование хэш-функций sha256 и sha3-256 на тестовых векторах

```bash
   # Тестирование sha256 (Linux/MacOS/WSL)
   ## Хэшируем пустой файл
   crypto dgst -alg sha256 -i tests/empty.txt.txt
   # Ожидаемый вывод: e3b0c44298fc1c149afbf4c899cfb92427ae41e4649b934ca495991b7852b855 tests/empty.txt.txt
   
   ## Хэшируем файл со строкой "abc"
   crypto dgst -alg sha256 -i tests/test_one.txt
   # Ожидаемый вывод: ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad  tests/test_one.txt
   
   ## Хэшируем файл со строкой "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"
   crypto dgst -alg sha256 -i tests/test_two.txt
   # Ожидаемый вывод: 248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1  tests/test_two.txt

```

```bash
   # Тестирование sha3-256 (Linux/MacOS/WSL)
   ## Хэшируем пустой файл
   crypto dgst -alg sha3-256 -i tests/empty.txt.txt
   # Ожидаемый вывод: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a tests/empty.txt.txt
   
   ## Хэшируем файл со строкой "abc"
   crypto dgst -alg sha3-256 -i tests/test_one.txt
   # Ожидаемый вывод: 3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532  tests/test_one.txt
   
   ## Хэшируем файл со строкой "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"
   crypto dgst -alg sha3-256 -i tests/test_two.txt
   # Ожидаемый вывод: 41c0dba2a9d6240849100376a8235e2c82e1b9998a999e21db32dd97496d3376  tests/test_two.txt

```

#### Тестирование хэш-функций sha256 и sha3-256 на интероперабельность

```bash
   # Тестирование sha256 (Linux/MacOS/WSL)
   # хэшируем пустой файл нашей реализацией
   crypto dgst -alg sha256 -i tests/empty.txt.txt -o tests/output_hash.txt
   # хэшируем пустой файл с помощью sha256sum
   sha256sum tests/empty.txt.txt > tests/system_hash.txt
   # проверяем идентичность
   diff -s tests/output_hash.txt tests/system_hash.txt
   #Ожидаемый вывод: Files tests/output_hash.txt and tests/system_hash.txt are identical
```

```bash
   # Тестирование sha3-256 (Linux/MacOS/WSL)
   # хэшируем пустой файл нашей реализацией
   crypto dgst -alg sha3-256 -i tests/empty.txt.txt -o tests/output_hash.txt
   # хэшируем пустой файл с помощью sha3sum
   sha3sum -a 256 tests/empty.txt.txt > tests/system_hash.txt
   # проверяем идентичность
   diff -s tests/output_hash.txt tests/system_hash.txt
   #Ожидаемый вывод: Files tests/output_hash.txt and tests/system_hash.txt are identical
```

#### Тестирование хэш-функций на файле ~1gb

```bash
   crypto dgst -alg sha256 -i tests/test1gb.txt
   # Ожидаемый вывод: d5739a8da2a57adb3b9a38495a389894227f5e083efb541b0b4473faccd55225  tests/test1gb.txt
   # Примерное время выполнение около 50-55 секунд
```

### Тестирование HMAC

#### Тесты с известными векторами RFC-4231

```bash
  # Ключ - 20 байт
  echo "Hi There" > tests/message.txt 
  crypto dgst -alg sha256 --hmac -k 0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b -i tests/message.txt
  # b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7  tests/message.txt
  
  # Ключ - 8 байт
  echo "what do ya want for nothing?" > tests/message.txt 
  crypto dgst -alg sha256 --hmac -k 4a656665 -i tests/message.txt
  # 5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843  tests/message.txt
  
  # Ключ - 20 байт
  echo -n "ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd" | xxd -r -p > tests/message.bin
  crypto dgst -alg sha256 --hmac -k aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa -i tests/message.bin
  # 773ea91e36800e46854db8ebd09181a72959098b3ef8c122d9635514ced565fe  tests/message.bin
  
  # Ключ - 25 байт
  echo -n "cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd" | xxd -r -p > tests/message.bin
  crypto dgst -alg sha256 --hmac -k 0102030405060708090a0b0c0d0e0f10111213141516171819 -i tests/message.bin
  # 82558a389a443c0ea4cc819899f2083a85f0faa3e578f8077a2e3ff46729665b  tests/message.bin
  
  # Ключ - 20 байт
  echo -n "Test With Truncation" > tests/message.txt
  crypto dgst -alg sha256 --hmac -k 0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c -i tests/message.txt
  # a3b6167473100ee06e0c796c2955552b  tests/message.txt
  
  # Ключ - 131 байт
  echo -n "Test Using Larger Than Block-Size Key - Hash Key First" > tests/message.txt
  crypto dgst -alg sha256 --hmac -k aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa -i tests/message.txt
  # 60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54  tests/message.txt
  
  # Ключ - 131 байт
  echo -n "This is a test using a larger than block-size key and a larger than block-size data. The key needs to be hashed before being used by the HMAC algorithm." > tests/message.txt
  crypto dgst -alg sha256 --hmac -k aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa -i tests/message.txt
  # 9b09ffa71b942fcb27635fbcd5b0e944bfdc63644f0713938a7f51535c3a35e2  tests/message.txt
```
#### Тест верификации 

```bash
   crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddeeff -i tests/message.txt -o tests/hmac.txt
    
   crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddeeff -i tests/message.txt -v tests/hmac.txt
   #Вывод [OK] Проверка HMAC успешна
```

#### Тест на обнаружение искажения
```bash
   # Изменение файла
   echo "original_content" > tests/message.txt
   crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddeeff -i tests/message.txt -o tests/original_hmac.txt
   echo "modified_content" > tests/message.txt
   crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddeeff -i tests/message.txt -v tests/original_hmac.txt
   #Вывод [ERROR] Проверка HMAC неверна
```
```bash
   # Изменение ключа
   echo "original_content" > tests/message.txt
   crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddeeff -i tests/message.txt -o tests/original_hmac.txt
   # используем уже другой ключ
   crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddee -i tests/message.txt -v tests/original_hmac.txt
   #Вывод [ERROR] Проверка HMAC неверна
```

#### Тест пустого и большого файла
```bash
   # Пустой файл
   crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddeeff -i tests/empty.txt
   # e8a06537f096ccf1a3c425a56cea054072c4a8db67bd28cfb02fbeaf84b35f6c tests/empty.txt
   
   # Большой файл 1 Гб
   crypto dgst -alg sha256 --hmac -k 00112233445566778899aabbccddeeff -i tests/test1gb.txt
   # 4b76d58337bb038d37c24e0ba7c47fb6b314bb1a5ad979b4ebb697a6d3571cdd  tests/test1gb.txt
```

### Тестирование GCM

#### TEST-1: NIST Test Vectors
```bash
   # NIST Test Case 1: Empty plaintext, empty AAD
   echo -n "" > tests/aead/nist_test1.txt
   
   crypto -alg aes -m gcm -enc \
       -k 00000000000000000000000000000000 \
       --aad "" \
       -i tests/aead/nist_test1.txt \
       -o tests/aead/nist_test1_cipher.bin
   
   # Размер должен быть 28 байт: 12 (nonce) + 0 (ciphertext) + 16 (tag)
   wc -c < tests/aead/nist_test1_cipher.bin
   # Ожидаемый вывод: 28
   
   # Расшифровываем и проверяем
   crypto -alg aes -m gcm -dec \
       -k 00000000000000000000000000000000 \
       --aad "" \
       -i tests/aead/nist_test1_cipher.bin \
       -o tests/aead/nist_test1_decrypted.txt
   
   diff -s tests/aead/nist_test1.txt tests/aead/nist_test1_decrypted.txt
   # Ожидаемый вывод: Files ... are identical
```
#### TEST-2: Round-trip Test
```bash
   # Создаём тестовый файл
   echo -n "The quick brown fox jumps over the lazy dog" > tests/aead/roundtrip.txt
   
   # Шифруем
   crypto -alg aes -m gcm -enc \
       -k 0123456789abcdef0123456789abcdef \
       --aad 48656c6c6f576f726c64 \
       -i tests/aead/roundtrip.txt \
       -o tests/aead/roundtrip_cipher.bin
   
   # Расшифровываем
   crypto -alg aes -m gcm -dec \
       -k 0123456789abcdef0123456789abcdef \
       --aad 48656c6c6f576f726c64 \
       -i tests/aead/roundtrip_cipher.bin \
       -o tests/aead/roundtrip_decrypted.txt
   
   # Проверяем
   diff -s tests/aead/roundtrip.txt tests/aead/roundtrip_decrypted.txt
   # Ожидаемый вывод: Files ... are identical
```
#### TEST-3: AAD Tampering Detection
```bash
   # Шифруем с правильным AAD
   echo -n "Secret message" > tests/aead/aad_test.txt
   
   crypto -alg aes -m gcm -enc \
       -k 00112233445566778899aabbccddeeff \
       --aad 636f72726563745f616164 \
       -i tests/aead/aad_test.txt \
       -o tests/aead/aad_test_cipher.bin
   
   # Пытаемся расшифровать с НЕВЕРНЫМ AAD
   crypto -alg aes -m gcm -dec \
       -k 00112233445566778899aabbccddeeff \
       --aad 77726f6e675f616164 \
       -i tests/aead/aad_test_cipher.bin \
       -o tests/aead/aad_test_fail.txt
   
   # Ожидаемый вывод:
   # [ERROR] Ошибка аутентификации
   
   # Проверяем что файл НЕ создан
   ls tests/aead/aad_test_fail.txt 2>&1
   # Ожидаемый вывод: No such file or directory
```
#### TEST-4: Ciphertext Tampering Detection
```bash
   # Шифруем
   echo -n "Message to tamper" > tests/aead/tamper_test.txt
   
   crypto -alg aes -m gcm -enc \
       -k ffeeddccbbaa99887766554433221100 \
       --aad aabbccdd \
       -i tests/aead/tamper_test.txt \
       -o tests/aead/tamper_cipher.bin
   
   # Копируем и модифицируем
   cp tests/aead/tamper_cipher.bin tests/aead/tamper_modified.bin
   
   python3 -c "data = bytearray(open('tests/aead/tamper_modified.bin', 'rb').read()); data[20] ^= 0x01; open('tests/aead/tamper_modified.bin', 'wb').write(data)"
   
   # Пытаемся расшифровать
   crypto -alg aes -m gcm -dec \
       -k ffeeddccbbaa99887766554433221100 \
       --aad aabbccdd \
       -i tests/aead/tamper_modified.bin \
       -o tests/aead/tamper_fail.txt
   
   # Ожидаемый вывод: [ERROR] Ошибка аутентификации
   
   # Файл НЕ создан
   ls tests/aead/tamper_fail.txt 2>&1
   # Ожидаемый вывод: No such file or directory
```
#### TEST-5: Nonce Uniqueness

```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from cryptocoreedu.modes.GCMMode import GCMMode
nonces = set()
key = bytes.fromhex('00112233445566778899aabbccddeeff')
for i in range(1000):
    gcm = GCMMode(key)
    nonces.add(gcm.nonce)
print(f'Unique nonces: {len(nonces)} out of 1000')
print('PASSED' if len(nonces) == 1000 else 'FAILED')
"
   # Ожидаемый вывод: 
   # Unique nonces: 1000 out of 1000
   # PASSED
```
#### TEST-6: Empty AAD
```bash
   echo -n "Message with empty AAD" > tests/aead/empty_aad.txt
   
   # Шифруем с пустым AAD
   crypto -alg aes -m gcm -enc \
       -k 11111111111111111111111111111111 \
       --aad "" \
       -i tests/aead/empty_aad.txt \
       -o tests/aead/empty_aad_cipher.bin
   
   # Расшифровываем с пустым AAD
   crypto -alg aes -m gcm -dec \
       -k 11111111111111111111111111111111 \
       --aad "" \
       -i tests/aead/empty_aad_cipher.bin \
       -o tests/aead/empty_aad_decrypted.txt
   
   diff -s tests/aead/empty_aad.txt tests/aead/empty_aad_decrypted.txt
   # Ожидаемый вывод: Files ... are identical
   
   # Без флага --aad вообще
   crypto -alg aes -m gcm -enc \
       -k 22222222222222222222222222222222 \
       -i tests/aead/empty_aad.txt \
       -o tests/aead/no_aad_cipher.bin
   
   crypto -alg aes -m gcm -dec \
       -k 22222222222222222222222222222222 \
       -i tests/aead/no_aad_cipher.bin \
       -o tests/aead/no_aad_decrypted.txt
   
   diff -s tests/aead/empty_aad.txt tests/aead/no_aad_decrypted.txt
   # Ожидаемый вывод: Files ... are identical
```
#### TEST-7: Large AAD
```bash
# Генерируем большой AAD (10KB в hex)
LARGE_AAD=$(python3 -c "import os; print(os.urandom(10240).hex())")

echo -n "Message with large AAD" > tests/aead/large_aad.txt

# Шифруем
crypto -alg aes -m gcm -enc \
    -k 33333333333333333333333333333333 \
    --aad "$LARGE_AAD" \
    -i tests/aead/large_aad.txt \
    -o tests/aead/large_aad_cipher.bin

# Расшифровываем
crypto -alg aes -m gcm -dec \
    -k 33333333333333333333333333333333 \
    --aad "$LARGE_AAD" \
    -i tests/aead/large_aad_cipher.bin \
    -o tests/aead/large_aad_decrypted.txt

diff -s tests/aead/large_aad.txt tests/aead/large_aad_decrypted.txt
# Ожидаемый вывод: Files ... are identical
```

### Тестирование ETM

#### TEST-9.1: ETM Round-trip
```bash
echo -n "ETM test message" > tests/aead/etm_plain.txt

crypto -alg aes -m etm -enc \
    -k 00112233445566778899aabbccddeeff \
    --aad 616263 \
    -i tests/aead/etm_plain.txt \
    -o tests/aead/etm_cipher.bin

crypto -alg aes -m etm -dec \
    -k 00112233445566778899aabbccddeeff \
    --aad 616263 \
    -i tests/aead/etm_cipher.bin \
    -o tests/aead/etm_decrypted.txt

diff -s tests/aead/etm_plain.txt tests/aead/etm_decrypted.txt
# Ожидаемый вывод: Files ... are identical
```
#### TEST-9.2: ETM AAD Tampering
```bash
crypto -alg aes -m etm -dec \
    -k 00112233445566778899aabbccddeeff \
    --aad 646566 \
    -i tests/aead/etm_cipher.bin \
    -o tests/aead/etm_aad_fail.txt

# Ожидаемый вывод: [ERROR] Ошибка аутентификации

ls tests/aead/etm_aad_fail.txt 2>&1
# Ожидаемый вывод: No such file or directory
```
#### TEST-9.3: ETM Ciphertext Tampering
```bash
cp tests/aead/etm_cipher.bin tests/aead/etm_tampered.bin

python3 -c "
data = bytearray(open('tests/aead/etm_tampered.bin', 'rb').read())
data[20] ^= 0x01
open('tests/aead/etm_tampered.bin', 'wb').write(data)
"

crypto -alg aes -m etm -dec \
    -k 00112233445566778899aabbccddeeff \
    --aad 616263 \
    -i tests/aead/etm_tampered.bin \
    -o tests/aead/etm_tamper_fail.txt

# Ожидаемый вывод: [ERROR] Ошибка аутентификации
ls tests/aead/etm_tamper_fail.txt 2>&1
# Ожидаемый вывод: No such file or directory
```
#### TEST-9.4: ETM Wrong Key
```bash
crypto -alg aes -m etm -dec \
    -k ffffffffffffffffffffffffffffffff \
    --aad 616263 \
    -i tests/aead/etm_cipher.bin \
    -o tests/aead/etm_wrong_key.txt

# Ожидаемый вывод: [ERROR] Ошибка аутентификации
ls tests/aead/etm_wrong_key.txt 2>&1
# Ожидаемый вывод: No such file or directory
```

### Тестирование PBKDF2 и HKDF

#### TEST-1 Known-Answer Tests
```bash
   # Тестовые векторы RFC 6070 PBKDF2-HMAC-SHA256
   
   # Test 1: 1 iteration
   crypto derive -p "password" -s 73616c74 -c 1 -l 32
   # Expected: 120fb6cffcf8b32c43e7225256c4f837a86548c92ccc35480805987cb70be17b
   
   # Test 2: 2 iterations  
   crypto derive -p "password" -s 73616c74 -c 2 -l 32
   # Expected: ae4d0c95af6b46d32d0adff928f06dd02a303f8ef3c251dfd6e2d85a95474c43
   
   # Test 3: 4096 iterations
   crypto derive -p "password" -s 73616c74 -c 4096 -l 32
   # Expected: c5e478d59288c841aa530db6845c4c8d962893a001ce4e11a4963873aa98134a
   
   # Test 4: 16777216 iterations
   crypto derive -p "password" -s 73616c74 -c 16777216 -l 32
   # Expected: cf81c66fe8cfc04d1f31ecb65dab4089f7f179e89b3b0bcb17ad10e3ac6eba46
   
   # Test 5:
   crypto derive -p "passwordPASSWORDpassword" -s 73616C7453414C5473616C7453414C5473616C7453414C5473616C7453414C5473616C74 -c 4096 -l 40
   # Expected: 348c89dbcbd32b2f32d814b8116e84cf2b17347ebc1800181c4e2a1fb8dd53e1c635518c7dac47e9
```
#### TEST-2 Iteration Test
```bash
   crypto derive -p "test_password" -s aabbccdd -c 1000 -l 32
   crypto derive -p "test_password" -s aabbccdd -c 1000 -l 32
   # Both should produce identical output
```
#### TEST-3 Length Test
```bash
   crypto derive -p "password" -s 73616c74 -c 100 -l 1
   # Expected: 07
   crypto derive -p "password" -s 73616c74 -c 100 -l 16
   # Expected: 07e6997180cf7f12904f04100d405d34
   crypto derive -p "password" -s 73616c74 -c 100 -l 32
   # Expected: 07e6997180cf7f12904f04100d405d34888fdf62af6d506a0ecc23b196fe99d8
   crypto derive -p "password" -s 73616c74 -c 100 -l 64
   # Expected: 07e6997180cf7f12904f04100d405d34888fdf62af6d506a0ecc23b196fe99d8675294ec5aa7944b6a86c51fd97051bbefad5239c8fe47db259c296e98569a86
   crypto derive -p "password" -s 73616c74 -c 100 -l 100
   # Expected: 07e6997180cf7f12904f04100d405d34888fdf62af6d506a0ecc23b196fe99d8675294ec5aa7944b6a86c51fd97051bbefad5239c8fe47db259c296e98569a86dbd0101cb6ce6a25b4155bccbcb77b2719de3a76f0487e73373c1daa79a53ca6afcda549
```
#### TEST-4 Interoperability Test
```bash
   openssl kdf -keylen 32 -kdfopt digest:SHA256 -kdfopt pass:test -kdfopt hexsalt:1234567890abcdef -kdfopt iter:1000 PBKDF2
   # Expected: 4C:D8:B5:C4:6A:EE:47:F0:D4:A6:A0:DD:7C:20:5B:1D:30:B5:4D:25:03:C1:3F:E7:42:2E:95:EA:31:2B:74:25
   crypto derive -p "test" -s 1234567890abcdef -c 1000 -l 32
   # Expected: 4cd8b5c46aee47f0d4a6a0dd7c205b1d30b54d2503c13fe7422e95ea312b7425  1234567890abcdef
```
#### TEST-5 Key Hierarchy Test
```bash
      
python3 -c "
from cryptocoreedu.kdf.hkdf import derive_key

master = b'master_secret_key_for_testing'

# вводим одинаковые параметры
key1 = derive_key(master, 'encryption', 32)
key2 = derive_key(master, 'encryption', 32)
key3 = derive_key(master, 'encryption', 32)
key4 = derive_key(master, 'encryption', 32)

print(key1.hex())
print(key2.hex())
print(key3.hex())
print(key4.hex())
"

# Все ключи должны быть одинаковы
```
#### TEST-6 Context Separation Test
```bash
python3 -c "
from cryptocoreedu.kdf.hkdf import derive_key

master = b'master_secret_key_for_testing'

key1 = derive_key(master, 'encryption', 32)
key2 = derive_key(master, 'authentication', 32)
key3 = derive_key(master, 'storage', 32)
key4 = derive_key(master, 'user:michan', 64)

print(f'Encryption key:     {key1.hex()}')
print(f'Authentication key: {key2.hex()}')
print(f'Stotage key: {key3.hex()}')
print(f'User key: {key4.hex()}')
"
```
#### TEST-7 Salt Randomness Test
```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from cryptocoreedu.csprng import generate_random_bytes

salts = set(generate_random_bytes(16).hex() for _ in range(1000))
print(f'Unique salts: {len(salts)} out of 1000')
print('PASSED' if len(salts) == 1000 else 'FAILED')
"
```
## Структура проекта

```
CryptoCoreEdu/
├── cryptocoreedu/         # Исходный код
│   ├── main.py            # Точка входа
│   └── hash/
│       ├──sha3-256.py     # Хэш-функция sha3-256
│       └──sha256.py       # Хэш-функция sha256
│   └── mac/
│       └──hmac.py     # HMAC функция
│   └── kdf/
│       ├──pbkdf2.py   # PBKDF2 реализация
│       └──hkdf.py     # HKDF реализация
│   └── utils/
│       ├── padding.py     # Реализация паддинга по стандрату PKCS7
│       └── validators.py  # Валидаторы для ключей, IV и файлов
│   └── modes/             # Реализации режимов шифрования
│       ├── ECBMode.py        # Режим ECB
│       ├── CBCMode.py        # Режим CBC
│       ├── CFBMode.py        # Режим CFB
│       ├── OFBMode.py        # Режим OFB
│       ├── GCMMode.py        # Режим GCM
│       ├── ETMMode.py        # Режим ETM
│       └── CTRMode.py        # Режим CTR
│   ├── cli_parser.py     # Парсинг аргументов
│   ├── csprng.py         # КСГПСЧ
│   ├── file_io.py        # Работа с файлами и IV
│   ├── exceptions.py     # Кастомные исключения для ошибок
│   └── main.py           # Точка входа в приложение
├── sts-2.1.2/            # Папка с тестами NIST (STS)
├── tests/                # Тесты
│   ├── aead/             # Папка с файлами .txt/.bin
│   ├── unit/             # Папка с unit-тестами
│   ├── integration/      # Папка с интеграционными тестами
│   ├── test_openssl.py   # Файл тестов на интероперабельность
│   ├── plain.txt         # Файл plaintext'а
├── setup.py              # Файл сборки проекта
├── pyproject.toml        # Файл сборки
└── README.md             # Документация
```

## Требования

### Зависимости
- **Python** 3.8 или выше
- **pycryptodome** 3.23.0 или выше
- **OpenSSL** (для тестирования совместимости)
- **numba** 0.62.1 или выше (для оптимизации вычислений хэш-функций)
- **numpy** 2.2.6 или выше (для оптимизации вычислений хэш-функций)

## Проверка целостности

Для проверки корректности работы утилиты:

```bash
diff -s tests/plain.txt tests/decrypted.txt
# Вывод при успешной работе утилиты: Files tests/plain.txt and tests/decrypted.txt are identical
```

### Коды ошибок
* 101: Ошибка валидации ключа

* 102: Ошибка валидации IV

* 103: Проблема с входным файлом

* 104: Проблема с выходным файлом

* 105: Входной и выходной файлы одинаковые

* 106: Неподдерживаемый режим

* 107: Ошибка инициализации режима шифрования

* 108: Ошибка выполнения операции

* 109: Неизвестная ошибка операции

* 110: Критическая ошибка

* 111: Ошибка отсутствия ключа как обязательного параметра

* 112: Ошибка КСГПСЧ

* 113: Ошибка алгоритма хэширования

* 114: Ошибка операции хэширования

* 115: Ошибка аргументов

* 116: Ошибка отсутствия ключа как обязательного параметра

* 117: Ошибка ключа

* 118: Не удачная верификация HMAC

* 119: Ошибка верификации HMAC

* 120: Ошибка валидации AAD

* 121: Ошибка аутентификации AEAD

* 122: Ошибка валидации nonce

* 123: Ошибка kdf

* 124: Ошибка валидация соли

* 125: Ошибка обязательного пароля

* 126: Ошибка неправильности итераций

* 127: Ошибка длины

## Важные заметки

- Проект разработан для **образовательных целей**
- Режим ECB не рекомендуется для защиты реальных данных
- Никогда не используйте один nonce дважды с одним ключом в GCM!
- При ошибке аутентификации AEAD выходной файл не создаётся
- Сохраняйте ключи в безопасном месте
- Для генерации криктостойких ключей и IV используется системный источник энтропии (os.urandom()); гарантирует уникальность и непредсказуемость генерируемых значений
- Скорость хэш-функций может быть гораздо ниже, чем в проверенных реализациях (hashlib, sha256sum и т.д.)

---

*Разработано для демонстрации принципов криптографии. Не используйте для защиты конфиденциальных данных.*