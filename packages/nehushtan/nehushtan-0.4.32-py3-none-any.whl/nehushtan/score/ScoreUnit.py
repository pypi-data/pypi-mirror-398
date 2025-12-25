import json
import re
from typing import Literal, Optional


class ScoreUnit:
    # CHAR_ACCIDENTAL_SHARP = "#"
    # CHAR_ACCIDENTAL_FLAT = "b"  # ♭
    # CHAR_ACCIDENTAL_NATURAL = "n"  # ♮
    # CHAR_DOT = "."
    # CHAR_TRIPLET = "%"
    # CHAR_ABOVE_POINT = ">"
    # CHAR_BELOW_POINT = "<"
    # CHAR_UNDER_LINE = "_"
    # CHAR_RIGHT_LINE = "-"
    # CHAR_TIE_OR_SLUR_BEGIN = "("
    # CHAR_TIE_OR_SLUR_END = ")"
    # CHAR_FERMATA = "~"
    #
    # CHAR_REMARK_AS_LEFT = ":>"
    # CHAR_REMARK_AS_RIGHT = ":<"
    # CHAR_REMARK_AS_CENTER = ":="

    def __init__(self,
                 note: Literal[
                     "0", "1", "2", "3", "4", "5", "6", "7", "|", "||", "||:", ":||", "|:", ":|", "(", ")", ")3"],
                 under_line_count: int = 0,
                 right_line_count: int = 0,
                 above_point_count: int = 0,
                 below_point_count: int = 0,
                 dot: bool = False,
                 accidental: Optional[Literal["#", "b", "n"]] = None,
                 # ties_or_slurs_begins: bool = False,
                 # ties_or_slurs_ends: bool = False,
                 fermata: bool = False,
                 # triplet: bool = False,
                 remark_style: Optional[Literal[":>", ":=", ":<"]] = None,
                 remark_text: Optional[str] = None
                 ):
        self.__note = note
        self.__under_line_count = under_line_count
        self.__right_line_count = right_line_count
        self.__above_point_count = above_point_count
        self.__below_point_count = below_point_count
        self.__dot = dot
        self.__accidental = accidental
        # self.__ties_or_slurs_begins = ties_or_slurs_begins
        # self.__ties_or_slurs_ends = ties_or_slurs_ends
        self.__fermata = fermata
        # self.__triplet = triplet
        self.__remark_style = remark_style
        self.__remark_text = remark_text

    def __repr__(self):
        return {
            "note": self.__note,
            "under_line_count": self.__under_line_count,
            "right_line_count": self.__right_line_count,
            "above_point_count": self.__above_point_count,
            "below_point_count": self.__below_point_count,
            "dot": self.__dot,
            "accidental": self.__accidental,
            "fermata": self.__fermata,
            # "triplet": self.__triplet,
            "remark": {
                "style": self.__remark_style,
                "text": self.__remark_text
            }
        }

    def get_accidental(self):
        return self.__accidental

    def get_note(self):
        return self.__note

    def get_under_line_count(self):
        return self.__under_line_count

    def get_right_line_count(self):
        return self.__right_line_count

    def get_above_point_count(self):
        return self.__above_point_count

    def get_below_point_count(self):
        return self.__below_point_count

    def get_dot(self):
        return self.__dot

    def get_fermata(self):
        return self.__fermata

    # def get_triplet(self):
    #     return self.__triplet

    def get_remark_style(self):
        return self.__remark_style

    def get_remark_text(self):
        return self.__remark_text

    def __str__(self):
        x = self.__repr__()
        return json.dumps(x)

    def get_cell_needed(self):
        if self.__note in ("(", ")"):
            return 0
        else:
            x = 1
            if self.__right_line_count > 0:
                x += self.__right_line_count
            if self.__dot:
                x += 1 * 0
            return x

    @staticmethod
    def parse_code_to_score(the_code: str):
        if the_code is None or len(the_code.strip()) == 0:
            raise SyntaxError("score code error: empty")

        code = the_code

        remark_style = None
        remark_text = None

        r0 = re.compile("^(.+)((:[<>=])(.+))$").match(code)
        if r0:
            code = r0.group(1)
            remark_style = r0.group(3)
            remark_text = r0.group(4)

        if code in ("||:", "|:", "|", ":|", ":||", "||", "(", ")", ")3"):
            return ScoreUnit(note=code, remark_style=remark_style, remark_text=remark_text)

        r1 = re.compile("^([b#n]?)([0-7])(.*)$").match(code)
        if not r1:
            raise SystemError("score note error: " + code)

        # print(f"debug: 0: {r1.group(0)} 1: {r1.group(1)} 2: {r1.group(2)} 3: {r1.group(3)}")

        accidental = r1.group(1)
        if accidental == "":
            accidental = None
        note = r1.group(2)
        code = r1.group(3)

        if code is None or len(code) == 0:
            # print("biaozhun si fen yin fu")
            return ScoreUnit(note=note, accidental=accidental, remark_style=remark_style, remark_text=remark_text)

        above_point_count = 0
        below_point_count = 0
        under_line_count = 0
        right_line_count = 0
        dot = False
        fermata = False
        # triplet = False

        r2 = re.compile(">+").search(code)
        if r2:
            above_point_count = len(r2.group(0))
        r2 = re.compile("<+").search(code)
        if r2:
            below_point_count = len(r2.group(0))
        r2 = re.compile("_+").search(code)
        if r2:
            under_line_count = len(r2.group(0))
        r2 = re.compile("-+").search(code)
        if r2:
            right_line_count = len(r2.group(0))

        r2 = re.compile("\.").search(code)
        if r2:
            # print(f"debug dot is {dot} for {code}")
            dot = True
        r2 = re.compile("~").search(code)
        if r2:
            fermata = True
        # r2 = re.compile("%").search(code)
        # if r2:
        #     triplet = True

        return ScoreUnit(
            note=note, accidental=accidental, remark_style=remark_style, remark_text=remark_text,
            above_point_count=above_point_count,
            below_point_count=below_point_count,
            under_line_count=under_line_count,
            right_line_count=right_line_count,
            dot=dot,
            fermata=fermata
            # triplet=triplet
        )
