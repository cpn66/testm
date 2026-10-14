from modules.connect_api import API

api = API()


def get_id(document_type):
    document_types = api.get_document_types()
    for type_doc in document_types:
        if type_doc["name"] == document_type:
            return type_doc["id"]
    return 13


def get_template(document_type):
    document_types = api.get_document_types()
    for type_doc in document_types:
        if type_doc["name"] == document_type:
            return type_doc["templateLink"]
    return "/settings/default.json"


def get_type(document_type_id):
    document_types = api.get_document_types()
    for type_doc in document_types:
        if type_doc["id"] == document_type_id:
            return type_doc["name"]
    return "Не определен"
