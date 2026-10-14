import re
from Levenshtein import distance as lev

def transliterate(name):
    slovar = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
              'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
              'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h',
              'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e',
              'ю': 'u', 'я': 'ya', 'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'YO',
              'Ж': 'ZH', 'З': 'Z', 'И': 'I', 'Й': 'I', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
              'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'H',
              'Ц': 'C', 'Ч': 'CH', 'Ш': 'SH', 'Щ': 'SCH', 'Ъ': '', 'Ы': 'y', 'Ь': '', 'Э': 'E',
              'Ю': 'U', 'Я': 'YA', ',': '', '?': '', ' ': '_', '~': '', '!': '', '@': '', '#': '',
              '$': '', '%': '', '^': '', '&': '', '*': '', '(': '', ')': '', '-': '', '=': '', '+': '',
              ':': '', ';': '', '<': '', '>': '', '\'': '', '"': '', '\\': '', '/': '', '№': '',
              '[': '', ']': '', '{': '', '}': '', 'ґ': '', 'ї': '', 'є': '', 'Ґ': 'g', 'Ї': 'i',
              'Є': 'e', '—': ''}

    # Циклически заменяем все буквы в строке
    for key in slovar:
        name = name.replace(key, slovar[key])
    return name


def table_to_text(table, text="table:::"):
    table = table["cells"]
    # print(table)
    rows = {}

    for key in table:
        if table[key]['columns'][0] in rows:
            rows[table[key]['columns'][0]].append(table[key]['rows'][0])
        else:
            rows[table[key]['columns'][0]] = list()
            rows[table[key]['columns'][0]].append(table[key]['rows'][0])
    for idx in rows:
        rows[idx] = sorted(rows[idx])
    for idx_r in rows:
        new_r = True
        for idx_c in rows[idx_r]:
            for key in table:
                if table[key]['columns'][0] == idx_r and new_r:
                    new_r = False
                    text += "tr:::"
                if table[key]['columns'][0] == idx_r and table[key]['rows'][0] == idx_c:
                    text += f"td(rows={table[key]['columns'][1] - table[key]['columns'][0]},columns={table[key]['rows'][1] - table[key]['rows'][0]},value={table[key]['text']}):::"
    text += '\n'
    return text


def table_text_to_html(match):
    text = ""
    first_tr = True
    for tag in match.split(":::"):
        if tag.startswith("table"):
            text += "<table>"
        if tag.startswith("tr"):
            if not first_tr:
                text += "</tr>"
            else:
                first_tr = False
            text += "<tr>"
        if tag.startswith("td"):
            match_tag = re.search("\(rows=(.*),columns=(.*),value=(.*)\)", tag)
            if match_tag and match_tag.groups():
                text += f"<td "
                if int(match_tag.groups()[1]) > 1:
                    text += f"colspan='{match_tag.groups()[1]}' "
                if int(match_tag.groups()[0]) > 1:
                    text += f"rowspan='{match_tag.groups()[0]}' "
                text += f">{match_tag.groups()[2]}</td>"
    text += "</tr></table>"
    return text


def replase_special_characters_in_xml(text):
    text = re.sub("&", '&amp;', text)
    text = re.sub("<", '&lt;', text)
    text = re.sub(">", '&gt;', text)
    text = re.sub("-\n", '', text)
    text = re.sub("\f", '', text)
    text = re.sub(" \n", '', text)
    text = re.sub("—\n", '—', text)
    text = re.sub("(?<=[^\n])table:::", '\ntable:::', text)
    text = re.sub("(?<=[^\n])img:::", '\nimg:::', text)
    text = re.sub("(?<=[^\n])math:::", '\nmath:::', text)
    return text


def get_bbox(bbox, line):
    if bbox[2] == 0 or line[0][0]/line[4][0] < bbox[2]:
        bbox[2] = line[0][0]/line[4][0]
    if bbox[0] == 0 or line[3] < bbox[0]:
        bbox[0] = line[3]
    if bbox[5] == 0 or line[0][2]/line[4][0] > bbox[5]:
        bbox[5] = line[0][2]/line[4][0]
    if bbox[3] == 0 or line[3] > bbox[3]:
        bbox[3] = line[3]
        bbox[4] = 0
    if bbox[1] == 0 or (line[0][1]%4000/line[4][1] < bbox[1] and bbox[0] == line[3]):
        bbox[1] = line[0][1]%4000/line[4][1]
    if bbox[4] == 0 or line[0][3]%4000/line[4][1] > bbox[4]:
        bbox[4] = line[0][3]%4000/line[4][1]
    # print(bbox)
    return bbox


def lines_to_html(type, lines):
    if type == 'text':
        return lines, [0, 0, 0, 0, 0, 0]
    if type == 'text-to-text':
        if len(lines) > 0:
            lines = replase_special_characters_in_xml(lines)
            lines = re.sub("\n\n", '', lines)
            lines = re.sub("\n$", '', lines)
            lines = re.sub("\n", ' ', lines)
            return lines, [0, 0, 0, 0, 0, 0]
        else:
            return "", [0, 0, 0, 0, 0, 0]
    if type == 'line-to-text':
        if len(lines) > 0:
            lines[1] = replase_special_characters_in_xml(lines[1])
            lines[1] = re.sub("\n\n", '', lines[1])
            lines[1] = re.sub("\n$", '', lines[1])
            lines[1] = re.sub("\n", ' ', lines[1])
            return lines[1], [lines[3], lines[0][1]/lines[4][1], lines[0][0]/lines[4][0],
                              lines[3], lines[0][3]/lines[4][1], lines[0][2]/lines[4][0]]
        else:
            return "", [0, 0, 0, 0, 0, 0]
    if type == 'line-to-html':
        if len(lines) > 0:
            lines[1] = replase_special_characters_in_xml(lines[1])
            lines[1] = re.sub("\n\n", '<br></br>', lines[1])
            lines[1] = re.sub("\n(?=[А-ЯA-Z\d(]|img|table)", '</p><p>', lines[1])
            lines[1] = re.sub("\n$", '', lines[1])
            lines[1] = re.sub("\n", ' ', lines[1])
            return f"<p>{lines[1]}</p>", [lines[3], lines[0][1]/lines[4][1], lines[0][0]/lines[4][0],
                                          lines[3], lines[0][3]/lines[4][1], lines[0][2]/lines[4][0]]
        else:
            return "", [[0, 0, 0], [0, 0, 0]]
    if type == 'text-to-html':
        if len(lines) > 0:
            # print(222, lines)
            lines = replase_special_characters_in_xml(lines)
            lines = re.sub("\n\n", '<br></br>', lines)
            lines = re.sub("\n(?=[А-ЯA-Z\d(]|img|table)", '</p><p>', lines)
            lines = re.sub("\n$", '', lines)
            lines = re.sub("\n", ' ', lines)
            # print(111, lines)
            return f"<p>{lines}</p>", [0, 0, 0, 0, 0, 0]
        else:
            return "", [0, 0, 0, 0, 0, 0]
    if type == 'lines-to-text':
        result = ''
        bbox = [0, 0, 0, 0, 0, 0]
        for line in lines:
            bbox = get_bbox(bbox, line)
            result += lines_to_html('line-to-text', line)[0] + " "
        return result, bbox
    if type == 'lines-to-html':
        result = ''
        bbox = [0, 0, 0, 0, 0, 0]
        for line in lines:
            bbox = get_bbox(bbox, line)
            result += lines_to_html('line-to-html', line)[0]
        return result, bbox
    if type == 'lines-to-none':
        result = ''
        bbox = [0, 0, 0, 0, 0, 0]
        for line in lines:
            bbox = get_bbox(bbox, line)
            result += line[1]
        return result, bbox
    if type == 'dict-to-html':
        for idx in lines:
            result = ''
            bbox = [0, 0, 0, 0, 0, 0]
            for line in lines[idx]:
                bbox = get_bbox(bbox, line)
                result += lines_to_html('text-to-html', line[1])[0]
            lines[idx] = [result, bbox]
        return lines, 1


def comparisonWordsLevenshtein(a, b):
    if len(a) <= len(b):
        eps = 5
        word = b[:len(a)+eps]
        eps = len(word)-len(a)
        if lev(a, word) <= eps:
            return True
    return False
