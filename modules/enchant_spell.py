# coding=utf-8
import os
import sys
import configparser
import enchant
from enchant.checker import SpellChecker
from enchant.tokenize import EmailFilter, URLFilter, WikiWordFilter
import difflib

config = configparser.ConfigParser()
config.read("settings.ini")
settings_dir = config['files']['dir'] + config['files']['settings']


import pycld2 as cld2

def getFileDic(nameLang):
    files = os.listdir(settings_dir)
    for file in files:
        filename, file_extension = os.path.splitext(file)
        if file_extension == ".dic" and filename == nameLang:
            return file
    my_file = open(f"{settings_dir}/{nameLang}.dic", "w+")
    my_file.close()
    return getFileDic(nameLang)


class EnchantSpell:
    def __init__(self):

        self.eng_dict = enchant.DictWithPWL("en_US", getFileDic("en_US"))
        self.ru_dict = enchant.DictWithPWL("ru_RU", getFileDic("ru_RU"))

        self.checker_with_filters = SpellChecker("ru_RU", filters=[EmailFilter, URLFilter, WikiWordFilter])

        self.local_dict = ['гост']

        self.languages_dict = {
            "ru": self.eng_dict,
            "en": self.ru_dict,
        }

        self.spell_languages = [l for l in self.languages_dict.keys()]

    def dictionary_correction(self, line):
        self.checker_with_filters.ignore_always('гост')

        isReliable, textBytesFound, details = cld2.detect(line)
        if isReliable:
            lang_code = details[0][1]
        else:
            lang_code = 'ru'

        # en or ru
        if lang_code in self.spell_languages:
            lang_dict = self.languages_dict[lang_code]
        else:
            return line

        self.checker_with_filters.set_text(line)

        for err in self.checker_with_filters:
            sim = dict()
            err_word = err.word

            if 'гост' in err_word.lower():
                self.checker_with_filters.ignore_always(err_word)

            if err_word.isupper():
                continue

            suggestions = set(lang_dict.suggest(err_word))
            for word in suggestions:
                res = self.checker_with_filters.check(word)
                if res:
                    measure = difflib.SequenceMatcher(None, err_word, word).ratio()
                    sim[measure] = word

            if len(sim.keys()) > 0:
                max_sim = max(sim.keys())
                if max_sim > 0.8:
                    # print("replace: ", sim[max_sim])
                    err.replace(sim[max_sim])

        corrected = self.checker_with_filters.get_text()
        return corrected
