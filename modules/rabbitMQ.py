import pika
import configparser
import json
from modules.document_type import get_id

config = configparser.ConfigParser()
config.read("settings.ini")
url = config["rabbit"]["url"]
queue_from = config["rabbit"]["queue_from"]
queue_to = config["rabbit"]["queue_to"]
parameters = pika.URLParameters(url)


def send_status(documentId, stateId, mlProcessingId, document_type, processed=0, total=0, json_normal=[],):
    connection = pika.BlockingConnection(parameters)
    properties = pika.BasicProperties(headers={"type": "UpdateTask", "from": "ML", "to": "Backend"},
                                      delivery_mode=pika.DeliveryMode.Persistent)
    channel = connection.channel()
    if document_type == "ГОСТ-Р" or document_type == "ГОСТР":
        document_type = "ГОСТ Р"
    # pageNumber	integer
    # positionY	integer
    channel.basic_publish(exchange='', routing_key=queue_to,
                          body=json.dumps({
                              "documentId": documentId,
                              "typeId": get_id(document_type),
                              "stateId": stateId,
                              "processed": processed,
                              "total": total,
                              "json": json_normal,
                              "mlProcessingId": mlProcessingId
                          }, indent=2).encode('utf-8'),
                          properties=properties)
    channel.close()
    connection.close()
    print(f"Отправил send_status {documentId}:{stateId}")
