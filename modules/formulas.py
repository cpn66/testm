import os
import re
import requests
import pandas as pd
import numpy as np
from itertools import chain

# from sympy.parsing.latex import parse_latex

OPENNER = "math:::"
CLOSER = ":::"

patterns = {
    "arrow": r"\\longrightarrow",
    "digit": r"\d+",
    "darrow": r"\d+\\longrightarrow",
    "chars": r"[а-яА-ЯёЁa-zA-Z]",

}

STYLE = {
    "bar": r"\\bar",
    "dot": r"\\dot",
    "cdot": r"\\cdot",
    "hat": r"\\hat",
    "scriptstyle":r"\\scriptstyle",
    "fig_brackets": r"\{|\}",
    "bf": r"\\bf",
    "rm": r"\\rm",
    "bm": r"\\bm",
    "italic": r"\\it",
    "overline": r"\\overline",
    "underline": r"\\underline",
    "brackets":r"\(|\)",
    "dash": "-",
    "tilda": "~",
    "strel": r"\\stackrel",
    "frown": r"\\frown",

    "boldm": r"\\boldmath",
    "mathtt": r"\\mathtt",
    "mathbf": r"\\mathbf",
    "mathrm": r"\\mathrm",
    "mathbb": r"\\mathbb",
    "mathfrak": r"\\mathfrak",
    "mathsf": r"\\mathsf",
    "mathit": r"\\mathit",
    "mathcal": r"\\mathcal",

    "boldsymbol": r"\\boldsymbol",
}

def find_all_occurrences(input_string, pattern):
    occuerrences = []
    index = 0
    offset = len(pattern)
    while index < len(input_string):
        start_index = input_string.find(pattern, index)
        if start_index == -1:
            break
        occuerrences.append(start_index)
        index = start_index + offset

    return occuerrences


def formula_as_file(formula, file, negate=False):
    tfile = file
    if negate:
        tfile = 'tmp.png'
    r = requests.get('http://latex.codecogs.com/png.latex?\dpi{300} \huge %s' % formula)
    f = open(tfile, 'wb')
    f.write(r.content)
    f.close()
    if negate:
        os.system('convert tmp.png -channel RGB -negate -colorspace rgb %s' % file)


def filter_blocks(blocks):
    """ Removes unnecessary keys from dict, data of empty entities
        and filter content by lines number.
    """
    target_keys = ["text", "top", "left", "width", "height", "line_num"]
    remove_idx = [i for i, x in enumerate(blocks["text"]) if x == ""]
    filtered_blocks = {}
    for key in target_keys:
        entity = [item for index, item in enumerate(blocks[key]) if index not in remove_idx]
        filtered_blocks[key] = entity

    sorted_blocks = {}
    unique_levels = set(filtered_blocks["line_num"])
    filtered_zip = list(zip(filtered_blocks["line_num"], filtered_blocks["text"], filtered_blocks["left"], \
                       filtered_blocks["top"], filtered_blocks["width"], filtered_blocks["height"]))

    for level in unique_levels:
        sorted_blocks[level] = list(filter(lambda x: x[0] == level, filtered_zip))

    for key in sorted_blocks.keys():
        sorted_dict = {"text": [], "left": [], "top": [], "width": [], "height": []}

        for item in sorted_blocks[key]:
            # sorted_dict['line_num'].append(item[0])
            sorted_dict['text'].append(item[1])
            sorted_dict['left'].append(item[2])
            sorted_dict['top'].append(item[3])
            sorted_dict['width'].append(item[4])
            sorted_dict['height'].append(item[5])

        # Change structure
        sorted_blocks[key] = sorted_dict

    return sorted_blocks


def filter_formula(equation):
    equation = equation.replace(' ', '')
    nums_exist = re.findall(patterns["digit"], equation)
    for item in STYLE:
        equation = re.sub(STYLE[item], '', equation)
    # fixed_eq = re.sub(patterns["bar"], '', fixed_eq)
    fixed_eq = "dummy_string"
    if len(nums_exist) > 0:
        if len(re.findall(patterns["arrow"], equation)) > 0:
            fixed_eq = re.sub(patterns["darrow"], '', equation)
        else:
            fixed_eq = re.sub(patterns["digit"], '', equation)
            if len(fixed_eq) > 0:
                fixed_eq = fixed_eq.replace('.', '')
                fixed_eq = re.sub(patterns["chars"], '', fixed_eq, count=1)

    else:
        fixed_eq = re.sub(patterns["arrow"], '', equation)
        fixed_eq = re.sub(patterns["chars"], '', fixed_eq)


    if len(fixed_eq) != 0:
        return False

    return True


def insert_formula_into_text(split_blocks, formulas, box):
    lines = str()
    offset = 10
    crop_origin_x = box[0][0]
    crop_origin_y = box[0][1]

    block_math = []
    line_struct = []

    # Collect formulas for current text_block
    if len(formulas) > 0:
        for ind, math in enumerate(formulas):
            if box[0][1] - offset <= math["position"][0][1] and \
                box[2][1] + offset >= math["position"][2][1] and \
                (box[0][0] - offset <= math["position"][0][0] and \
                box[2][0] + offset >= math["position"][2][0] or \
                abs(math["position"][2][0] - box[0][0]) < offset or \
                abs(math["position"][0][0] - box[2][0] < offset)):
                if math["permit"]:
                    block_math.append(math)
    text_df = pd.DataFrame.from_dict(split_blocks)
    lines = text_df.groupby(['block_num', 'par_num', 'line_num'])['text'].apply(list)
    left = text_df.groupby(['block_num', 'par_num', 'line_num'])['left'].apply(list)
    top = text_df.groupby(['block_num', 'par_num', 'line_num'])['top'].apply(list)
    width = text_df.groupby(['block_num', 'par_num', 'line_num'])['width'].apply(list)
    height = text_df.groupby(['block_num', 'par_num', 'line_num'])['height'].apply(list)
    conf = text_df.groupby(['block_num', 'par_num', 'line_num'])['conf'].apply(list)

    uniq_block = set(text_df["block_num"])

    if len(block_math) > 0:
        for i, math in enumerate(block_math):

            f_top = int(math["position"][0][1]) - crop_origin_y
            f_bot = int(math["position"][2][1]) - crop_origin_y
            f_right = int(math["position"][2][0]) - crop_origin_x
            f_left = int(math["position"][0][0]) - crop_origin_x
            f_center_line = (f_bot + f_top) / 2
            f_inserted = False

            for b_level in uniq_block:
                par_block = list(lines[b_level].index.unique('par_num'))
                for ind_par, b_par in enumerate(par_block):
                    line_block = list(lines[b_level][b_par].index.unique('line_num'))

                    for b_line in line_block:
                        line = lines[b_level][b_par][b_line]

                        # Get top bottom border for formula placement.
                        t_top = np.array(top[b_level][b_par][b_line])
                        t_center_line = t_top + np.array(height[b_level][b_par][b_line]) / 2
                        t_center_line = np.median(t_center_line)
                        if abs(t_center_line - f_center_line) <= 6:
                            for item_ind in range(len(line)):
                                word = lines[b_level][b_par][b_line][item_ind]
                                if len(line) > 1 and item_ind == 0 and word == '' or \
                                        conf[b_level][b_par][b_line][item_ind] == -1:
                                    continue

                                t_left = left[b_level][b_par][b_line][item_ind]
                                t_right = left[b_level][b_par][b_line][item_ind] + width[b_level][b_par][b_line][item_ind]
                                if not f_inserted and (abs(t_left - f_right) <= offset or \
                                    abs(t_left - f_left) <= offset):

                                    text = "{0} {1}".format(math["text"], word)
                                    lines[b_level][b_par][b_line][item_ind] = text
                                    conf[b_level][b_par][b_line][item_ind] = 11
                                    f_inserted = True
                                elif not f_inserted and (abs(t_right - f_left) <= offset):

                                    text = "{0} {1}".format(word, math["text"])
                                    lines[b_level][b_par][b_line][item_ind] = text
                                    conf[b_level][b_par][b_line][item_ind] = 11
                                    f_inserted = True

    for l, t, w, h, text, cnf in zip(left, top, width, height, lines, conf):
        l = int(min(l))
        t = int(min(t))
        w = int(max(w))
        h = int(max(h))
        start = (l, t)
        end = (int(l + w), int(t + h))
        text = [str(text[i]) for i in range(len(text)) if cnf[i] >= 0]

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
    lines = [l["text"] + "\n" for l in line_struct]

    lines = "".join(lines)

    return lines


def remove_words_breaks(text_lines):
    text_wo_breaks = str()
    lines_count = len(text_lines)
    for i in range(lines_count):
        if i < lines_count - 1 and len(text_lines[i]) > 2:
            if text_lines[i][-1] in ["-", "–", "—"] and text_lines[i][-2].isalpha():
                line_parts = text_lines[i + 1].split(" ")
                text_lines[i] = text_lines[i][:-1] + line_parts[0]
                text_lines[i + 1] = " ".join(line_parts[1:])
    text_wo_breaks = text_lines
    return text_wo_breaks


def remove_tag_with_content(string, tag="math"):
    pattern = r"<{}>.*?</{}>".format(tag, tag)
    cleaned_string = re.sub(pattern, "", string)
    return cleaned_string


def get_words(text, num_words, left_side=False):
    word = ""
    if len(text) > 0:
        text = remove_tag_with_content(text)
        word = text.split(' ')
        word = word[-num_words:] if left_side else word[:num_words]
        word = " ".join(word)

    return word


def extract_formulas(text, enc_words=1):
    math = []
    openner = find_all_occurrences(text, OPENNER)
    closer = find_all_occurrences(text, CLOSER)
    indexes = list(chain(*zip(openner, closer)))
    for ind in range(len(indexes)):
        if ind % 2 == 0:
            offset = indexes[ind] + len(OPENNER)
            formula = text[offset:indexes[ind + 1]]
            left = text[:indexes[ind] - 1]
            left = get_words(left, enc_words, True)

            closer = indexes[ind + 1] + len(CLOSER) + 1
            right = text[closer:]
            right = get_words(right, enc_words)
            items = (left, formula, right)

            math.append(items)

    return math


def correct_text(text_lines, speller):
    corrected__text = []
    text_lines = remove_words_breaks(text_lines)

    for line in text_lines:
        openner = find_all_occurrences(line, OPENNER)
        closer = find_all_occurrences(line, CLOSER)
        indexes = list(chain(*zip(openner, closer)))

        if len(indexes) > 0:
            formulas = []
            chunks = []
            for i in range(len(indexes)):
                if i == 0 and indexes[i] > 0:
                    corrected_chunk = speller.dictionary_correction(line[:indexes[i]])

                elif i == len(indexes) - 1 and indexes[i] < len(line):
                    offset = indexes[i] + len(CLOSER)
                    corrected_chunk = speller.dictionary_correction(line[offset:])
                    chunks.append(corrected_chunk)

                elif i % 2 == 0:  # index of openner
                    offset = indexes[i] + len(OPENNER)
                    formula = "math:::%s:::" % line[offset:indexes[i + 1]]
                    formulas.append(formula)

                elif i % 2 == 1:  # Closer
                    offset = indexes[i] + len(CLOSER)
                    corrected_chunk = speller.dictionary_correction(line[offset:indexes[i + 1]])
                    chunks.append(corrected_chunk)
            corrected_line = list(chain(*zip(formulas, chunks))) if indexes[0] == 0 else list(chain(*zip(chunks, formulas)))
            corrected_line = "".join(corrected_line)
        else:
            corrected_line = speller.dictionary_correction(line)

        corrected__text.append(corrected_line)

    return corrected__text
