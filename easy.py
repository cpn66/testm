from pdf2image import convert_from_path
from PIL import Image
import time
from modules.paginate.paginate import Paginate
if __name__ != "__main__":
    from ocrToPdf.octToJson import save_img
    from modules.rabbitMQ import send_status
import os
import re
from modules.ocr import OCR


ocr = OCR(True)
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'


def get_page_dpi(page_shape):
    page_inch_shape = [8.27, 11.69]  # a4 size
    dpi = max(page_shape) / max(page_inch_shape)
    return int(dpi)


def convert_pdt_to_img(pdf_name: str, image_path: str, dpi):
    try:
        return convert_from_path(pdf_name, fmt="jpg", dpi=dpi)
    except Exception as ex:
        print("ERROR convert_pdt_to_img:", ex)
        return []


def find_document_type(pages):
    document_types = dict()
    document_type = ""
    max_count = 0
    for page in pages:
        for block in page:
            if block[2] == "text":
                match = re.search(r'([А-Я ]+)\s([\d\.]+)[\s\-\—\.]+(\d{2}|\d{4})[^\d]', block[1])
                if match and match.groups()[0]:
                    type = f"{match.groups()[0]} {match.groups()[1]} {match.groups()[2]}"
                    if type in document_types:
                        document_types[type]["count"] += 1
                    else:
                        document_types[type] = {
                            "name": match.groups()[0].strip(),
                            "number": match.groups()[1].strip(),
                            "year": match.groups()[2].strip(),
                            "count": 1
                        }
                    if document_types[type]["count"] > max_count:
                        max_count = document_types[type]["count"]
                        document_type = document_types[type]
    return document_type


def start_ocr(files_path, document_id, mlProcessingId, document_type, setting, send=True):
    result = list()
    pages_size = list()
    images = []
    pages = list()
    for file_path in files_path:
        type_file = file_path.split(".")[-1].lower()
        if type_file == "pdf":
            pages.extend(convert_pdt_to_img(file_path, "", setting["dpiCompression"]))
        elif type_file == "jpg" or type_file == "png" or type_file == "jpeg" or type_file == "bmp" or type_file == "gif":
            pages.append(Image.open(file_path).convert('RGB'))
    if len(pages):
        start_file_time = time.time()
        for index, page in enumerate(pages):
            start_time = time.time()
            # if index == 9:
            dpi_page = get_page_dpi(page.size)
            res, files = ocr.img_to_text(page, index, document_id, mlProcessingId, document_type, dpi_page <= setting["dpiAutocorrection"])
            for img in files:
                images.append(img)
            # print(res)
            result.append(res)
            pages_size.append(page.size)
            end_time = time.time()
            if send:
                send_status(document_id, 102, mlProcessingId, document_type['name'], int(index)+1, len(pages))
            print("Распознал страницу - ", index, end_time - start_time)
        ocr.del_streams(mlProcessingId)
        document_type_new = find_document_type(result)
        if not document_type['name'] or document_type['name'] != "Не определен":
            document_type_new['name'] = document_type['name']
        document_type = document_type_new
        end_file_time = time.time()
        print(f"Распознал Весь файл({document_type['name']})", end_file_time - start_file_time)
    try:
        if send and len(images) > 0:
            for img in images:
                save_img(img, document_id)
        else:
            for img in images:
                print(img)
    except Exception as ex:
        print("ERROR send_img:", ex)
        if send:
            send_status(document_id, 500, mlProcessingId, document_type["name"], int(index)+1, len(pages))
        return None
    try:
        print("text_to_page", document_type)
        paginate = Paginate()
        paginate.text_to_page(result, document_id, send, mlProcessingId, document_type, pages_size)
    except Exception as ex:
        print("ERROR text_to_page:", ex)
        if send:
            send_status(document_id, 500, mlProcessingId, document_type["name"], int(index)+1, len(pages))
        return None


if __name__ == '__main__':
    server_dir_files = "files"
    source = "/source"
    dir_files = f"{server_dir_files}/1{source}"
    start_ocr([f"{dir_files}/{file}" for file in os.listdir(dir_files)], 21, 1,
              {"name": "Не определен"},
              {"dpiCompression": 150, "dpiAutocorrection": 60},
              False)
