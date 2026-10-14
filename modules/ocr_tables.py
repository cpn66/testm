import pytesseract
import cv2
import pandas as pd
import numpy as np


tesseract_cfg = {
        "page": "tsv --psm 1",
        "table": "-c tessedit_char_blacklist=|][/_ --oem 1 --psm 1",
        "cell": "-c tessedit_char_blacklist=|][/_ --psm 7",
    }


def include_xy(a, b):
    x_include = a[0] <= b[0] <= a[2] and a[0] <= b[2] <= a[2]
    y_include = a[1] <= b[1] <= a[3] and a[1] <= b[3] <= a[3]
    if x_include and y_include:
        return True
    else:
        return False

def scale_bboxes(ocr_data, shape, new_shape):
    h, w = shape
    new_h, new_w = new_shape
    for word, bboxes in ocr_data.items():
        ocr_data[word] = [
            int(bboxes[0] / w * new_w),
            int(bboxes[1] / h * new_h),
            int(bboxes[2] / w * new_w),
            int(bboxes[3] / h * new_h)
        ]
    return ocr_data

def remove_table_lines(img):
    result = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255,
                        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Remove horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    remove_horizontal = cv2.morphologyEx(thresh,
                                        cv2.MORPH_OPEN,
                                        horizontal_kernel,
                                        iterations=2)
    cnts = cv2.findContours(remove_horizontal, cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(result, [c], -1, (255, 255, 255), 5)

    # Remove vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    remove_vertical = cv2.morphologyEx(thresh,
                                    cv2.MORPH_OPEN,
                                    vertical_kernel,
                                    iterations=2)
    cnts = cv2.findContours(remove_vertical, cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(result, [c], -1, (255, 255, 255), 5)
    return result


def get_words_data(text_data):
    # out format [x_l, y_l, x_r, y_r]
    n_boxes = len(text_data['level'])
    words_bboxes_dict = {}
    for i in range(n_boxes):
        text = text_data['text'][i]
        if text_data['conf'][i] > -1 and len(text)>0 and len(text.strip())>0:
            (x, y, w, h) = (
                                text_data['left'][i],
                                text_data['top'][i],
                                text_data['width'][i],
                                text_data['height'][i]
                            )
            bbox = [int(num) for num in [x, y, x + w, y + h]]
            words_bboxes_dict[text] = bbox
    return words_bboxes_dict

def get_lines_data(text_data):
    lines = text_data.groupby(['block_num','par_num','line_num'])['text'].apply(list)
    left = text_data.groupby(['block_num','par_num','line_num'])['left'].apply(list)
    top = text_data.groupby(['block_num','par_num','line_num'])['top'].apply(list)
    width = text_data.groupby(['block_num','par_num','line_num'])['width'].apply(list)
    height = text_data.groupby(['block_num','par_num','line_num'])['height'].apply(list)
    conf = text_data.groupby(['block_num','par_num','line_num'])['conf'].apply(list)
    line_struct = []
    for l, t, w, h, text, cnf in zip(left, top, width, height, lines, conf):
        l = int(min(l))
        t = int(min(t))
        w = int(max(w))
        h = int(max(h))
        start = (l, t)
        end = (int(l + w), int(t + h))
        # conf_text = [ cnf[i] for i in range(len(cnf)) if cnf[i] >= 0 and len(str(text[i])) > 0]
        text = [ str(text[i]) for i in range(len(text)) if cnf[i] >= 0]
        line = " ".join(text).strip()
        if len(line):
            line_struct.append(
                {
                    'bbox': [start[0], start[1], end[0], end[1]],
                    'text': line
                }
            )
    # sort by y1
    line_struct = sorted(line_struct, key=lambda d: d['bbox'][1])
    return line_struct

def ocr_table(img, lang="rus+eng"):
    text_data = pytesseract.image_to_data(img, lang=lang, config=tesseract_cfg["table"], output_type='data.frame')
    words_with_bboxes = get_words_data(text_data)
    return words_with_bboxes


def img_to_text_data(img, lang="rus+eng", page_num = 0, get_word_bboxes = True):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text_data = pytesseract.image_to_data(img, lang=lang, config=tesseract_cfg['page'], output_type='data.frame')
    lines_struct = get_lines_data(text_data)
    return lines_struct

def cells_to_text_data(page_table_data, page_num = 0):
    if len(page_table_data):
        for table_id, table_data in enumerate(page_table_data):
            if table_data['type'] != 'table':
                continue
            table_bboxes = []
            table_bbox = table_data['bbox']
            cell_indxs = table_data['structure']
            temp_img = table_data["img"]
            if 'table_text' not in table_data:
                table_data['table_text'] = []
            if 'structure_text' not in table_data:
                struct_list = []
                for i in range(len(cell_indxs)):
                    struct_list.append([])
                    struct_list[i] = ['']*len(cell_indxs[i])
                table_data['structure_text'] = struct_list
            for i in range(len(cell_indxs)):
                for j in range(len(cell_indxs[i])):
                    cell_id = cell_indxs[i][j]
                    if cell_id >= 0:
                        cell_bbox = table_data['cells'][cell_id]['bbox']
                        table_bboxes.append(cell_bbox.copy())
                        temp_cell_bbox = cell_bbox.copy()
                        temp_cell_bbox[0] -= table_bbox[0]
                        temp_cell_bbox[1] -= table_bbox[1]
                        temp_cell_bbox[2] -= table_bbox[0]
                        temp_cell_bbox[3] -= table_bbox[1]
                        cell_img = temp_img[temp_cell_bbox[1]:temp_cell_bbox[3], temp_cell_bbox[0]:temp_cell_bbox[2]]
                        h, w, _ = cell_img.shape
                        if h == 0 or w == 0:
                            cell_bboxes[i][j] = []
                            continue
                        cell_img = cv2.resize(cell_img, (w*2, h*2), interpolation = cv2.INTER_AREA)
                        line_struct = img_to_text_data(cell_img, get_word_bboxes = False)
                        cell_text = ' '.join([l['text'] for l in line_struct])
                        table_data['cells'][cell_id]['text'] = cell_text
                        table_data['structure_text'][i][j] = cell_text
                        table_data['table_text'].append(cell_text)
            #print(table_id, "table_text: ", table_data['table_text'])
    return page_table_data


def tables_to_text_data(page_table_data, page_num = 0):
    if len(page_table_data):
        # merge tables to one img
        tables_w = [ abs(table_data['bbox'][2] - table_data['bbox'][0]) for table_data in page_table_data ]
        tables_h = [ abs(table_data['bbox'][3] - table_data['bbox'][1]) for table_data in page_table_data ]
        merged_w = max(tables_w)
        merged_h = sum(tables_h)
        merged_img = np.zeros( (merged_h,merged_w,3), dtype=np.uint8)
        start_pos_h = 0
        starts = [0]
        for table_data in page_table_data:
            if table_data['type'] != 'table':
                continue
            h, w, _ = table_data["img"].shape
            merged_img[start_pos_h:start_pos_h+h, 0:w] = table_data["img"]
            start_pos_h += h
            starts.append(start_pos_h)
        # find text on merged
        no_lines_merged = remove_table_lines(merged_img)
        h, w, _ = no_lines_merged.shape
        no_lines_merged = cv2.resize(no_lines_merged, (w*2, h*2), interpolation = cv2.INTER_AREA)
        new_h, new_w, _ = no_lines_merged.shape
        ocr_data = ocr_table(no_lines_merged)
        ocr_data = scale_bboxes(ocr_data, (new_h, new_w), (h, w))
        # text to cells
        start_id = 0
        for table_id, table_data in enumerate(page_table_data):
            if table_data['type'] != 'table':
                continue
            table_words_bboxes = []
            table_bbox = table_data['bbox']
            cell_indxes = table_data['structure']
            if 'table_text' not in table_data:
                table_data['table_text'] = []
            if 'structure_text' not in table_data:
                struct_list = []
                for i in range(len(cell_indxes)):
                    struct_list.append([])
                    struct_list[i] = ['']*len(cell_indxes[i])
                table_data['structure_text'] = struct_list
            # find text bboxes for temp table and convert bboxes to page coord
            h_intrv = [starts[start_id], starts[start_id]+(table_bbox[3]-table_bbox[1]) ]
            for word, w_box in ocr_data.items():
                if h_intrv[0] <= w_box[1] <= h_intrv[1] and h_intrv[0] <= w_box[3] <= h_intrv[1]:
                    w_box = [
                              w_box[0]+table_bbox[0],
                              w_box[1]-h_intrv[0]+table_bbox[1],
                              w_box[2]+table_bbox[0],
                              w_box[3]-h_intrv[0]+table_bbox[1]
                            ]
                    table_words_bboxes.append(w_box)
                    table_data['table_text'].append(word)
            for i in range(len(cell_indxes)):
                for j in range(len(cell_indxes[i])):
                    for w_pos, w_box in enumerate(table_words_bboxes):
                        cell_id = cell_indxes[i][j]
                        if cell_id >= 0:
                            cell_bbox = table_data['cells'][cell_id]['bbox']
                            result = include_xy(cell_bbox, w_box)
                            if result:
                                if 'text' not in table_data['cells'][cell_id]:
                                    table_data['cells'][cell_id]['text'] = ''
                                if len(table_data['structure_text'][i][j]):
                                    table_data['structure_text'][i][j] += " "
                                    table_data['cells'][cell_id]['text'] += ' '
                                table_data['structure_text'][i][j] += table_data['table_text'][w_pos]
                                table_data['cells'][cell_id]['text'] += table_data['table_text'][w_pos]
            start_id += 1
            #print(table_id, "table_text: ", table_data['table_text'])
    return page_table_data
