from nehushtan.score.ParsedLine import ParsedLine


class ParsedLineAsBlank(ParsedLine):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "ParsedLineAsBlank"
