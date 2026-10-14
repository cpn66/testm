import json
import re
from modules.connect_api import API
from translate import Translator
from modules.default import transliterate, table_text_to_html
from modules.to_niso.mathml import generate_math_ml
from modules.nlp.predict import NLP



if __name__ == '__main__':
    api = API("../settings.ini")
    nlp = NLP("../")
else:
    api = API()
    nlp = NLP()

translator = Translator(to_lang="en", from_lang="ru")

if __name__ == '__main__':
    f = json.load(open(f'../result/result.json', encoding='utf8'))


def find_id_tag(data, name):
    for tag in data:
        if tag['name'] == name:
            return tag['id']
    api.crate_tag(name)
    data = api.get_tags()
    return find_id_tag(data, name)


def find_id_parameter(data, name):
    for tag in data:
        if tag['name'] == name:
            return tag['id']
    api.crate_parameter(name)
    data = api.get_parameters()
    return find_id_parameter(data, name)


def get_index(index):
    index += 1
    return index

# В массиве bBox передаются параметры: 1 - номер страницы начала 2 - координата начала по Y (в %) 3 - координата начала по X (в %) 4 - номер страницы окончания 5 - координата окончания по Y (в %) 6 - координата окончания по X (в %)
def normalize(json):
    default_structure = []
    pic = 0
    index_formula = 0
    predict = 0
    body_order = 0
    data_tags = api.get_tags()
    data_parameters = api.get_parameters()

    def add_tag_structure(tag, tag_attr, value, order, bbox=None, parent=None, parameter=None):
        parent_id = None
        for t in default_structure:
            if t['tagId'] == find_id_tag(data_tags, parent['name']) and t['tagAttr'] == parent['tagAttr']:
                parent_id = t['id']
                break
        parameterId = None
        if parameter:
            parameterId = find_id_parameter(data_parameters, parameter)
        default_structure.append({
            "id": len(default_structure) + 1,
            "name": tag,
            "tagId": find_id_tag(data_tags, tag),
            "tagAttr": tag_attr,
            "parameterId": parameterId,
            "value": value,
            "parentId": parent_id,
            "order": order,
            "bBox": bbox
        })

    add_tag_structure('standard',
                      "xmlns:tbx='urn:iso:std:iso:30042:ed-1' xmlns:svg='http://www.w3.org/2000/svg' xmlns:mml='http://www.w3.org/1998/Math/MathML'",
                      "", 1, None, {"name": None, "tagAttr": None}, "Стандарт")
    add_tag_structure('front', None, "", 1,
                      None, {"name": "standard",
                       "tagAttr": "xmlns:tbx='urn:iso:std:iso:30042:ed-1' xmlns:svg='http://www.w3.org/2000/svg' xmlns:mml='http://www.w3.org/1998/Math/MathML'"},
                      "Вступительная часть")
    add_tag_structure('iso-meta', None, "", 1,
                      None, {"name": "front", "tagAttr": None}, "Метаданные")
    add_tag_structure('title-wrap', "xml:lang='ru'", "", 1,
                      None, {"name": "iso-meta", "tagAttr": None})
    add_tag_structure('title-wrap', "xml:lang='en'", "", 2,
                      None, {"name": "iso-meta", "tagAttr": None})
    add_tag_structure('std-ident', "type='iso-meta'", "", 3,
                      None, {"name": "iso-meta", "tagAttr": None})
    add_tag_structure('originator', None, "", 1,
                      None, {"name": "std-ident", "tagAttr": "type='iso-meta'"})
    add_tag_structure('doc-type', None, "", 2,
                      None, {"name": "std-ident", "tagAttr": "type='iso-meta'"})
    add_tag_structure('edition', None, "", 3,
                      None, {"name": "std-ident", "tagAttr": "type='iso-meta'"})
    add_tag_structure('version', None, "", 4,
                      None, {"name": "std-ident", "tagAttr": "type='iso-meta'"})
    add_tag_structure('content-language', None, "ru", 1,
                      None, {"name": "iso-meta", "tagAttr": None})
    add_tag_structure('custom-meta-group', None, "", 1,
                      None, {"name": "iso-meta", "tagAttr": None})
    add_tag_structure('custom-meta-group', "content-type='gruppa_trebovaniy'", "", 1,
                      None, {"name": "iso-meta", "tagAttr": None}, "Группа требований")
    add_tag_structure('body', None, "", 2,
                      None, {"name": "standard",
                       "tagAttr": "xmlns:tbx='urn:iso:std:iso:30042:ed-1' xmlns:svg='http://www.w3.org/2000/svg' xmlns:mml='http://www.w3.org/1998/Math/MathML'"},
                      "Основное содержание")
    add_tag_structure('back', None, "", 3,
                      None, {"name": "standard",
                       "tagAttr": "xmlns:tbx='urn:iso:std:iso:30042:ed-1' xmlns:svg='http://www.w3.org/2000/svg' xmlns:mml='http://www.w3.org/1998/Math/MathML'"},
                      "Справочный аппарат")

    full_ru = list()
    full_en = list()
    for page in json:
        for block in json[page]:
            if json[page][block]:
                if block == "bbox":
                    continue
                if page == "title":
                    if block == 'intro':
                        full_ru.append(json[page][block])
                        add_tag_structure(block, None, json[page][block], 1,
                                          json[page]['bbox'][block], {"name": "title-wrap", "tagAttr": "xml:lang='ru'"})
                        if json[page][block] and len(json[page][block]) < 200:
                            try:
                                en_text = translator.translate(json[page][block])
                                full_en.append(en_text)
                                add_tag_structure(block, None, en_text, 1,
                                                  None, {"name": "title-wrap", "tagAttr": "xml:lang='en'"})
                            except Exception as ex:
                                print("translator:", ex)

                    if block == 'main':
                        json[page][block], index_formula = generate_math_ml(json[page][block], index_formula)
                        full_ru.append(json[page][block])
                        add_tag_structure(block, None, json[page][block], 2,
                                          json[page]['bbox'][block], {"name": "title-wrap", "tagAttr": "xml:lang='ru'"})
                        if json[page][block] and len(json[page][block]) < 200:
                            try:
                                en_text = translator.translate(json[page][block])
                                full_en.append(en_text)
                                add_tag_structure(block, None, en_text, 2,
                                                  None, {"name": "title-wrap", "tagAttr": "xml:lang='en'"})
                            except Exception as ex:
                                print("translator:", ex)

                    if block == 'compl':
                        json[page][block], index_formula = generate_math_ml(json[page][block], index_formula)
                        full_ru.append(json[page][block])
                        add_tag_structure(block, None, json[page][block], 3,
                                          json[page]['bbox'][block], {"name": "title-wrap", "tagAttr": "xml:lang='ru'"})
                        if json[page][block] and len(json[page][block]) < 200:
                            try:
                                en_text = translator.translate(json[page][block])
                                full_en.append(en_text)
                                add_tag_structure(block, None, en_text, 3,
                                                  None, {"name": "title-wrap", "tagAttr": "xml:lang='en'"})
                            except Exception as ex:
                                print("translator:", ex)
                    if block == 'box-gost':
                        add_tag_structure('std-ref', "type='dated'", json[page][block], 1,
                                          json[page]['bbox'][block], {"name": "iso-meta", "tagAttr": None})
                        add_tag_structure('std-ref', "type='short'", json[page][block], 1,
                                          json[page]['bbox'][block], {"name": "iso-meta", "tagAttr": None})
                        add_tag_structure('doc-ref', None, json[page][block], 1,
                                          json[page]['bbox'][block], {"name": "iso-meta", "tagAttr": None})
                        match = re.search(r"(\d+.+)[—-]\d+", json[page][block])
                        if match and match.groups()[0]:
                            add_tag_structure('doc-number', None, match.groups()[0], 3,
                                              None, {"name": "std-ident", "tagAttr": "type='iso-meta'"})
                            add_tag_structure('std-ref', "type='undated'",
                                              json[page]['ontological-type'] + " " + match.groups()[0], 1,
                                              None, {"name": "iso-meta", "tagAttr": None})
                    if block == 'comm-ref':
                        add_tag_structure(block, None, json[page][block], 1,
                                          json[page]['bbox'][block], {"name": "iso-meta", "tagAttr": None})
                    if block == 'custom-meta':
                        add_tag_structure('custom-meta', "type='Type'", "", 1,
                                          None, {"name": "custom-meta-group", "tagAttr": None})
                        add_tag_structure('meta-name', None, "Type", 1,
                                          None, {"name": "custom-meta", "tagAttr": "type='Type'"})
                        add_tag_structure('meta-value', None, json[page][block], 1,
                                          json[page]['bbox'][block], {"name": "custom-meta", "tagAttr": "type='Type'"})
                if page == "foreword":
                    if json[page][block] == "<p></p>":
                        continue
                    json[page][block], index_formula = generate_math_ml(json[page][block], index_formula)
                    if block == "notes":
                        add_tag_structure('notes', None, json[page][block], 1,
                                          json[page]['bbox'][block], {"name": "front", "tagAttr": None}, "Примечания")
                    if block == "foreword":
                        match_table = re.findall("(table[^<>]*:::)", json[page][block])
                        for table in match_table:
                            text = table_text_to_html(table)
                            json[page][block] = re.sub("table[^<>]*:::", text, json[page][block], 1)
                        add_tag_structure('sec', "id='sec_foreword' sec-type='foreword'", "", 1,
                                          json[page]['bbox'][block], {"name": "front", "tagAttr": None}, "Предисловие")
                        json[page][block] = json[page][block].replace('<p></p>', '')
                        add_tag_structure('title', None, "Предисловие", 1,
                                          None, {"name": "sec", "tagAttr": "id='sec_foreword' sec-type='foreword'"},
                                          "Заголовок")
                        add_tag_structure('p', None, json[page][block], 2,
                                          None, {"name": "sec", "tagAttr": "id='sec_foreword' sec-type='foreword'"}, "Текст")

                    if block == "doc-ident":
                        match = re.search(r"РАЗРАБОТАН([\s\S]+?)(<\/p>)|$", json[page][block])
                        if match and match.groups()[0]:
                            text = re.sub("<br></br>", " ", match.groups()[0])
                            add_tag_structure('doc-ident', None, "", 1,
                                              None, {"name": "iso-meta", "tagAttr": None})
                            add_tag_structure('sdo', None, text, 1,
                                              json[page]['bbox'][block], {"name": "doc-ident", "tagAttr": None})
                            add_tag_structure('proj-id', None, "", 1,
                                              None, {"name": "doc-ident", "tagAttr": None})
                            add_tag_structure('language', None, "ru", 1,
                                              None, {"name": "doc-ident", "tagAttr": None})
                            add_tag_structure('release-version', None, "", 1,
                                              None, {"name": "doc-ident", "tagAttr": None})
                    if block == "secretariat":
                        match = re.search(r"ВНЕСЕН([\s\S]+?)(<\/p>)|$", json[page][block])
                        if match and match.groups()[0]:
                            text = re.sub("<br></br>", " ", match.groups()[0])
                            add_tag_structure('secretariat', None, text, 1,
                                              json[page]['bbox'][block], {"name": "iso-meta", "tagAttr": None})
                if page == "content":
                    if block == "implementation_text":
                        match_p = re.findall("<p>(.*?)</p>", json[page][block])
                        for text in match_p:
                            len_text = len(text)
                            if len_text < 2:
                                continue
                            if len_text > 4 and text[0:3] == "img":
                                pic += 1
                                body_order += 1
                                add_tag_structure('fig', f"id='fig_{pic}'", "", body_order,
                                                  None, {"name": "body", "tagAttr": None}, f"Рисунок")
                                [img] = re.findall("name='(.*?)'", text)
                                add_tag_structure('graphic',
                                                  f"xmlns:ns0='http://www.w3.org/1999/xlink' ns0:href='/graphics/{img}'",
                                                  "", 1,
                                                  None, {"name": "fig", "tagAttr": f"id='fig_{pic}'"})
                                continue
                            if len_text > 5 and text[0:5] == "table":
                                body_order += 1
                                text = table_text_to_html(text)
                                add_tag_structure('p', None, text, body_order,
                                                  None, {"name": "body", "tagAttr": None}, "Текст")
                                continue
                            if len_text > 10 and nlp.predict(text):
                                predict += 1
                                add_tag_structure('custom-meta', f"type='trebovaniye' id='cm_trebovaniye_{predict}'",
                                                  "", predict,
                                                  None, {"name": "custom-meta-group",
                                                         "tagAttr": "content-type='gruppa_trebovaniy'"}, "Требование")
                                add_tag_structure('meta-name', None, "Введение", 1,
                                                  None, {"name": "custom-meta",
                                                         "tagAttr": f"type='trebovaniye' id='cm_trebovaniye_{predict}'"})
                                add_tag_structure('meta-value', f"id='mv_trebovaniye_{predict}'",
                                                  f"<xref ref-type='trebovaniye' rid='trebovaniye_{predict}'></xref>",
                                                  2,
                                                  None, {"name": "custom-meta",
                                                         "tagAttr": f"type='trebovaniye' id='cm_trebovaniye_{predict}'"})
                                add_tag_structure('p', f"id='trebovaniye_{predict}'", "<p>" + text + "</p>", body_order,
                                                  None, {"name": "body", "tagAttr": None}, "Текст")
                            else:
                                body_order += 1
                                add_tag_structure('p', None, "<p>" + text + "</p>", body_order,
                                              None, {"name": "body", "tagAttr": None}, "Текст")
                    if block == "implementation" and json['title']['ontological-type']:
                        match = re.search(r"(\d{4}[-—]\d{2}[-—]\d{2})", json[page][block])
                        add_tag_structure('nat-meta', f"originator='{json['title']['ontological-type']}'", "", 1,
                                          None, {"name": "front", "tagAttr": None}, "Метаданные")
                        add_tag_structure('title-wrap', "type='nat-meta'", "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('main', None, "", 1,
                                          None, {"name": "title-wrap",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('full', None, "", 1,
                                          None, {"name": "title-wrap",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('doc-ident', "type='nat-meta'", "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('sdo', None, "", 1,
                                          None, {"name": "doc-ident",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('proj-id', None, "", 1,
                                          None, {"name": "doc-ident",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('language', None, "ru", 1,
                                          None, {"name": "doc-ident",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('release-version', None, "", 1,
                                          None, {"name": "doc-ident",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('std-ident', "type='nat-meta'", "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('originator', None, "", 1,
                                          None, {"name": "std-ident",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('doc-type', None, "", 1,
                                          None, {"name": "std-ident",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('doc-number', None, "", 1,
                                          None, {"name": "std-ident",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('edition', None, "", 1,
                                          None, {"name": "std-ident",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('version', None, "", 1,
                                          None, {"name": "std-ident",
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('content-language', "", "ru", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('std-ref', "type='dated'", "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('std-ref', "type='undated'", "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('doc-ref', None, "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('release-date', None, "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('meta-date', "type='ratification'", "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        if match and match.groups()[0]:
                            add_tag_structure('meta-date', "type='implementation'", match.groups()[0], 1,
                                              None, {"name": "nat-meta",
                                                     "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        else:
                            add_tag_structure('meta-date', "type='implementation'", "", 1,
                                              None, {"name": "nat-meta",
                                                     "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('meta-date', "type='termination'", "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('comm-ref', None, "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('secretariat', None, "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('ics', None, "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('ics', None, "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('permissions', "type='nat-meta'", "", 1,
                                          None, {"name": "nat-meta",
                                                 "tagAttr": f"originator='{json['title']['ontological-type']}'"})
                        add_tag_structure('copyright-statement', None, "Все права сохраняются", 1,
                                          None, {"name": 'permissions',
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('copyright-year', None, "", 1,
                                          None, {"name": 'permissions',
                                                 "tagAttr": "type='nat-meta'"})
                        add_tag_structure('copyright-holder', None, "", 1,
                                          None, {"name": 'permissions',
                                                 "tagAttr": "type='nat-meta'"})
                    if block == "sec":
                        for sec in json[page][block]:
                            bbox = json[page][block][sec][1]
                            json[page][block][sec] = json[page][block][sec][0]
                            json[page][block][sec], index_formula = generate_math_ml(json[page][block][sec],
                                                                                     index_formula)
                            sec_type = None
                            sec_name = "Раздел"
                            attr = "id='sec_" + str(sec) + "'"
                            if json[page][block][sec].lower().startswith("<p>область применения"):
                                sec_type = "scope"
                                sec_name = "Область применения"
                            elif json[page][block][sec].lower().startswith("<p>нормативные ссылки"):
                                sec_type = "norm-refs"
                                sec_name = "Нормативные ссылки"
                            elif json[page][block][sec].lower().startswith("<p>термины и определения"):
                                sec_type = "terms"
                                sec_name = "Термины и определения"
                            else:
                                find = re.findall("^<p>(.*?)<\/p>", json[page][block][sec])
                                if find:
                                    number = re.findall("^(\d+)\.(\d+)", find[0])
                                    if not number:
                                        # print(find[0])
                                        sec_name = find[0]
                                    else:
                                        # print(number)
                                        sec_name = "Раздел "+number[0][0]
                            if sec_type:
                                attr += " sec-type='" + sec_type + "'"
                            body_order += 1
                            add_tag_structure('sec', attr, '', body_order,
                                              bbox, {"name": "body", "tagAttr": None}, "Раздел")
                            add_tag_structure('label', None, sec, 1,
                                              None, {"name": "sec", "tagAttr": attr}, "Номер заголовка")
                            json[page][block][sec] = json[page][block][sec].replace(f'<p>{sec_name}</p>', '', 1)
                            add_tag_structure('title', None, sec_name, 2,
                                                None, {"name": "sec", "tagAttr": attr}, "Заголовок")
                            if sec_type == "terms":
                                terms = re.findall('(?:<p>)([\d.]+)((?:<\/p>|\s).+?)(?=<p>[\d.])',
                                                   json[page][block][sec])
                                json[page][block][sec] = re.sub('(?:<p>)([\d.]+)((?:<\/p>|\s).+?)(?=<p>[\d.])', '',
                                                                json[page][block][sec])
                                for term in terms:
                                    add_tag_structure('term-sec', f"id='sec_{term[0]}'", '', 6,
                                                      None, {"name": "sec", "tagAttr": attr}, "Термин")
                                    add_tag_structure('label', None, term[0], 1,
                                                      None, {"name": "term-sec", "tagAttr": f"id='sec_{term[0]}'"},
                                                      "Номер заголовка")
                                    add_tag_structure('tbx:termEntry', f"id='sec_{term[0]}'", "", 2,
                                                      None, {"name": "term-sec", "tagAttr": f"id='sec_{term[0]}'"})
                                    add_tag_structure('tbx:langSet', f"id='sec_{term[0]}' xml:lang='ru'", "", 3,
                                                      None, {"name": 'tbx:termEntry', "tagAttr": f"id='sec_{term[0]}'"})
                                    text_split = term[1].split(":")
                                    if len(text_split) > 1:
                                        definition = "<p>" + ":".join(text_split[1:])
                                        match_table = re.findall("(table[^<>]*:::)", definition)
                                        for table in match_table:
                                            text = table_text_to_html(table)
                                            definition = re.sub("table[^<>]*:::", text, definition, 1)
                                        add_tag_structure('tbx:definition', '', definition, 1,
                                                          None, {"name": 'tbx:langSet',
                                                           "tagAttr": f"id='sec_{term[0]}' xml:lang='ru'"})
                                    if len(text_split) > 0:
                                        add_tag_structure('tbx:tig', f"id='sec_{term[0]}'", "", 2,
                                                          None, {"name": 'tbx:langSet',
                                                           "tagAttr": f"id='sec_{term[0]}' xml:lang='ru'"})
                                        add_tag_structure('tbx:term', None, re.sub('<.*?>', ' ', text_split[0]), 1,
                                                          None, {"name": 'tbx:tig', "tagAttr": f"id='sec_{term[0]}'"})
                            match_p = re.findall("<p>(.*?)</p>", json[page][block][sec])
                            order = 2
                            for text in match_p:
                                len_text = len(text)
                                if len_text < 2:
                                    continue
                                order += 1
                                if len_text > 4 and text[0:3] == "img":
                                    pic += 1
                                    add_tag_structure('fig', f"id='fig_{pic}'", "", order,
                                                      None, {"name": "sec", "tagAttr": attr}, f"Рисунок")
                                    [img] = re.findall("name='(.*?)'", text)
                                    add_tag_structure('graphic',
                                                      f"xmlns:ns0='http://www.w3.org/1999/xlink' ns0:href='/graphics/{img}'",
                                                      "", 1,
                                                      None, {"name": "fig", "tagAttr": f"id='fig_{pic}'"})
                                    continue
                                if len_text > 5 and text[0:5] == "table":
                                    text = table_text_to_html(text)
                                    add_tag_structure('p', None, text, order,
                                                      None, {"name": "sec", "tagAttr": attr}, "Текст")
                                    continue
                                if len_text > 10 and nlp.predict(text):
                                    predict += 1
                                    add_tag_structure('custom-meta', f"type='trebovaniye' id='cm_trebovaniye_{predict}'", "", predict,
                                                      None, {"name": "custom-meta-group", "tagAttr": "content-type='gruppa_trebovaniy'"}, "Требование")
                                    add_tag_structure('meta-name', None, sec_name, 1,
                                                      None, {"name": "custom-meta", "tagAttr": f"type='trebovaniye' id='cm_trebovaniye_{predict}'"})
                                    add_tag_structure('meta-value', f"id='mv_trebovaniye_{predict}'",
                                                      f"<xref ref-type='trebovaniye' rid='trebovaniye_{predict}'></xref>", 2,
                                                      None, {"name": "custom-meta", "tagAttr": f"type='trebovaniye' id='cm_trebovaniye_{predict}'"})
                                    add_tag_structure('p', f"id='trebovaniye_{predict}'", "<p>"+text+"</p>", order,
                                                      None, {"name": "sec", "tagAttr": attr}, "Текст")
                                else:
                                    add_tag_structure('p', None, "<p>"+text+"</p>", order,
                                                      None, {"name": "sec", "tagAttr": attr}, "Текст")


                if page == "application":
                    add_tag_structure('app-group', None, "", 1,
                                      None, {"name": "back", "tagAttr": None}, "Группа приложений")
                    if block == "applications":
                        app_order = 1
                        parent = {
                            "tag": "sec",
                            "atr": None
                        }
                        for app in json[page][block]:
                            prefix = transliterate(app["label"].split(" ")[1].lower())
                            add_tag_structure('app', f"id='app_{prefix}' content-type='norm-annex'", "", app_order,
                                              None, {"name": "app-group", "tagAttr": None}, "Приложение")
                            app_order += 1
                            add_tag_structure('label', None, app["label"], 1,
                                              None, {"name": "app",
                                               "tagAttr": f"id='app_{prefix}' content-type='norm-annex'"},
                                              "Номер заголовка")
                            add_tag_structure('annex-type', None, app["annex-type"], 1,
                                              None, {"name": "app",
                                               "tagAttr": f"id='app_{prefix}' content-type='norm-annex'"})
                            for sec in app["body"][0]:
                                sec["body"], index_formula = generate_math_ml(sec["body"], index_formula)
                                if len(sec["body"]) > 0:
                                    match_p = re.findall("<p>(.*?)</p>", sec["body"])
                                    if sec['number']:
                                        parent = {
                                            "tag": "sec",
                                            "atr": f"id='sec_{transliterate(sec['number'].lower())}'"
                                        }
                                        add_tag_structure('sec', f"id='sec_{transliterate(sec['number'].lower())}'",
                                                          "", 1, app["body"][1], {"name": "app",
                                                                                  "tagAttr": f"id='app_{prefix}' content-type='norm-annex'"},
                                                          "Раздел")
                                        add_tag_structure('label', None,
                                                          sec['number'], 1, None, {"name": "sec",
                                                                                   "tagAttr": f"id='sec_{transliterate(sec['number'].lower())}'"},
                                                          "Номер заголовка")
                                        add_tag_structure('title', None,
                                                          match_p[0], 2, None, {"name": "sec",
                                                                                 "tagAttr": f"id='sec_{transliterate(sec['number'].lower())}'"},
                                                          "Заголовок")
                                        match_p = match_p[1::]
                                    order = 2
                                    for text in match_p:
                                        if parent["atr"]:
                                            tag = parent["tag"]
                                            attr = parent["atr"]
                                        else:
                                            tag = "app"
                                            attr = f"id='app_{prefix}' content-type='norm-annex'"
                                        len_text = len(text)
                                        if len_text < 2:
                                            continue
                                        order += 1
                                        if len_text > 4 and text[0:3] == "img":
                                            pic += 1
                                            add_tag_structure('fig', f"id='fig_{pic}'", "", order,
                                                              None, {"name": tag, "tagAttr": attr}, f"Рисунок")
                                            [img] = re.findall("name='(.*?)'", text)
                                            add_tag_structure('graphic',
                                                              f"xmlns:ns0='http://www.w3.org/1999/xlink' ns0:href='/graphics/{img}'",
                                                              "", 1,
                                                              None, {"name": "fig", "tagAttr": f"id='fig_{pic}'"})
                                            continue
                                        if len_text > 5 and text[0:5] == "table":
                                            text = table_text_to_html(text)
                                            add_tag_structure('p', None, text, order,
                                                              None, {"name": tag, "tagAttr": attr}, "Текст")
                                            continue
                                        if len_text > 10 and nlp.predict(text):
                                            predict += 1
                                            add_tag_structure('custom-meta',
                                                              f"type='trebovaniye' id='cm_trebovaniye_{predict}'", "",
                                                              predict,
                                                              None, {"name": "custom-meta-group",
                                                                     "tagAttr": "content-type='gruppa_trebovaniy'"},
                                                              "Требование")
                                            add_tag_structure('meta-name', None, app["label"], 1,
                                                              None, {"name": "custom-meta",
                                                                     "tagAttr": f"type='trebovaniye' id='cm_trebovaniye_{predict}'"})
                                            add_tag_structure('meta-value', f"id='mv_trebovaniye_{predict}'",
                                                              f"<xref ref-type='trebovaniye' rid='trebovaniye_{predict}'></xref>",
                                                              2,
                                                              None, {"name": "custom-meta",
                                                                     "tagAttr": f"type='trebovaniye' id='cm_trebovaniye_{predict}'"})
                                            add_tag_structure('p', f"id='trebovaniye_{predict}'",
                                                              "<p>" + text + "</p>", order,
                                                              None, {"name": tag,
                                                                     "tagAttr": attr}, "Текст")
                                        else:
                                            add_tag_structure('p', None, "<p>" + text + "</p>", order,
                                                                  None, {"name": tag,
                                                                         "tagAttr": attr}, "Текст")



                                # if len(sec["body"]) > 0 and sec['number']:
                                #     match_table = re.findall("(table[^<>]*:::)", sec['body'])
                                #     for table in match_table:
                                #         text = table_text_to_html(table)
                                #         sec['body'] = re.sub("table[^<>]*:::", text, sec['body'], 1)
                                #     match_img = re.findall("img\[name='([^\]]*)']([\s\S]*?)", sec['body'])
                                #     # sec['body'] = re.sub("img\[name='([^\]]*)']([\s\S]*?)", '', sec['body'])
                                #     if sec['type'] == "header":
                                #         parent = {
                                #             "tag": "sec",
                                #             "atr": f"id='sec_{transliterate(sec['number'].lower())}'"
                                #         }
                                #         add_tag_structure('sec', f"id='sec_{transliterate(sec['number'].lower())}'",
                                #                           "", 1, app["body"][1], {"name": "app",
                                #                                   "tagAttr": f"id='app_{prefix}' content-type='norm-annex'"},
                                #                           "Раздел")
                                #         add_tag_structure('label', None,
                                #                           sec['number'], 1, None, {"name": "sec",
                                #                                              "tagAttr": f"id='sec_{transliterate(sec['number'].lower())}'"},
                                #                           "Номер заголовка")
                                #         add_tag_structure('title', None,
                                #                           sec['body'], 1, None, {"name": "sec",
                                #                                            "tagAttr": f"id='sec_{transliterate(sec['number'].lower())}'"},
                                #                           "Заголовок")
                                #     else:
                                #         if parent["atr"] and parent["tag"] == "sec":
                                #             add_tag_structure('sec', f"id='p_{transliterate(sec['number'].lower())}'",
                                #                               "", 1, None, {"name": parent["tag"],
                                #                                                "tagAttr": parent["atr"]}, "Текст")
                                #             parent = {
                                #                 "tag": "sec",
                                #                 "atr": f"id='p_{transliterate(sec['number'].lower())}'"
                                #             }
                                #         else:
                                #             parent = {
                                #                 "tag": "sec",
                                #                 "atr": f"id='p_{transliterate(sec['number'].lower())}'"
                                #             }
                                #             add_tag_structure('sec', f"id='p_{transliterate(sec['number'].lower())}'",
                                #                               "", 1, None, {"name": "app",
                                #                                                "tagAttr": f"id='app_{prefix}' content-type='norm-annex'"},
                                #                               "Текст")
                                #     order = 3
                                #     for img in match_img:
                                #         text = sec['body'].split(f"img[name='{img[0]}']")
                                #         add_tag_structure('p', "",
                                #                           text[0], order, None, {"name": parent["tag"],
                                #                                            "tagAttr": parent["atr"]},
                                #                           "Текст")
                                #         order += 1
                                #         if len(text) > 1:
                                #             sec['body'] = text[1]
                                #         else:
                                #             sec['body'] = ""
                                #         description_img = re.sub('<inline-formula>[\s\S]*</inline-formula>', "",
                                #                                  img[1])
                                #         name = description_img.split(" ")
                                #         if len(name) == 1:
                                #             prefix_img = "_".join(img[0].split(".")[0].split("-")[1::])
                                #         else:
                                #             prefix_img = transliterate(name[1].lower())
                                #         add_tag_structure('fig', f"id='fig_{prefix_img}'", "", order,
                                #                           None, {"name": parent["tag"],
                                #                            "tagAttr": parent["atr"]}, "Рисунок")
                                #         order += 1
                                #         if len(name[0:2]) > 0:
                                #             add_tag_structure('label', "", " ".join(name[0:2]), 2,
                                #                               None, {"name": "fig", "tagAttr": f"id='fig_{prefix_img}'"},
                                #                               "Номер заголовка")
                                #         if len(name[2:]) > 0:
                                #             add_tag_structure('caption', f"id='fig_{prefix_img}'", "", 3,
                                #                               None, {"name": "fig", "tagAttr": f"id='fig_{prefix_img}'"})
                                #             add_tag_structure('title', "", " ".join(name[2:]), 1,
                                #                               None, {"name": "caption", "tagAttr": f"id='fig_{prefix_img}'"},
                                #                               "Заголовок")
                                #         add_tag_structure('graphic',
                                #                           f"xmlns:ns0='http://www.w3.org/1999/xlink' ns0:href='/graphics/{img[0]}'",
                                #                           "", 1,
                                #                           None, {"name": "fig", "tagAttr": f"id='fig_{prefix_img}'"})
                                #     add_tag_structure('p', f"id='p_{prefix}'",
                                #                       sec['body'], order, None, {"name": parent["tag"],
                                #                                            "tagAttr": parent["atr"]},
                                #                       "Текст")
                                # else:
                                #     match_table = re.findall("(table[^<>]*:::)", sec['body'])
                                #     for table in match_table:
                                #         text = table_text_to_html(table)
                                #         sec['body'] = re.sub("table[^<>]*:::", text, sec['body'], 1)
                                #     match_img = re.findall("img\[name='([^\]]*)']([\s\S]*?)", sec['body'])
                                #     order = 3
                                #     for index, img in enumerate(match_img):
                                #         text = sec['body'].split(f"<p>img[name='{img[0]}']</p>")
                                #         add_tag_structure('p', f"id='p_{prefix}'",
                                #                           text[0], order, None, {"name": "app",
                                #                                            "tagAttr": f"id='app_{prefix}' content-type='norm-annex'"},
                                #                           "Текст")
                                #         order += 1
                                #         if len(text) > 1:
                                #             sec['body'] = text[1]
                                #         else:
                                #             sec['body'] = ""
                                #         description_img = re.sub('<inline-formula>[\s\S]*</inline-formula>', "",
                                #                                  img[1])
                                #         name = description_img.split(" ")
                                #         if len(name) == 1:
                                #             prefix_img = prefix+str(index)
                                #         else:
                                #             prefix_img = transliterate(name[1].lower())
                                #         add_tag_structure('fig', f"id='fig_{prefix_img}'", "", order,
                                #                           None, {"name": "p",
                                #                            "tagAttr": f"id='p_{prefix}'"}, "Рисунок")
                                #         order += 1
                                #         if len(name[0:2]) > 0:
                                #             add_tag_structure('label', "", " ".join(name[0:2]), 2,
                                #                               None, {"name": "fig", "tagAttr": f"id='fig_{prefix_img}'"},
                                #                               "Номер заголовка")
                                #         if len(name[2:]) > 0:
                                #             add_tag_structure('caption', f"id='fig_caption_{prefix_img}'", "", 3,
                                #                               None, {"name": "fig", "tagAttr": f"id='fig_{prefix_img}'"})
                                #             add_tag_structure('title', "", " ".join(name[2:]), 1,
                                #                               None, {"name": "caption",
                                #                                "tagAttr": f"id='fig_caption_{prefix_img}'"},
                                #                               "Заголовок")
                                #         add_tag_structure('graphic',
                                #                           f"xmlns:ns0='http://www.w3.org/1999/xlink' ns0:href='/graphics/{img[0]}'",
                                #                           "", 1,
                                #                           None, {"name": "fig", "tagAttr": f"id='fig_{prefix_img}'"})
                                #     add_tag_structure('p', f"id='p_{prefix}'",
                                #                       sec['body'], order, None, {"name": "app",
                                #                                                "tagAttr": f"id='app_{prefix}' content-type='norm-annex'"},
                                #                       "Текст")

                if page == "keywords":

                    if block == "keywords":
                        match = re.search(r"Ключевые слова([\s\S]+?)$", json[page][block])
                        if match and match.groups()[0]:
                            add_tag_structure('custom-meta', "type='Keywords'", "", 1,
                                              json[page]['bbox'][block], {"name": "custom-meta-group", "tagAttr": None})
                            add_tag_structure('meta-name', None, "Keywords", 1,
                                              None, {"name": "custom-meta", "tagAttr": "type='Keywords'"})
                            add_tag_structure('meta-value', None, re.sub(":", "", match.groups()[0]),
                                              1, None, {"name": "custom-meta", "tagAttr": "type='Keywords'"})
                    if block == "type_documents":
                        json[page][block] = re.sub('math:::.*end:::', '', json[page][block])
                        match = re.findall('([^\d]+?)\s*([0-9\.\-—:+\s\(\)]+)\s?', json[page][block])
                        order = 0
                        for index, type_documents in enumerate(match):
                            split = type_documents[1].split(" ")
                            for value in split:
                                if value:
                                    order += 1
                                    add_tag_structure('custom-meta', f"type='{type_documents[0]}' id='classifier{order}'", "", order,
                                                      json[page]['bbox'][block], {"name": "custom-meta-group", "tagAttr": None},"Классификатор")
                                    add_tag_structure('meta-name', None, type_documents[0], 1,
                                                      None, {"name": "custom-meta", "tagAttr": f"type='{type_documents[0]}' id='classifier{order}'"})
                                    add_tag_structure('meta-value', None, value, 2,
                                                      None, {"name": "custom-meta", "tagAttr": f"type='{type_documents[0]}' id='classifier{order}'"})
                if page == "bibliography":
                    if block == "std":
                        if '1' in json[page][block] and json[page][block]['1'][0] == "":
                            continue
                    add_tag_structure('ref-list', "content-type='bibl' id='sec_bibl'", "", 1,
                                      None, {"name": "back", "tagAttr": None}, "Библиография")
                    if block == "title":
                        add_tag_structure('title', None, json[page][block], 1,
                                          json[page]['bbox'][block], {"name": 'ref-list', "tagAttr": "content-type='bibl' id='sec_bibl'"},
                                          "Заголовок")
                    if block == "std":
                        for std in json[page][block]:
                            bbox = json[page][block][std][1]
                            json[page][block][std] = json[page][block][std][0]
                            json[page][block][std], index_formula = generate_math_ml(json[page][block][std],
                                                                                     index_formula)
                            add_tag_structure('ref', f"id='biblref_{std}'", "", 1,
                                              bbox, {"name": 'ref-list', "tagAttr": "content-type='bibl' id='sec_bibl'"},
                                              "Ссылка")
                            add_tag_structure('label', None, std, 1,
                                              None, {"name": 'ref', "tagAttr": f"id='biblref_{std}'"}, "Номер заголовка")
                            add_tag_structure('std', "type='dated' xml:lang='ru'",
                                              re.sub(r"[\[\(\|](\d+)[\]\)\|]", "", json[page][block][std]), 1,
                                              None, {"name": 'ref', "tagAttr": f"id='biblref_{std}'"})

    if len(full_ru) > 0:
        add_tag_structure("full", None, '. '.join(full_ru), 4,
                          None, {"name": "title-wrap", "tagAttr": "xml:lang='ru'"})
    if len(full_en) > 0:
        add_tag_structure("full", None, ". ".join(full_en), 4,
                          None, {"name": "title-wrap", "tagAttr": "xml:lang='en'"})
    # print(default_structure)
    for block in default_structure:
        if re.search(">&<", block["value"]):
            block["value"] = re.sub(">&<", ">&amp;<", block["value"])
    return default_structure


if __name__ == '__main__':
    print(normalize(f))
