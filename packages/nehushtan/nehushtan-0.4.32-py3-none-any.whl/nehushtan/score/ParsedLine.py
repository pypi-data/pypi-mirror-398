from abc import abstractmethod


class ParsedLine:
    def __init__(self):
        pass

    @abstractmethod
    def __str__(self):
        return "ParsedLine"
