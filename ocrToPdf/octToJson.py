import configparser
from modules.rabbitMQ import send_status
from ocrToPdf.normalizeJson import normalize
import os
import traceback
config = configparser.ConfigParser()
config.read("settings.ini")
server_dir_files = config["files"]["dir"]
source = config["files"]["source"]
graphics = config["files"]["graphics"]


def send_json(array, document_id, status, mlProcessingId, document_type):
    try:
        print("normalize")
        json_normal = normalize(array)
        print("send_status")
        send_status(document_id, status, mlProcessingId, document_type, 0, 0, json_normal)
    except Exception as ex:
        print("ERROR send_json:", ex)
        print(traceback.format_exc())
        send_status(document_id, 500, mlProcessingId, document_type, 0, 0)
        return None


def open_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def save_img(image, document_id):
    dir_img = f"{server_dir_files}/{document_id}{graphics}/"
    open_dir(dir_img)
    with open(dir_img + image[0] + ".png", "wb") as f:
        f.write(image[1].getbuffer())
