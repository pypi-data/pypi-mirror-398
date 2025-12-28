from setuptools import setup, find_packages

setup(
    name="laba44",                     # имя библиотеки
    version="0.1.0",                    # версия
    packages=find_packages(),           # автоматически ищет все папки с __init__.py
    install_requires=[],                # зависимости, если есть
    python_requires=">=3.8",            # минимальная версия Python
    description="Учебная Python-библиотека для лабораторной работы №44",
    author="Your Name",                 # сюда можно написать своё имя
    url="https://github.com/yourusername/laba44",  # если нет — можно оставить пустым
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
