# Установка

Для работы на CPU необходимо включать вложенную виртуализацию (nested virtualization) на виртуальной машине.
 

## Установка пакетов в систему

### Linux

    sudo apt install poppler-utils
    sudo apt install tesseract-ocr -y
    sudo apt-get install python3-enchant
    apt install -y myspell-ru

### Windows
Установить 
[tesseract-ocr](https://tesseract-ocr.github.io/tessdoc/Downloads.html),
[poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)
и прописать переменные среды в Path

PyTorch для Windows с GPU
    
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

PyTorch для Windows без GPU

    pip3 install torch torchvision torchaudio

## Установка модуля распознавания русского языка

После установки tesseract-ocr нужно загрузить языковую модель из папки или по ссылке [rus.traineddata](https://github.com/tesseract-ocr/tessdata/blob/main/rus.traineddata)

    /lib/rus.traineddata

В дирректорию tesseract-ocr

* для debian 11: /usr/share/tesseract-ocr/4.00/tessdata/

## Установка пакетов python

    pip install -U Flask
    pip install threaded
    pip install easyocr
    pip install pdf2image
    pip install pytesseract
    pip install pillow
    pip install translate
    pip install waitress
    pip install pyenchant
    pip install pandas
    pip install cnstd
    pip install pycld2
    pip install pika
    pip install retry
    pip install pix2tex
    pip install latex2mathml
    pip install onnxruntime
    pip install natsort
    pip install 'tensorflow==2.15.0'
    pip install pymorphy3
    pip install python-Levenshtein


## Запуск проекта

Скопировать файл example_settings.ini с именем settings.ini
Заполнить поля:

    url_server - URL до backend с префиксом
    cpu - Указать количество потоков
    url - URL rabbitMQ
    dir - Путь до серверного хранилища документов

Скопировать файл lib/math/ocr/example_mixed.yaml в lib/math/ocr/mixed.yaml
Заполнить строку:

    tokenizer: ...  - путь до файла tok_v2.json

Запуск проекта    

    pm2 start main.py

## Проверка работы проэкта

Выполнить запрос

    http://host:port/test

Если ответ:
- "Документ отправлен" все работает
- "Ошибка отправки документа" не верно указана ссылка в settings.ini
