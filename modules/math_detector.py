import io
import os
import sys
import pytesseract
from scipy import stats
from PIL import ImageDraw, ImageFont
import numpy as np
from pix2text import Pix2Text
from pix2tex.cli import LatexOCR
from tokenizers.decoders import ByteLevel
from munch import Munch

root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_path)
sys.path.append(os.getcwd())

from modules.formulas import filter_formula

rep_chars = [":", ";", '.', '°', '-', '=', '--', '+', '—', '~', '*', '%']

class MathDetector:
    def __init__(self, gpu, det_conf_thresh=0.4):
        th = {
            'formula2general': 0.85,
            'english2general': 0.85,
        }
        if gpu:
            device = "cuda"
        else:
            device = "cpu"
        self.p2t = Pix2Text(analyzer_config=dict(model_name='mfd', model_fp='lib/math/int_ex_wo_ema.pt',
                                                 model_backend="pytorch"), device=device, thresholds=th,
                            resized_shape=993)
        self.layout_det = Pix2Text(analyzer_config=dict(model_name='layout'))
        path = f'{os.getcwd()}/lib/math/ocr/mixed.pth'
        cfg = f'{os.getcwd()}/lib/math/ocr/mixed.yaml'
        config = Munch({'config': cfg, 'checkpoint': path, 'no_cuda': True, 'no_resize': False})

        self.latex_vit = LatexOCR(arguments=config)
        self.decoder = ByteLevel()
        self.det_conf = det_conf_thresh
        # self.font = ImageFont.truetype('/opt/ws/lib/arial.ttf', 12)

        self.cnt = 0

    def recognize(self, crop):

        recog = self.latex_vit(crop)
        latex_ocr = list()
        for char in recog.split(' '):
            latex_ocr.append(self.decoder.decode([char]))

        return "".join(latex_ocr)

    def pack_images(self, math_equations, type, img, remove=False):
        bb_list = []
        append_permit = True
        math_equations = [eq for eq in math_equations if eq["type"] == type]
        for i, bb_array in enumerate(math_equations):
            box = self.get_bbox_from_p2t(bb_array)
            crop = img.crop(box)
            buffer = io.BytesIO()
            crop.save(buffer, 'png')
            if type == "embedding":
                math_equations[i]["text"] = self.recognize(crop)
                append_permit = self.check_equation(bb_array)
            if append_permit:
                bb_list.append([box, buffer])

                if remove:
                    img = self.remove_math_from_page(img, box)
            math_equations[i].update({"permit": append_permit})

        return bb_list, img

    def draw_equations(self, eq_data, image):
        drawer = ImageDraw.Draw(image)
        for item in eq_data:
            box = self.get_bbox_from_p2t(item)
            if item["permit"]:
                if "tesseract" in item["type"]:
                    color = 'purple'
                else:
                    score = "score: %.3f" % round(item["score"], 3)
                    pos = (box[0], box[1] - 10)
                    drawer.text(pos, score, align="left", font=self.font, fill="red")
                    print(score)
                    color = 'blue'
            else:
                color = "orange"
            drawer.rectangle(box, outline=color)
        return image

    def check_equation(self, math):
        latex = math["text"].replace('$', '')
        if not filter_formula(latex) and '^' in latex or '_' in latex:
            math["text"] = "math:::%send:::" % latex
            return True
        return False

    def get_text_layout(self, image, idx):
        page_layout = self.layout_det.analyzer(image)
        return page_layout, None  #

    def find_math(self, img, idx, remove=False):

        math_expr = self.p2t.analyzer(img, conf_threshold=self.det_conf)
        insertions = [expr for expr in math_expr if expr["type"] == "embedding"]
        formulas, img = self.pack_images(math_expr, "isolated", img, remove)
        _, img = self.pack_images(math_expr, "embedding", img, False)
        return img, formulas, None, insertions

    def remove_math_from_page(self, img, bbox):
        draw = ImageDraw.Draw(img)
        draw.rectangle(bbox, fill="white")
        return img

    def rem_ins(self, insertions, image):
        for eq in insertions:
            bbox = eq['position']
            bbox = bbox.tolist()
            box = (int(bbox[0][0]), int(bbox[0][1]),
                   int(bbox[2][0]), int(bbox[2][1]))
            image = self.remove_math_from_page(image, box)
        return image

    def split_data_on_lines(self, tess_eq, image_height):
        page_text = []
        lined_text = list()
        lines = dict()
        top = image_height - np.array(tess_eq["top"])
        bot = image_height - np.array(tess_eq["bottom"])
        right = np.array(tess_eq["right"])
        left = np.array(tess_eq["left"])
        width = right - left
        height = bot - top
        square = width * height

        avg_width = stats.mode(width).mode
        avg_height = stats.mode(height).mode

        for i in range(len(tess_eq["top"])):

            # Add space if distance between letters greater than avg letter
            item = tess_eq['char'][i] if i == 0 else ''
            if i > 0:
                spacing = (tess_eq['left'][i] - tess_eq['right'][i - 1])
                line = (tess_eq['bottom'][i - 1] - tess_eq['top'][i])
                if line > 0.2 * avg_height:
                    tess_eq["new_line"].append(True)
                    item = tess_eq['char'][i]
                else:
                    tess_eq["new_line"].append(False)
                    if spacing >= avg_width * 0.5:
                        tess_eq['char'][i] = ' ' + tess_eq['char'][i]
                        item = tess_eq['char'][i]
                    else:
                        item = tess_eq['char'][i]
            else:
                tess_eq["new_line"].append(True)

            page_text.append(item)
        line_indexes = np.where(tess_eq["new_line"])[0].tolist()

        for line_ind in range(len(line_indexes)):
            left = line_indexes[line_ind]
            if line_ind < len(line_indexes) - 1:
                right = line_indexes[line_ind + 1]
                loc_line = "".join(tess_eq['char'][left:right])
                lines[line_ind] = {
                    "char": tess_eq['char'][left:right],
                    "left": tess_eq['left'][left:right],
                    "top": tess_eq['top'][left:right],
                    "right": tess_eq['right'][left:right],
                    "bottom": tess_eq['bottom'][left:right],
                    "square": square[left:right]
                }
            else:
                lines[line_ind] = {
                    "char": tess_eq['char'][left:right],
                    "left": tess_eq['left'][left:right],
                    "top": tess_eq['top'][left:right],
                    "right": tess_eq['right'][left:right],
                    "bottom": tess_eq['bottom'][left:right],
                    "square": square[left:right]
                }
                loc_line = "".join(tess_eq['char'][left:])
            lined_text.append(loc_line)

        return lines

    def find_insertion_with_tesseract(self, image):
        tess_eq = pytesseract.image_to_boxes(image, lang="rus+eng",
                                             config="tsv --psm 6 -c hocr_char_boxes=1 -c tessedit_create_hocr=1 --oem 6",
                                             output_type=pytesseract.Output.DICT)
        res_img = image.copy()
        additional_insertions = list()

        tess_eq.update({"new_line": list()})

        lines = self.split_data_on_lines(tess_eq, image.height)

        for key in lines.keys():
            left = np.array(lines[key]["left"])
            if len(left) == 0:
                continue
            top = image.height - np.array(lines[key]["top"])
            right = np.array(lines[key]["right"])
            bot = image.height - np.array(lines[key]["bottom"])

            avg_top = stats.mode(top).mode
            avg_bot = stats.mode(bot).mode
            avg_width = np.mean(np.array(lines[key]["right"]) - np.array(lines[key]["left"]))
            avg_height = avg_bot - avg_top
            avg_square = avg_width * avg_height
            middle_line = (avg_top + avg_bot) / 2

            # Find indexes and powers\
            for ind in range(len(lines[key]['top'])):
                char = lines[key]['char'][ind]
                char_height = lines[key]['top'][ind] - lines[key]['bottom'][ind]
                char_square = (right[ind] - left[ind]) * (bot[ind] - top[ind])

                if lines[key]['char'][ind].replace(' ', '') in rep_chars and char_height <= avg_height:
                    continue
                box = [left[ind] - avg_width * 0.2, top[ind], right[ind] + avg_width * 0.2, bot[ind]]
                if (bot[ind] <= middle_line) and char_square > 0.3 * avg_square:
                    lines[key]['char'][ind] = "^^" + lines[key]['char'][ind]
                elif (top[ind] >= middle_line) and char_square > 0.3 * avg_square \
                        and (right[ind - 1] - left[ind]) < avg_width:
                    lines[key]['char'][ind] = "__" + lines[key]['char'][ind]
                elif middle_line > top[ind] and middle_line < bot[ind] and \
                        char_square > 0.3 * avg_square and (right[ind - 1] - left[ind]) < avg_width:

                    char_height = bot[ind] - top[ind]
                    top_height = middle_line - top[ind]
                    bot_height = bot[ind] - middle_line
                    if top_height / char_height > 0.9:
                        lines[key]['char'][ind] = "^^" + lines[key]['char'][ind]
                    elif bot_height / char_height > 0.9:
                        lines[key]['char'][ind] = "__" + lines[key]['char'][ind]
            # Get line and collect equations
            line = ''.join(lines[key]['char'])
            line_eq, image = self.extrat_eq_from_line(line, lines[key], image.height, image)
            additional_insertions.extend(line_eq)

        return additional_insertions, res_img

    def extrat_eq_from_line(self, line_text, line_data, image_height, img):
        add_eq = list()
        try:
            for part in line_text.split(' '):
                eq = ''
                if '^^' in part:
                    spl_part = part.split('^^')
                    if spl_part[0] == '':
                        continue
                    spl_part[-1] = '{%s}' % spl_part[-1]
                    eq = "^".join(spl_part)
                if '__' in part:
                    spl_part = part.split('__')
                    if (len(spl_part[0]) > 2 and spl_part[1] in [',', '.']) or \
                            spl_part[1] == '' or spl_part[0] == '' or \
                            spl_part[0][-1] in rep_chars:
                        continue
                    spl_part[-1] = '{%s}' % spl_part[-1]
                    eq = "_".join(spl_part)
                pos = line_text.find(part)

                pos = len(line_text[:pos].replace(' ', '').replace('^^', '').replace('__', ''))
                num_chars = len(part) - part.count('^^') * 2 - part.count('__') * 2

                if eq != '' and num_chars > 0:
                    left = np.min(np.array(line_data['left'][pos:pos + num_chars]))
                    top = np.min(image_height - np.array(line_data['top'][pos:pos + num_chars]))
                    right = np.max(np.array(line_data['right'][pos:pos + num_chars]))
                    bottom = np.max(image_height - np.array(line_data['bottom'][pos:pos + num_chars]))
                    box = [left, top, right, bottom]
                    box = [[left, top], [right, top], [right, bottom], [left, bottom]]
                    crop = img.crop([left, top, right, bottom])
                    recog = self.latex_vit(crop)
                    latex_ocr = list()
                    for char in recog.split(' '):
                        latex_ocr.append(self.decoder.decode([char]))
                    eq = "math:::%send:::" % "".join(latex_ocr)
                    data = {"position": np.array(box),
                            "text": eq,
                            "type": "embedding",
                            "permit": True}
                    add_eq.append(data)
        except:
            pass

        return add_eq, img

    def filter_overlapped_insertions(self, p2t_ins, tess_ins):

        merged_ins = list()
        merged_ins.extend(tess_ins)

        for p2tin in p2t_ins:
            overlap_flag = False
            for tin in tess_ins:
                overlap_flag = self.check_overlap(p2tin, tin)
                if overlap_flag:
                    break
            if not overlap_flag:
                merged_ins.append(p2tin)

        return merged_ins

    def get_bbox_from_p2t(self, item):
        try:
            bbox = item['position']
        except:
            bbox = item['box']
            item['position'] = item['box']
        bbox = [int(bbox[0][0]), int(bbox[0][1]),
                int(bbox[2][0]), int(bbox[2][1])]
        return bbox

    def check_overlap(self, boxA, boxB):
        is_overlapped = False
        boxA = self.get_bbox_from_p2t(boxA)
        boxB = self.get_bbox_from_p2t(boxB)
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
        boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
        boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
        iou = interArea / float(boxAArea + boxBArea - interArea)
        if iou > 0:
            is_overlapped = True

        return is_overlapped