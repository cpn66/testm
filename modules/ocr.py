import re
import easyocr
import pytesseract
from io import BytesIO
from modules.streams import Streams
import configparser
from modules.math_detector import MathDetector
from modules.formulas import correct_text, insert_formula_into_text
import os
import sys
import numpy as np
from modules.enchant_spell import EnchantSpell
from modules.table_detection.table_detector import TableDetector
from modules.image_detector import ImageDetector
import modules.ocr_tables as ocr_tables
from modules.default import transliterate
from PIL import Image
import cv2
from modules.rabbitMQ import send_status

root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_path)
sys.path.append(os.getcwd())
config = configparser.ConfigParser()
config.read("settings.ini")
GPU = True
settings_dir = (config['files']['dir'] + config['files']['settings']).replace("\\", "/")
if config['backend']['gpu'] == "0":
    GPU = False
reader = easyocr.Reader(['ru', 'en'], gpu=GPU)

streams = Streams(int(config["streams"]["cpu"]))

speller = EnchantSpell()
table_detector = TableDetector()
image_detector = ImageDetector()
detector = MathDetector(GPU)


def tesseract_image_to_string(box, pil_img, result, index, use_of_dictionaries=False):
    im_crop = pil_img.crop((box[0][0], box[0][1], box[2][0], box[2][1]))
    tess_result = pytesseract.image_to_string(im_crop, lang="rus+eng",
                                              config=f'--psm 3 --oem 1 --tessdata-dir "{settings_dir}"')
    if use_of_dictionaries:
        text_no_words_breaks = tess_result.replace("-\n", '')
        text_lines = text_no_words_breaks.split('\n')

        corrected__text = correct_text(text_lines, speller)
        merjed = "\n".join(corrected__text)
    else:
        merjed = tess_result
    result[index][1] = merjed
    return True


def tesseract_image_to_string_formula(box, pil_img, result, index, math_insertions, use_of_dictionaries=False,
                                      lang="rus+eng"):
    im_crop = pil_img.crop((box[0][0], box[0][1], box[2][0], box[2][1]))
    # im_crop.save("crop%d.png"%index)
    config = f'tsv --psm 1 --tessdata-dir "{settings_dir}"'
    tess_result = pytesseract.image_to_data(im_crop, lang=lang, config=config,
                                            output_type=pytesseract.Output.DICT)
    if use_of_dictionaries:
        merged_text = insert_formula_into_text(tess_result, math_insertions, box)
        text_no_words_breaks = merged_text.replace("-\n", '')
        text_lines = text_no_words_breaks.split('\n')

        corrected__text = correct_text(text_lines, speller)
        merjed = "\n".join(corrected__text)
    else:
        merjed = insert_formula_into_text(tess_result, math_insertions, box)
    result[index][1] = merjed
    return True


def find_box_image(result, block_image, img_rgb):
    size = img_rgb.size
    top_line = 10
    bottom_line = block_image[0][0][1] - 1
    image_name = re.findall(r'(?:^|\s)(Рисунок|Чертеж|Черт\.)\s(\d+|[А-Я]+[.,]\d*)(?:\s|$)', block_image[1])
    image_name = image_name[0][0] + image_name[0][1]
    image_name = transliterate(image_name)
    # block_image[1] = re.sub(r'(^[Рр]исунок[^А-Яа-я]|^[Чч]ертеж[^А-Яа-я]|^[Чч]ерт.[^А-Яа-я])(\d*)', '',
    #                         block_image[1])
    array_result = list()
    byte_io = BytesIO()
    for block in reversed(result):
        if (block[2] == "image") or (block[2] == "text" and block[0][2][1] < bottom_line - 100 and (
                (block[0][1][0] - block[0][0][0]) > (size[0] * 0.5) or block[0][1][1] < result[0][0][2][1] or re.search(
            r'(?:^|\s)(Рисунок|Чертеж|Черт\.)\s(\d+|[А-Я]+[.,]\d*)(?:\s|$)', block[1]))):
            top_line = block[0][2][1] + 1
            break

    crate_img = False
    for block in result:
        if top_line > block[0][0][1]:
            array_result.append(block)
        else:
            if not crate_img and bottom_line - top_line > 0:
                crate_img = True
                img = img_rgb.crop((0, top_line, size[0], bottom_line))
                size = img.size
                # img.show()
                img.save(byte_io, 'png')
                byte_io.seek(0)
                array_result.append([[[0, top_line], [size[0], top_line], [size[0], bottom_line], [0, bottom_line]],
                                     f"img[name='{image_name}.png']", "image"])
                # print(block_image)
                # array_result.append(block_image)
            if bottom_line < block[0][0][1]:
                array_result.append(block)

    return array_result, byte_io, image_name


def get_image(block_image, img_rgb, index, page):
    img = img_rgb.crop((block_image[0][0], block_image[0][1], block_image[1][0], block_image[1][1]))
    byte_io = BytesIO()
    # img.show()
    img.save(byte_io, 'png')
    byte_io.seek(0)
    return [[[block_image[0][0], block_image[0][1]], [block_image[1][0], block_image[0][1]],
             [block_image[1][0], block_image[1][1]], [block_image[0][0], block_image[1][1]]],
            f"img[name='image-{page}-{index}.png']", "image"], byte_io, f'image-{page}-{index}'


def find_box_formulas(pil_img, page_index, remove_from_page):
    byte_io = BytesIO()
    images = []
    array_result = list()
    f_insertions = list()
    img = pil_img.copy()
    img, formulas, _, f_insertions = detector.find_math(img, page_index, remove_from_page)
    # add_insertions, img = detector.find_insertion_with_tesseract(img) # Try to find all units and chemical formulas
    # f_insertions = detector.filter_overlapped_insertions(f_insertions, add_insertions)
    # img = detector.rem_ins(f_insertions, img)

    for idx, formula in enumerate(formulas):
        images.append(formula[1])
        array_result.append([formula[0],
                             f"img[name='formula-{page_index}-{idx}.png']", False])
    return img, array_result, images, f_insertions


def convert_from_cv2_to_image(img: np.ndarray) -> Image:
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def convert_from_image_to_cv2(img: Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def getLanguageOCR(index):
    if index == 0:
        return "rus"
    return "rus+eng"


class OCR:

    def __init__(self, tesseract):
        self.tesseract = tesseract

    def img_to_text(self, pil_img, page_index, document_id, mlProcessingId, document_type, use_of_dictionaries=False,
                    recognize_each_table_cell=True):
        try:
            images = []
            formulas = []
            page_table_struct = []
            f_insertions = []
            final_images_bboxes = list()
            cv_img_without_tables = np.array(pil_img)
            image = pil_img

            # Поиск на странице таблиц и распознавание их структуры
            if page_index != 0:
                # page_layout, _ = detector.get_text_layout(pil_img, page_index)

                cv_img = np.array(pil_img)
                page_table_struct = table_detector.find_table(cv_img)
                cv_img_without_tables, page_table_struct = table_detector.remove_tables_from_page(cv_img_without_tables,
                                                                                                  page_table_struct)
                if recognize_each_table_cell:
                    page_table_struct = ocr_tables.cells_to_text_data(page_table_struct)
                else:
                    page_table_struct = ocr_tables.tables_to_text_data(page_table_struct)
                page_table_struct = list(filter(lambda x: "cells" in x, page_table_struct))
                for table in page_table_struct:
                    table["page_add"] = False
                print("Tables on page: ", len(page_table_struct))
                image = convert_from_cv2_to_image(cv_img_without_tables)
                # _, Большие формулы, __, внутритекстовые формулы
                image, formulas, files, f_insertions = find_box_formulas(image, page_index, True)
                cv_img_without_tables = convert_from_image_to_cv2(image)
                for index, img in enumerate(files):
                    images.append((f"formula-{page_index}-{index}", img, 'multipart/form-data'))
                # rm_ins = []
                # for item in page_layout:
                #     if item['type'] in ['Reference', 'Table', "Figure", 'Title', 'Figure caption']:
                #         for insertion in f_insertions:
                #             # print(item)
                #             res = detector.check_overlap(item, insertion)
                #             if res:
                #                 rm_ins.append(insertion)
                # try:
                #     for r in rm_ins:
                #         f_insertions.remove(r)
                # except:
                #     print("Error with removing  overlapped page items.")

                # Определение изображения с помощью pix2text
                images_bboxes = image_detector.find_images(pil_img)
                for img in images_bboxes:
                    flag = True
                    for table in page_table_struct:
                        if (img[1][1] >= table["bbox"][1] >= img[0][1] or img[1][1] >= table["bbox"][3] >= img[0][1] or
                                (table["bbox"][3] >= img[1][1] and img[0][1] >= table["bbox"][1])):
                            flag = False
                            break
                    if flag:
                        img.append(False)
                        final_images_bboxes.append(img)
                # page_without_imgs, page_images = image_detector.remove_images_from_page(cv_img, final_images_bboxes)
                # for img in page_images:
                #      img2 = convert_from_cv2_to_image(img)
                #      img2.show()
                # image = convert_from_cv2_to_image(page_without_imgs)
                # image.show()

            # Определение блоков текста на изображении EasyOCR
            result = reader.readtext(cv_img_without_tables, paragraph=True, width_ths=1, add_margin=0.15)
            # Определение изображения, по подписи(Рисунок*****
            for block in result:
                block.append("text")
            for block in result:
                if re.search(r'(?:^|\s)(Рисунок|Чертеж|Черт\.)\s(\d+|[А-Я]+[.,]\d*)(?:\s|$)',
                             block[1]):
                    result, byte_io, image_name = find_box_image(result, block, pil_img)
                    images.append((f"{image_name}", byte_io, 'multipart/form-data'))
            array_line = list()

            # Собираем все блоки последовательно, относительно их позидий
            for index, block in enumerate(result):
                for formula in formulas:
                    if block[2] == "image" and not formula[2] and block[0][0][1] <= formula[0][1] <= block[0][2][1]:
                        formula[2] = True
                    if block[0][0][1] >= formula[0][1] and not formula[2]:
                        formula[2] = True
                        array_line.append([
                            [[formula[0][0], formula[0][1]],
                             [formula[0][2], formula[0][1]],
                             [formula[0][2], formula[0][3]],
                             [formula[0][0], formula[0][3]]],
                            formula[1],
                            "formula"
                        ])
                for index_img, img in enumerate(final_images_bboxes):
                    if block[2] == "image" and img[0][1] > block[0][0][1] and img[1][1] < block[0][2][1]:
                        img[2] = True
                    if block[0][0][1] > img[0][1] and not img[2]:
                        img[2] = True
                        block_image, byte_io, image_name = get_image(img, pil_img, index_img, page_index)
                        images.append((f"{image_name}", byte_io, 'multipart/form-data'))
                        array_line.append(block_image)
                for table in page_table_struct:
                    if block[2] == "image" and not table["page_add"] and block[0][0][1] <= table['bbox'][1] <= block[0][2][
                        1]:
                        table["page_add"] = True
                    if block[0][0][1] > table['bbox'][1] and not table["page_add"]:
                        table["page_add"] = True
                        if "cells" in table:
                            array_line.append([
                                [[table['bbox'][0], table['bbox'][1] + 10],
                                 [table['bbox'][2], table['bbox'][1] + 10],
                                 [table['bbox'][2], table['bbox'][3] - 10],
                                 [table['bbox'][0], table['bbox'][3] - 10]],
                                {"cells": table["cells"]},
                                "table"
                            ])
                array_line.append(block)
            # Добавляем формулы если они стоят в конце страницы
            for formula in formulas:
                if not formula[2]:
                    array_line.append([
                        [[formula[0][0], formula[0][1]],
                         [formula[0][2], formula[0][1]],
                         [formula[0][2], formula[0][3]],
                         [formula[0][0], formula[0][3]]],
                        formula[1],
                        "formula"
                    ])
            for index, img in enumerate(final_images_bboxes):
                if not img[2]:
                    img[2] = True
                    block_image, byte_io, image_name = get_image(img, pil_img, index, page_index)
                    images.append((f"{image_name}", byte_io, 'multipart/form-data'))
                    array_line.append(block_image)
            # Добавляем таблицы если они стоят в конце страницы
            for table in page_table_struct:
                if not table["page_add"]:
                    table["page_add"] = True
                    if "cells" in table:
                        array_line.append([
                            [[table['bbox'][0], table['bbox'][1] + 10],
                             [table['bbox'][2], table['bbox'][1] + 10],
                             [table['bbox'][2], table['bbox'][3] - 10],
                             [table['bbox'][0], table['bbox'][3] - 10]],
                            {"cells": table["cells"]},
                            "table"
                        ])
            if len(array_line):
                result = array_line

            # Remove overlapped regions
            cleared_ocr = []
            for i, block in enumerate(result):

                if i != len(result) - 1 and block[2] == "text":
                    overlaped = False
                    square = (block[0][2][0] - block[0][0][0]) * (block[0][2][1] - block[0][0][1])
                    for id_nb, nblock in enumerate(result):
                        nb_square = (nblock[0][2][0] - nblock[0][0][0]) * (nblock[0][2][1] - nblock[0][0][1])
                        if i != id_nb and (
                                block[0][0][0] >= nblock[0][0][0] and block[0][0][0] < nblock[0][2][0] and \
                                block[0][0][1] >= nblock[0][0][1] and block[0][0][1] < nblock[0][2][1]) and \
                                square < nb_square:
                            overlaped = True
                            break
                    if not overlaped:
                        cleared_ocr.append(block)
                else:
                    cleared_ocr.append(block)
            result = cleared_ocr

            # Распознание текста из найденых блоков TesseractOCR
            if self.tesseract:
                for index, box in enumerate(result):
                    if result[index][2] == "text":
                        streams.add(
                            f"image_to_string_{mlProcessingId}",
                            tesseract_image_to_string_formula,
                            (result[index][0], image, result, index, f_insertions, use_of_dictionaries, getLanguageOCR(page_index)))
                    # if result[index][2] == "formula":
                    #     streams.add(
                    #         f"image_to_string_{mlProcessingId}",
                    #         tesseract_image_to_string_formula,
                    #         (result[index][0], image, result, index, f_insertions, use_of_dictionaries))
                streams.end(f"image_to_string_{mlProcessingId}")
            # print(result, images)
            return result, images
        except Exception as ex:
            send_status(document_id, 500, mlProcessingId, document_type, page_index, 0, [ex])
            print("ERROR img_to_text:", ex)
            return None

    def del_streams(self, mlProcessingId):
        streams.del_process(f"image_to_string_{mlProcessingId}")
        return True
