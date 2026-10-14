import tensorflow as tf
import re
import pymorphy3
import pickle
physical_devices = tf.config.list_physical_devices('CPU')
tf.config.set_visible_devices(physical_devices)
class NLP:
    def __init__(self, dir=""):
        self.ma = pymorphy3.MorphAnalyzer()
        self.model_loaded = tf.keras.models.load_model(dir + 'lib/nlp/findRequirements.h5')
        self.words_block_list = ['гост']
        with open(dir + 'lib/nlp/tokenizer.pickle', 'rb') as handle:
            self.tokenizer = pickle.load(handle)

    def clean_text(self, text):
        text = text.replace("\\", " ").replace(u"╚", " ").replace(u"╩", " ").replace(u"<p>", " ").replace(u"</p>", " ")
        text = text.lower()
        text = re.sub('\-\r\n|’s', '', text)  # deleting newlines and line-breaks
        text = re.sub('[«»°–\-—―.,:;_%©?*,!@#$%^&()\d]|[+=]|[\[]|[\]]|[\/]|"|\s{2,}|\r\n', ' ', text)
        array = [word for word in text.split() if len(word) > 3]
        array = [word for word in array if not word in self.words_block_list]
        array = [self.ma.parse(word)[0].normal_form for word in array]
        text = ' '.join(array)

        return text

    def predict(self, text):
        text = self.clean_text(text)
        textSequences = self.tokenizer.texts_to_sequences([text])
        [y] = self.model_loaded.predict(self.tokenizer.sequences_to_matrix(textSequences, mode='binary'), verbose=0)
        return y[0] < y[1]
