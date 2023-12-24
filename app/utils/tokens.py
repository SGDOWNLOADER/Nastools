import re

from config import SPLIT_CHARS, SPLIT_CHARS_1, SPLIT_CHARS_2


class Tokens:
    _text = ""
    _index = 0
    _tokens = []

    def __init__(self, text):
        self._text = text
        self._tokens = []
        self.load_text(text)

    def load_text(self, text):
        if len(re.findall(SPLIT_CHARS_1, text)) > 6:
            splited_text = re.split(r'%s' % SPLIT_CHARS_1, text)
        else:
            splited_text = re.split(r'%s' % SPLIT_CHARS, text)
        for sub_text in splited_text:
            if sub_text:
                self._tokens.append(sub_text)

    def cur(self):
        if self._index >= len(self._tokens):
            return None
        else:
            token = self._tokens[self._index]
            return token

    def get_next(self):
        token = self.cur()
        if token:
            self._index = self._index + 1
        return token

    def peek(self):
        index = self._index + 1
        if index >= len(self._tokens):
            return None
        else:
            return self._tokens[index]
