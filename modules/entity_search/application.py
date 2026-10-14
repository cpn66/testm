import re
from modules.default import lines_to_html

class Application:

    def __init__(self):
        self.application = dict()
        self.application['label'] = ""
        self.application['annex-type'] = ""
        self.application['title'] = ""
        self.application['body'] = list()
        self.application['bbox'] = list()

    def get_data(self):
        return self.application

    def parse_line(self, line):
        if len(line[1]) > 0:
            self.application['bbox'].append(line)
            if len(self.application['body']) > 0:
                self.application['body'].append(line)
            elif not self.application['label']:
                search = re.search('(^[\s\S]*?)\n[\(\{\[]*([\s\S]*?)[\)\]\}]*\n', line[1])
                if search and len(search.groups()) > 0:
                    self.application['label'] = search.groups()[0]
                    self.application['annex-type'] = search.groups()[1]
                else:
                    self.application['label'] = line[1]
            elif not self.application['annex-type']:
                search = re.search('^[\(\{\[]([\s\S]*)[\)\]\}]', line[1])
                if search and len(search.groups()) > 0:
                    self.application['annex-type'] = search.groups()[0]
                else:
                    self.application['title'] = line
            elif not self.application['title']:
                self.application['title'] = line
            else:
                # print('body', line)
                self.application['body'].append(line)

    def body_to_sec(self):
        self.application['body'] = lines_to_html("lines-to-none", self.application['body'])
        # print(self.application['body'][0])
        split = re.split('(?=^|(?<=\\n))([А-ЯA-Z]+)[\.\-\,]?([\d]+)([\.\-\,][\d]+)?([\.\-\,][\d]+)?\s', self.application['body'][0])
        idx = 0
        sections = list()
        if len(split[0]) > 0:
            sections.append({"id": 0, "number": None, "body": split[0], "type": "text"})
        del split[0]
        parent = {
            "id": 0,
            "type": 0
        }
        while idx < len(split):
            section = dict()
            type_sec = 0
            if split[0 + idx]:
                type_sec = 1
                section['number'] = split[0 + idx]
            if split[1 + idx]:
                type_sec = 2
                section['number'] += "." + split[1 + idx]
            if split[2 + idx]:
                type_sec = 3
                section['number'] += split[2 + idx]
            if split[3 + idx]:
                type_sec = 4
                section['number'] += split[3 + idx]
            if type_sec > parent["type"]:
                for sec in sections:
                    if sec["id"] == parent["id"]:
                        sec["type"] = "header"
            section['body'] = split[4 + idx]
            section['type'] = "text"
            parent["id"] += 1
            parent["type"] = type_sec
            section['id'] = parent["id"]
            sections.append(section)
            idx += 5
        self.application['body'] = [sections, self.application['body'][1]]
        return True



class Applications:
    def __init__(self, pages):
        self.app_pages = list()
        self.pages = pages

    def find_applications(self):
        idx = -1
        for line in self.pages:
            text = re.findall("Приложение.*?\\n(([\(\{\[\]\}\)].*\))*)*?", line[1])
            if text:
                idx += 1
                self.app_pages.append(Application())
                self.app_pages[idx].parse_line(line)
            elif idx >= 0:
                self.app_pages[idx].parse_line(line)
        for app in self.app_pages:
            app.body_to_sec()
        return [app.get_data() for app in self.app_pages]
