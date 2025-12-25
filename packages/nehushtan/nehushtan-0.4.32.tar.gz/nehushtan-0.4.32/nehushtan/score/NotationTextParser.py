import re

from nehushtan.score.ParsedLineAsBlank import ParsedLineAsBlank
from nehushtan.score.ParsedLineAsLyric import ParsedLineAsLyric
from nehushtan.score.ParsedLineAsScore import ParsedLineAsScore
from nehushtan.score.ParsedLineAsTitle import ParsedLineAsTitle
from nehushtan.score.ScoreUnit import ScoreUnit


class NotationTextParser:
    def __init__(self, text: str = None, file: str = None):
        self.__lines = []
        self.__parsed_lines = []
        if text is not None:
            lines = text.splitlines(keepends=False)
            for line in lines:
                self.__lines.append(line)
        elif file is not None:
            with open(file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                self.__text = ""
                for line in lines:
                    self.__lines.append(line)
        else:
            pass

    def parse(self):
        for line in self.__lines:
            if line is None or line == "" or len(line.strip()) == 0:
                self.__parsed_lines.append(ParsedLineAsBlank())
            elif line.startswith("~"):
                self.__parse_title_line(line)
            elif line.startswith(">"):
                self.__parse_lyric_line(line)
            else:
                self.__parse_score_line(line)

    def __parse_title_line(self, line):
        compiled = re.compile("^~ (.+)\s*$")
        r = compiled.match(line)
        if r:
            x = r.group(1)
            components = re.compile("\s*\|\s*").split(x)
            self.__parsed_lines.append(ParsedLineAsTitle(components))

    def __parse_lyric_line(self, line):
        compiled = re.compile("^>((.+)([<=>]))? (.+)\s*$")
        r = compiled.match(line)
        if r:
            prefix = r.group(2)
            if prefix == "":
                prefix = None
            content_align_type = r.group(3)
            if content_align_type not in ("<", "="):
                content_align_type = ">"
            content = r.group(4)

            # if len(r.groups()) == 2:
            #     prefix = None
            #     content = r.group(1)
            # else:
            #     prefix = r.group(2)
            #     content = r.group(3)
            self.__parsed_lines.append(ParsedLineAsLyric(content, prefix, content_align_type))

    def __parse_score_line(self, line):
        # print(line)
        compiled = re.compile("\s+")
        items = compiled.split(line.strip())
        score_unit_list = []
        for item in items:
            #print(json.dumps(item))
            score_unit = ScoreUnit.parse_code_to_score(item)
            score_unit_list.append(score_unit)
        self.__parsed_lines.append(ParsedLineAsScore(score_unit_list))

    def debug(self):
        for p in self.__parsed_lines:
            print(p)

    def get_parsed_score_lines(self):
        return self.__parsed_lines
