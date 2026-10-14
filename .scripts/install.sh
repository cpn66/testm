#!/bin/bash

apt-get update
apt-get install -y poppler-utils tesseract-ocr python3.11-venv libgl1-mesa-glx
# Enchant and dictionares installation..
apt-get install -y gcc g++
apt-get install -y python3-enchant
apt install -y myspell-ru

python3 -m venv venv
source venv/bin/activate

pip install -U Flask
pip install threaded
pip install easyocr
pip install pdf2image
pip install pytesseract
pip install pillow
pip install translate
pip install waitress

pip install requests
pip install pyicu
pip install pycld2
pip install pyenchant
pip install pandas
pip install cnstd[ort-cpu]
pip install pix2text
pip install onnxruntime
pip install antlr4-python3-runtime==4.11
