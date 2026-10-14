import re
import json
import os
from modules.default import lines_to_html, table_to_text, comparisonWordsLevenshtein
from modules.entity_search.application import Applications


def filter_lines(line):  # Фильтр прочитаных линий
    return line[-1]


def get_box_border(box_point: list):  # Перевод формата границ коробки (x_min, y_min, x_max, y_max)
    return box_point[0][0], box_point[0][1], box_point[2][0], box_point[2][1]


def find_box_by_text(lines, string):
    find_line = []
    for line in lines:
        if not find_line and re.search(string.lower()+"(?:[^а-яА-Я]|$)", line[1].lower().strip()):
            line[-1] = False
            find_line = line
        elif find_line:
            if 0 < find_line[0][1] - line[0][1] < 5:
                line[-1] = False
                find_line[1] += " " + line[1]
            return find_line
    return find_line


class TypePageDefaultSSSR:
    def __init__(self, gost, dir):
        print(gost, "стандартный", "СССР")
        # dir_project = os.path.dirname(__file__)
        self.config = json.load(open(f'{dir}', encoding='utf8'))
        self.config["box"]["gost"] = gost
        self.indexPageType = 0

    def getPages(self, all_text, page_type):
        # print(all_text.split("\n"))
        for text in all_text.split("\n")[0:20]:
            for sheet in self.config["sequence_of_sheets"][self.indexPageType + 1:]:
                for anchor in self.config["anchords"][sheet]:
                    if comparisonWordsLevenshtein(anchor, text):
                        self.indexPageType = self.config["sequence_of_sheets"].index(sheet)
                        return True, sheet
                if sheet in self.config["required"]:
                    break
        return False, page_type

    def parse_title(self, pages: list, xml):  # Парсер титульной страницы
        for line in pages:
            line[0] = get_box_border(line[0])
            line.append(True)
        xml['box-gost'] = find_box_by_text(pages, self.config["box"]["gost"])
        bottom_border = find_box_by_text(pages, 'Издание официальное')
        if not xml['box-gost']:
            xml['box-gost'] = [[0, 0, 0, 0], self.config["box"]["gost"], 'text', 0, [1, 1]]
        if not bottom_border:
            bottom_border = pages[-1]
        xml['ontological-type'] = self.config["box"]["gost"]
        xml['box-gost'][1] = lines_to_html("line-to-text", xml['box-gost'])[0].upper().strip()
        filtered_grades = list(filter(filter_lines, pages))
        for line in filtered_grades:
            if line[1] != "":
                line[-1] = False
                xml['comm-ref'].append(line)
                break
        filtered_grades = list(filter(filter_lines, pages))
        meta = [[], "", ]
        for line in filtered_grades:
            if bottom_border[0][1] > line[0][3]:
                meta = [line[0], meta[1]+line[1], line[2], line[3], line[4], line[-1]]
        match = re.findall('^(.+)\n([\S\s]+)\n(.+)(?:$|\n)', meta[1])
        if match:
            if match[0][0]:
                xml['intro'].append([meta[0], match[0][0], meta[2], meta[3], meta[4], meta[-1]])
            if match[0][1]:
                xml['main'].append([meta[0], match[0][1], meta[2], meta[3], meta[4], meta[-1]])
            if match[0][2]:
                xml['compl'].append([meta[0], match[0][2], meta[2], meta[3], meta[4], meta[-1]])


    def parse_bibliography(self, pages: list, xml):
        for line in pages:
            line[0] = get_box_border(line[0])
            line.append(True)
        xml['title'] = find_box_by_text(pages, self.config["box"]["bibliography"])
        for line in pages:
            if xml['title'][0][1] > line[0][3]:
                line[-1] = False
        filtered_grades = list(filter(filter_lines, pages))
        sec_number = '1'
        xml['std'][sec_number] = list()
        for line in filtered_grades:
            sections = re.findall(r'(?=[\[\(\|](\d+)[\]\)\|])*([\s\S]+?)(?=[\[\(\|]\d+[\]\)]|$)', line[1])
            if len(sections) > 0:
                for sec in sections:
                    if len(sec[1]) > 5:
                        if sec[0] == '' or int(sec[0]) < int(sec_number) or int(sec[0]) - int(sec_number) > 5:
                            xml['std'][sec_number].append([line[0], line[1], line[2], line[3], line[4]])
                        else:
                            xml['std'][sec[0]] = list()
                            xml['std'][sec[0]].append([line[0], sec[1], line[2], line[3], line[4]])
                            sec_number = sec[0]
                    else:
                        xml['std'][sec_number].append([line[0], line[1], line[2], line[3], line[4]])
            else:
                xml['std'][sec_number].append([line[0], line[1], line[2], line[3], line[4]])
            line[-1] = False

    def parse_application(self, pages: list, xml):
        for line in pages:
            line[0] = get_box_border(line[0])
            line.append(True)
        xml['applications'] = Applications(pages).find_applications()

    def parse_keywords(self, pages: list, xml):
        for line in pages:
            line[0] = get_box_border(line[0])
            line.append(True)
        xml['keywords'] = find_box_by_text(pages, self.config["box"]["keywords"])
        filtered_grades = list(filter(filter_lines, pages))
        for line in filtered_grades:
            if len(find_box_by_text([line], self.config["box"]["gost"])):
                continue
            if len(line[1]) > 0 and line[0][1] < xml['keywords'][0][1]:
                xml['type_documents'].append(line)

    def parse_introduction(self, pages: list, xml):
        for line in pages:
            line[0] = get_box_border(line[0])
            line.append(True)
        # 'foreword': None,
        # 'notes': list(),
        # 'permissions': list()
        xml['introduction'] = [find_box_by_text(pages, self.config["box"]["introduction"])]
        if not xml['introduction'][0]:
            xml['introduction'] = [[[0, 0, 0, 0], self.config["box"]["introduction"], "text", 0, [1, 1]]]
        filtered_grades = list(filter(filter_lines, pages))
        for line in filtered_grades:
            line[-1] = False
            xml['notes'].append(line)

    def parse_foreword(self, pages: list, xml, ontological_type):
        for line in pages:
            line[0] = get_box_border(line[0])
            line.append(True)
        # 'foreword': None,
        # 'notes': list(),
        # 'permissions': list()
        xml['foreword'] = [find_box_by_text(pages, self.config["box"]["foreword"])]
        if not xml['foreword'][0]:
            xml['foreword'] = [[[0, 0, 0, 0], "", "text", 0, [1, 1]]]
        else:
            xml['foreword'][0][1] = ""
        filtered_grades = list(filter(filter_lines, pages))
        last_good_line = None
        end_line = None
        for line in filtered_grades:
            if xml['foreword'][0][0][3] < line[0][1]:
                if re.search(r'^[\d]|[/\n][\d]|РАЗРАБОТАН|ВНЕСЕН|ПРИНЯТ|ВЗАМЕН', line[1]):
                    last_good_line = line
                if re.search(r'РАЗРАБОТАН', line[1]):
                    xml['doc-ident'] = line
                if re.search(r'ВНЕСЕН', line[1]):
                    xml['secretariat'] = line
                if (not end_line and
                        (re.search('©([\s\S]+?)[.,] оформление[,.] [\d]{4}', line[1]) or
                         re.search('Стандартинформ', line[1]))):
                    end_line = line
                if ontological_type:
                    find_box_by_text(pages, ontological_type)
        filtered_grades = list(filter(filter_lines, pages))
        for line in filtered_grades:
            if xml['foreword'][0][0][3] < line[0][1] and (
                    last_good_line[0][1] > line[0][3] or last_good_line[0][1] == line[0][1]):
                line[-1] = False
                xml['foreword'].append(line)
        filtered_grades = list(filter(filter_lines, pages))
        for line in filtered_grades:
            if xml['foreword'][0][0][3] < line[0][1] and last_good_line[0][3] < line[0][1] and (
                    end_line and end_line[0][1] > line[0][3]):
                line[-1] = False
                xml['notes'].append(line)

    def parse_content(self, pages: list, xml):
        for line in pages:
            line[0] = get_box_border(line[0])
            line.append(True)
        # 'foreword': None,
        # 'notes': list(),
        # 'permissions': list()
        for block in self.config["box"]["content"]:
            xml['implementation'] = find_box_by_text(pages, block)
            if xml['implementation']:
                break
        block_lines = (self.config["box"]["gost"], self.config["box"]["end-gost"])
        for line in pages:
            # if line[1].strip().startswith(box_gost[1]):
            #     line[-1] = False
            # print(xml['implementation'][0][1], line, xml['implementation'][0][1] > line[0][3])
            if xml['implementation'] and xml['implementation'][0][1] > line[0][3]:
                line[-1] = False
            elif len(line[1]) < 100 and line[1].strip().startswith(block_lines[0]):
                line[-1] = False
            elif len(line[1]) < 100 and line[1].strip().startswith(block_lines[1]):
                line[-1] = False
            elif len(line[1]) < 5:
                line[-1] = False
        filtered_grades = list(filter(filter_lines, pages))
        # print(filtered_grades)
        sec_number = 0
        for line in filtered_grades:
            sections = re.findall('(?:^|\n)([\d]+)\.*([\d]*)\.*([\d]*)[^.\d\w—]([\s\S]*?)(?=\n\d+|\n$)', line[1])
            if len(sections) > 0:
                if sec_number == 0:
                    sec_number = '1'
                    xml['sec'][sec_number] = list()
                for sec in sections:
                    if len(sec[3]) > 5:
                        if sec[0] == '' or int(sec[0]) < int(sec_number) or int(sec[0]) - int(sec_number) > 1:
                            if sec[1] == '':
                                xml['sec'][sec_number].append([line[0], f"{sec[0]} {sec[3]}", line[2], line[3], line[4]])
                            else:
                                if sec[2] == '':
                                    xml['sec'][sec_number].append([line[0], f"{sec[0]}.{sec[1]} {sec[3]}", line[2], line[3], line[4]])
                                else:
                                    xml['sec'][sec_number].append([line[0], f"{sec[0]}.{sec[1]}.{sec[2]} {sec[3]}", line[2], line[3], line[4]])
                        else:
                            sec_number = sec[0]
                            if not sec[0] in xml['sec']:
                                xml['sec'][sec[0]] = list()
                            if sec[1] == '':
                                xml['sec'][sec[0]].append([line[0], sec[3], line[2], line[3], line[4]])
                            else:
                                if sec[2] == '':
                                    xml['sec'][sec[0]].append([line[0], f"{sec[0]}.{sec[1]} {sec[3]}", line[2], line[3], line[4]])
                                else:
                                    xml['sec'][sec[0]].append([line[0], f"{sec[0]}.{sec[1]}.{sec[2]} {sec[3]}", line[2], line[3], line[4]])
                    # else:
                    #     xml['sec'][sec_number].append(line[1])
                    #     break
            else:
                if sec_number == 0:
                    xml['implementation_text'].append([line[0], line[1], line[2], line[3], line[4]])
                else:
                    xml['sec'][sec_number].append([line[0], line[1], line[2], line[3], line[4]])
            line[-1] = False


