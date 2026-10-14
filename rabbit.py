import pika
import configparser
from modules.document_type import get_type
import json
from easy import start_ocr
import time
import os
from natsort import natsorted

config = configparser.ConfigParser()
config.read("settings.ini")
url = config["rabbit"]["url"]
queue_from = config["rabbit"]["queue_from"]
queue_to = config["rabbit"]["queue_to"]
server_dir_files = config["files"]["dir"]
source = config["files"]["source"]
graphics = config["files"]["graphics"]
parameters = pika.URLParameters(url)


def start():
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    # cnt = channel.queue_declare(queue=queue_from, passive=True).method.message_count
    # print(f"Количество файлов в очереди {cnt}")
    method_frame, properties, body = channel.basic_get(queue_from)
    if body:
        data = json.loads(body.decode('utf-8'))
        if (properties.headers["type"] == "CreateTask" and properties.headers["from"] == "Backend"
                and properties.headers["to"] == "ML"):
            channel.basic_ack(method_frame.delivery_tag)
            channel.close()
            connection.close()
            print(f"Получил файл в обработку {data['documentId']}")
            dir_files = f"{server_dir_files}/{data['documentId']}{source}"
            open_dir(dir_files)
            files = os.listdir(dir_files)
            files = natsorted(files)
            start_ocr(
                [f"{dir_files}/{file}" for file in files],
                data["documentId"],
                data['mlProcessingId'],
                {"name": get_type(data['typeId'])},
                data['setting']
            )
        else:
            channel.basic_ack(method_frame.delivery_tag)
            channel.close()
            connection.close()
    else:
        channel.close()
        connection.close()


def open_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def start_server():
    try:
        while True:
            start()
            time.sleep(5)
    except Exception as ex:
        print("ERROR start_server:", ex)
        start_server()


if __name__ == '__main__':
    print("Сервер запущен")
