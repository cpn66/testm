import requests
import configparser
import json
import time

config = configparser.ConfigParser()
if __name__ == "__main__":
    config.read("../settings.ini")
else:
    config.read("settings.ini")

class API:
    def __init__(self, dir=None):
        if dir:
            config.read(dir)
        self.token = None
        self.document_types = None
        self.headers = None
        self.document_types = None
        self.auth()

    def auth(self):
        while not self.get_token():
            print(
                f"Ошибка авторизации: {config['backend']['url_server']}, login:{config['backend']['login']}, password:{config['backend']['password']}")

    def get_token(self):
        document = requests.post(config["backend"]["url_server"] + "login",
                                 json={"login": config["backend"]["login"], "password": config["backend"]["password"]})
        req = json.loads(document.text)
        if not req["error"]:
            self.token = req["result"]["token"]
            self.headers = {'X-Auth-Token': req["result"]["token"]}
            return True
        time.sleep(0.1)
        return False

    def get_document_types(self):
        if self.document_types:
            return self.document_types
        document = requests.get(config["backend"]["url_server"] + "documentTypes", headers=self.headers)
        res = json.loads(document.text)
        if not res["error"]:
            self.document_types = res["result"]
            return res["result"]
        else:
            print("Ошибка API:get_document_types")
            self.auth()
            return self.get_document_types()

    def crate_tag(self, name):
        document = requests.post(config["backend"]["url_server"] + "tags", json={"name": name}, headers=self.headers)
        res = json.loads(document.text)
        if not (res['error']) or res['message'] == "Такой тег уже уже существует.":
            print("Создал тег", name)
            return True
        else:
            print("Ошибка API:crate_tag")
            self.auth()
            return self.crate_tag(name)

    def get_tags(self):
        document = requests.get(config["backend"]["url_server"] + "tags", headers=self.headers)
        res = json.loads(document.text)
        if not (res['error']):
            return res['result']
        else:
            print("Ошибка API:get_tags")
            self.auth()
            return self.get_tags()

    def crate_parameter(self, name):
        document = requests.post(config["backend"]["url_server"] + "parameters", json={"name": name}, headers=self.headers)
        res = json.loads(document.text)
        if not (res['error']) or res['message'] == "Параметр с таким названием уже существует.":
            print("Создал параметр", name)
            return True
        else:
            print("Ошибка API:crate_parameter")
            self.auth()
            return self.crate_parameter(name)

    def get_parameters(self):
        document = requests.get(config["backend"]["url_server"] + "parameters", headers=self.headers)
        res = json.loads(document.text)
        if not (res['error']):
            return res['result']
        else:
            print(res)
            print("Ошибка API:get_parameter")
            self.auth()
            return self.get_parameters()


if __name__ == "__main__":
    api = API()
    print(api.crate_parameter("Метаданные"))
    print(api.get_parameters())
    print(api.get_parameters())
    print(api.get_parameters())
    print(api.get_parameters())
