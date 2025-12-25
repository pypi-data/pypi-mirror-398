import json
from typing import List, Optional

from nehushtan.score.ParsedLine import ParsedLine


class ParsedLineAsTitle(ParsedLine):

    def __init__(self, components: List[str]):
        super().__init__()

        self.__left_component: Optional[str] = None
        self.__middle_component: Optional[str] = None
        self.__right_component: Optional[str] = None

        if components is None or len(components) == 0:
            raise SyntaxError("title line componets empty")
        if len(components) == 1:
            self.__middle_component = components[0]
        elif len(components) == 2:
            self.__left_component = components[0]
            self.__right_component = components[1]
        else:
            self.__left_component = components[0]
            self.__middle_component = components[1]
            self.__right_component = components[2]

    def get_left_componet(self):
        if self.__left_component == "":
            return None
        return self.__left_component

    def get_middle_component(self):
        if self.__middle_component is None:
            return ""
        return self.__middle_component

    def get_right_component(self):
        if self.__right_component == "":
            return None
        return self.__right_component

    def __str__(self):
        x = (self.__left_component, self.__middle_component, self.__right_component,)
        return "ParsedLineAsTitle: " + json.dumps(x)
