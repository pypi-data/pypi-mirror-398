# Сборочный файл проекта

from setuptools import setup, find_packages

setup(
    name="cryptocoreedu",
    version="2.0.0", # ОБНОВЛЕНИЕ ВЕРСИИ ПРИ КАЖДОМ ВЫПУСКЕ
    packages=find_packages(),
    description="Educational cryptography toolkit",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="michaans",
    keywords=["cryptography", "educational", "aes", "ecb"],
    # Зависимости проекта (библиотеки, которые нужны для работы)
    install_requires=[
        'pycryptodome>=3.23.0',  # Ваша основная зависимость
    ],
    python_requires='>=3.8',
    # entry_points - это "магия", которая делает из вашего кода CLI-утилиту
    entry_points={
        'console_scripts': [
            'crypto=cryptocoreedu.main:main',  # Формат: 'имя_команды=путь.к.модулю:функция'
        ],
    },

)