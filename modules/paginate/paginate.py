import json
import configparser
from modules.default import lines_to_html, table_to_text

config = configparser.ConfigParser()
if __name__ != '__main__':
    from ocrToPdf.octToJson import send_json, send_status
    from modules.document_type import get_template
    config.read("settings.ini")
    settings_dir = config['files']['dir']
else:
    def get_template(document_type):
        return "gostr.json"
    settings_dir = "../../files/settings"


def group_pages(pages):  # Объединение страниц в одну
    b = list()
    for idx, page in enumerate(pages):
        for line in page:
            line[0][0][1] += idx * 4000
            line[0][1][1] += idx * 4000
            line[0][2][1] += idx * 4000
            line[0][3][1] += idx * 4000
            b.append(line)
    return b


class Paginate:
    normalize = {
        'title': {
            'box-gost': 'line-to-text',
            'ontological-type': 'text',
            'comm-ref': 'lines-to-text',
            'custom-meta': 'lines-to-text',
            'main': 'lines-to-text',
            'intro': 'lines-to-text',
            'compl': 'lines-to-text',
        },
        'foreword': {
            'foreword': 'lines-to-html',
            'notes': 'lines-to-html',
            'permissions': 'lines-to-text',
            'doc-ident': 'line-to-text',
            'secretariat': 'line-to-text'
        },
        'introduction': {
            'introduction': 'lines-to-html',
            'notes': 'lines-to-html'
        },
        'content': {
            'implementation': 'line-to-text',
            'implementation_text': 'lines-to-html',
            'dated': 'lines-to-text',
            'sec': 'dict-to-html',
        },
        'keywords': {
            'keywords': 'line-to-text',
            'type_documents': 'lines-to-text',
        },
        'bibliography': {
            "title": 'line-to-text',
            "std": 'dict-to-html',
        },
        'application': {
            "label": 'line-to-text',
            "annex-type": 'line-to-text',
            "title": 'line-to-text',
        }
    }

    def __init__(self):
        self.xml = {
            'title': {
                'box-gost': list(),
                'ontological-type': None,
                'comm-ref': list(),
                'custom-meta': list(),
                'main': list(),
                'intro': list(),
                'compl': list(),
                'bbox': dict()
            },
            'foreword': {
                'foreword': None,
                'notes': list(),
                'permissions': list(),
                'doc-ident': list(),
                'secretariat': list(),
                'bbox': dict()
            },
            'introduction': {
                'introduction': None,
                'notes': list(),
                'bbox': dict()
            },
            'content': {
                'implementation': None,
                'implementation_text': list(),
                'dated': list(),
                'sec': dict(),
                'bbox': dict()
            },
            "application": {
                "applications": list(),
                'bbox': dict()
            },
            'keywords': {
                'keywords': None,
                'type_documents': list(),
                'bbox': dict()
            },
            'bibliography': {
                "title": None,
                "std": dict(),
                'bbox': dict()

            }
        }

    def text_to_page(self, result, document_id, send, mlProcessingId, document_type, pages_size=[]):
        if not send and __name__ != '__main__':
            with open("result/result_page.json", "w", encoding='utf8') as file:
                file.write(json.dumps([result, document_id, send, mlProcessingId, document_type, pages_size], ensure_ascii=False))
        if document_type['year']:
            if (len(document_type['year']) == 2 and int(document_type['year']) < 93) or (
                    len(document_type['year']) == 4 and int(document_type['year']) < 1993):
                from modules.paginate.type.defaultSSSR import TypePageDefaultSSSR
                paginate_type = TypePageDefaultSSSR(document_type["name"], settings_dir + "/" + get_template("ГОСТ (СССР)"))
                document_type["name"] = "ГОСТ (СССР)"
            else:
                if document_type["name"] == "ГОСТ" or document_type["name"] == "ГОСТ (СССР)":
                    document_type["name"] = "ГОСТ"
                    from modules.paginate.type.new import TypePageNew
                    paginate_type = TypePageNew(settings_dir + "/" + get_template("ГОСТ"))
                elif document_type["name"] == "ПНСТ":
                    from modules.paginate.type.new import TypePageNew
                    paginate_type = TypePageNew(settings_dir + "/" + get_template("ПНСТ"))
                elif document_type["name"] == "РМГ":
                    from modules.paginate.type.new import TypePageNew
                    paginate_type = TypePageNew(settings_dir + "/" + get_template("РМГ"))
                elif document_type["name"] == "ПР":
                    from modules.paginate.type.new import TypePageNew
                    paginate_type = TypePageNew(settings_dir + "/" + get_template("ПР"))
                elif document_type["name"] == "ПМГ":
                    from modules.paginate.type.new import TypePageNew
                    paginate_type = TypePageNew(settings_dir + "/" + get_template("ПМГ"))
                elif document_type["name"] in ["СП", "CП", "CN", "СN"] or document_type["name"] == "Своды правил":
                    from modules.paginate.type.new import TypePageNew
                    paginate_type = TypePageNew(settings_dir + "/" + get_template("Своды правил"))
                    document_type["name"] = "Своды правил"
                elif (document_type["name"] == "ГОСТ Р" or document_type["name"] == "ГОСТ-Р" or
                      document_type["name"] == "ГОСТР"):
                    from modules.paginate.type.new import TypePageNew
                    paginate_type = TypePageNew(settings_dir + "/" + get_template("ГОСТ Р"))
                elif document_type["name"] == "Р":
                    from modules.paginate.type.r import TypePageR
                    paginate_type = TypePageR(settings_dir + "/" + get_template("Р"))
                else:
                    from modules.paginate.type.default import TypePageDefault
                    print(document_type["name"])
                    paginate_type = TypePageDefault(document_type["name"], settings_dir + "/" + get_template("Не определен"))

        pages = result
        document_blocks = {
            'title': list(),
            'foreword': list(),
            'content-list': list(),
            'introduction': list(),
            'content': list(),
            'application': list(),
            'bibliography': list(),
            'keywords': list(),
            'end': list()
        }
        # Поиск страниц
        page_type = paginate_type.config["sequence_of_sheets"][0]
        for index, page in enumerate(pages):
            for line in page:
                line.append(index)
                line.append(pages_size[index])
            for line in page:
                if line[2] == "table":
                    line[1] = table_to_text(line[1])
                if line[2] == "formula" or line[2] == "image":
                    line[1] = line[1] + "\n"
            if index != 0:
                for line in page[0:20]:  # ищу только в первых 10 блоках, заголовках
                    if line[2] == 'text':
                        text = line[1].strip()
                    else:
                        text = ""
                    # print(text)
                    find, page_type = paginate_type.getPages(text, page_type)
                    if find:
                        break
            document_blocks[page_type].append(page)
        # for page_type in document_blocks:
        #     print(page_type, document_blocks[page_type])
        # try:
        paginate_type.parse_title(group_pages(document_blocks['title']), self.xml['title'])
        # print('title', self.xml['title'])
        paginate_type.parse_foreword(group_pages(document_blocks['foreword']), self.xml['foreword'],
                                     self.xml["title"]["ontological-type"])
        # print(self.xml['foreword'])
        paginate_type.parse_introduction(group_pages(document_blocks['introduction']), self.xml['introduction'])
        paginate_type.parse_content(group_pages(document_blocks['content']), self.xml['content'])
        # print('content', self.xml['content'])
        paginate_type.parse_application(group_pages(document_blocks['application']), self.xml['application'])
        # print(self.xml['application'])
        paginate_type.parse_keywords(group_pages(document_blocks['keywords']), self.xml['keywords'])
        paginate_type.parse_bibliography(group_pages(document_blocks['bibliography']), self.xml['bibliography'])
        # except Exception as ex:
        #     print("ERROR Paginate:", ex)
        #     if send:
        #         send_status(document_id, 500, mlProcessingId, document_type["name"])
        #     return None
        for type in self.xml:
            for tag in self.xml[type]:
                if self.xml[type][tag]:
                    if tag != 'bbox':
                        if type != 'application':
                            self.xml[type][tag], self.xml[type]["bbox"][tag] = lines_to_html(self.normalize[type][tag], self.xml[type][tag])
                        else:
                            for app in self.xml[type][tag]:
                                for sec in app['body'][0]:
                                    sec['body'] = lines_to_html('text-to-html', sec['body'])[0]
        if send:
            print("send_json")
            send_json(self.xml, document_id, 202, mlProcessingId, document_type["name"])
        else:
            if __name__ == '__main__':
                print(self.xml)
                with open("../../result/result.json", "w", encoding='utf8') as file:
                    file.write(json.dumps(self.xml, ensure_ascii=False))


if __name__ == '__main__':
    p = Paginate()
    result, document_id, send, mlProcessingId, document_type, pages_size = json.load(open(f'../../result/result_page.json', encoding='utf8'))
    p.text_to_page(result, document_id, send, mlProcessingId, document_type, pages_size)
