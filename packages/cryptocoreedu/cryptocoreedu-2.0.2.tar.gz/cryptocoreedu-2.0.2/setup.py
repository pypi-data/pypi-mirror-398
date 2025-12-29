# Сборочный файл проекта

from setuptools import setup, find_packages

setup(
    name="cryptocoreedu",
    version="2.0.2",  # ОБНОВЛЕНИЕ ВЕРСИИ ПРИ КАЖДОМ ВЫПУСКЕ
    packages=find_packages(exclude=["tests", "tests.*"]),
    description="Educational cryptography toolkit with AES, SHA-256, SHA3-256, HMAC, PBKDF2",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="michaans",
    url="https://github.com/michaans/CryptoCoreEdu",  # Замени на свой URL
    license="MIT",
    keywords=[
        "cryptography",
        "educational",
        "aes",
        "sha256",
        "sha3",
        "hmac",
        "pbkdf2",
        "encryption",
        "hashing",
    ],

    # Зависимости проекта
    install_requires=[
        "numpy>=1.21.0",
        "numba>=0.56.0",
        "pycryptodome>=3.15.0",
    ],

    # Опциональные зависимости для разработки
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },

    python_requires=">=3.10",

    # CLI entry point
    entry_points={
        "console_scripts": [
            "crypto=cryptocoreedu.main:main",
        ],
    },

    # Классификаторы для PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security :: Cryptography",
        "Topic :: Education",
    ],
)



