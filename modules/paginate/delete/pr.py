import re
from modules.default import lines_to_html, table_to_text
from modules.entity_search.application import Applications
from modules.paginate.type.default import filter_lines, get_box_border, find_box_by_text

class TypePagePr:
    def __init__(self):
        print("ПР")
        self.config = []
        self.indexPageType = 0

    def getPages(self, text, page_type):
        for sheet in self.config["sequence_of_sheets"][self.indexPageType + 1:]:
            for anchor in self.config["anchords"][sheet]:
                if text.lower().startswith(anchor.lower()):
                    self.indexPageType = self.config["sequence_of_sheets"].index(sheet)
                    return True, sheet
            if sheet in self.config["required"]:
                return False, page_type
        return False, page_type

    def parse_title(self, pages: list, xml):  # Парсер титульной страницы
        for line in pages:
            line[0] = get_box_border(line[0])
            line.append(True)
        xml['box-gost'] = find_box_by_text(pages, self.config["box"]["gost"])
        if not xml['box-gost']:
            xml['box-gost'] = [[0, 0, 0, 0], self.config["box"]["gost"], 'text', 0]
        xml['ontological-type'] = self.config["box"]["gost"]
        xml['box-gost'][1] = lines_to_html("line-to-text", xml['box-gost']).upper().strip()
        filtered_grades = list(filter(filter_lines, pages))
        for line in filtered_grades:
            if xml['box-gost'][0][1] > line[0][3] or line[1] == "":
                line[-1] = False
                xml['comm-ref'].append(line)
        filtered_grades = list(filter(filter_lines, pages))
        for line in filtered_grades:
            middle = ((xml['box-gost'][0][1] + xml['box-gost'][0][3]) / (line[0][1] + line[0][3]))
            if xml['box-gost'][0][0] > line[0][2] and (0.9 < middle < 1.1):
                line[-1] = False
                xml['custom-meta'].append(line)
        filtered_grades = list(filter(filter_lines, pages))
        for line in filtered_grades:
            match = re.search(
                '([А-Я]{1}[а-я\s\\n]+|)(?=^|(?<=\\n))([А-Я\s\-\\n]+)(?=$|\\n)\\n([А-Я]{1}[а-я\s\\n]*|)',
                line[1])
            if match and match.groups()[1]:
                line[-1] = False
                if match.groups()[0]:
                    xml['intro'].append([line[0], match.groups()[0], line[2], line[3], line[-1]])
                if match.groups()[1]:
                    xml['main'].append([line[0], match.groups()[1], line[2], line[3], line[-1]])
                if match.groups()[2]:
                    xml['compl'].append([line[0], match.groups()[2], line[2], line[3], line[-1]])
        filtered_grades = list(filter(filter_lines, pages))
        if xml['main']:
            for line in filtered_grades:
                if xml['main'][0] and xml['main'][0][0][1] > line[0][3]:
                    line[-1] = False
                    xml['intro'].append(line)
        filtered_grades = list(filter(filter_lines, pages))
        for line in filtered_grades:
            if line[1].find(self.config["box"]["end-gost"]) > -1:
                line[-1] = False
                break
            line[-1] = False
            xml['compl'].append(line)


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
                            xml['std'][sec_number].append(line[1])
                        else:
                            xml['std'][sec[0]] = list()
                            xml['std'][sec[0]].append(sec[1])
                            sec_number = sec[0]
                    else:
                        xml['std'][sec_number].append(line[1])
            else:
                xml['std'][sec_number].append(line[1])
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
            xml['introduction'] = [[[0, 0, 0, 0], self.config["box"]["introduction"], "text"]]
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
            xml['foreword'] = [[[0, 0, 0, 0], "", "text"]]
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
        xml['implementation'] = find_box_by_text(pages, self.config["box"]["content"])
        block_lines = (self.config["box"]["gost"], self.config["box"]["end-gost"])
        for line in pages:
            # if line[1].strip().startswith(box_gost[1]):
            #     line[-1] = False
            if xml['implementation'] and xml['implementation'][0][1] > line[0][3]:
                line[-1] = False
            elif len(line[1]) < 100 and line[1].strip().startswith(block_lines[0]):
                line[-1] = False
            elif len(line[1]) < 100 and line[1].strip().startswith(block_lines[1]):
                line[-1] = False
            elif len(line[1]) < 5:
                line[-1] = False
        filtered_grades = list(filter(filter_lines, pages))
        sec_number = '1'
        xml['sec'][sec_number] = list()
        for line in filtered_grades:
            sections = re.findall('(?:^|\n)([\d]+)\.*([\d]*)\.*([\d]*)[^.\d\w—]([\s\S]*?)(?=\n\d+|\n$)', line[1])
            if len(sections) > 0:
                for sec in sections:
                    if len(sec[3]) > 5:
                        if sec[0] == '' or int(sec[0]) < int(sec_number) or int(sec[0]) - int(sec_number) > 5:
                            if sec[1] == '':
                                xml['sec'][sec_number].append(f"{sec[0]} {sec[3]}")
                            else:
                                if sec[2] == '':
                                    xml['sec'][sec_number].append(f"{sec[0]}.{sec[1]} {sec[3]}")
                                else:
                                    xml['sec'][sec_number].append(f"{sec[0]}.{sec[1]}.{sec[2]} {sec[3]}")
                        else:
                            sec_number = sec[0]
                            if not sec[0] in xml['sec']:
                                xml['sec'][sec[0]] = list()
                            if sec[1] == '':
                                xml['sec'][sec[0]].append(sec[3])
                            else:
                                if sec[2] == '':
                                    xml['sec'][sec[0]].append(f"{sec[0]}.{sec[1]} {sec[3]}")
                                else:
                                    xml['sec'][sec[0]].append(f"{sec[0]}.{sec[1]}.{sec[2]} {sec[3]}")
                    # else:
                    #     xml['sec'][sec_number].append(line[1])
                    #     break
            else:
                xml['sec'][sec_number].append(line[1])
            line[-1] = False


