import json
from typing import Literal

from nehushtan.score.ParsedLine import ParsedLine


class ParsedLineAsLyric(ParsedLine):
    def __init__(self, content: str, prefix=None, content_align_type: Literal["<", "=", ">"] = ">"):
        super().__init__()
        self.__prefix = prefix
        self.__content = content
        self.__content_align_type = content_align_type

    def get_prefix(self):
        return self.__prefix

    def get_content(self):
        return self.__content

    def get_lyric_char(self, index: int):
        return self.__content[index]

    def get_content_align_type(self):
        return self.__content_align_type

    def __str__(self):
        x = (self.__prefix, self.__content)
        return "ParsedLineAsLyric: " + json.dumps(x)
