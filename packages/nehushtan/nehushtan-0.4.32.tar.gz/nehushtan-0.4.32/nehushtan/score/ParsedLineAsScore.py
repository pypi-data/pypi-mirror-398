import json
from typing import List

from nehushtan.score.ParsedLine import ParsedLine
from nehushtan.score.ScoreUnit import ScoreUnit


class ParsedLineAsScore(ParsedLine):
    def __init__(self, score_units: List[ScoreUnit]):
        super().__init__()
        self.__score_units = score_units

    def get_score_units(self):
        return self.__score_units

    def get_score_unit(self, index: int):
        return self.__score_units[index]

    def __str__(self):
        y = []
        for su in self.__score_units:
            x = su.__repr__()
            y.append(x)
        return "ParsedLineAsScore: " + json.dumps(y)
