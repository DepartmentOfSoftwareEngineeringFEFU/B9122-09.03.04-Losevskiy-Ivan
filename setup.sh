```bash
#!/bin/bash

set -e

echo "==========================================="
echo "Установка необходимых компонентов"
echo "==========================================="

sudo apt update

sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    ffmpeg

echo
echo "==========================================="
echo "Создание виртуального окружения"
echo "==========================================="

python3 -m venv .venv

source .venv/bin/activate

echo
echo "==========================================="
echo "Установка зависимостей Python"
echo "==========================================="

pip install --upgrade pip
pip install -r requirements.txt

echo
echo "==========================================="
echo "Проверка установки FFmpeg"
echo "==========================================="

ffmpeg -version
ffprobe -version

echo
echo "==========================================="
echo "Установка завершена!"
echo
echo "Для запуска программы выполните:"
echo
echo "source .venv/bin/activate"
echo "python3 main.py"
echo "==========================================="
```
