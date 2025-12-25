from typing import Literal, Optional

from nehushtan.paint.Paint import Paint


class ScoreDrawerOptions:
    def __init__(self,
                 default_ttf_font_file_path,
                 default_font_size: int
                 ):
        self.__default_ttf_font_file_path = default_ttf_font_file_path
        self.__default_font_size = default_font_size
        # self.__default_font = Paint.load_ttf_font(self.__default_ttf_font_file_path, self.__default_font_size)

        self.__title_font_file_path = None
        self.__title_font_size = None

        self.__title_left_component_font_file_path = None
        self.__title_left_component_font_size = None
        self.__title_middle_component_font_file_path = None
        self.__title_middle_component_font_size = None
        self.__title_right_component_font_file_path = None
        self.__title_right_component_font_size = None

        self.__score_font_path = None
        self.__score_font_size = None

        self.__lyric_font_path = None
        self.__lyric_font_size = None

        self.__lyric_prefix_font_path = None
        self.__lyric_prefix_font_size = None

        self.__total_cells_in_one_line = None

    def get_default_font_size(self):
        return self.__default_font_size

    def get_default_font(self):
        return Paint.load_ttf_font(self.__default_ttf_font_file_path, self.__default_font_size)

    def set_title_font_size(self, x):
        self.__title_font_size = x
        return self

    def set_title_font_file_path(self, x):
        self.__title_font_file_path = x
        return self

    def set_title_left_component_font_size(self, x):
        self.__title_left_component_font_size = x
        return self

    def set_title_left_component_font_file_path(self, x):
        self.__title_left_component_font_file_path = x
        return self

    def set_title_middle_component_font_size(self, x):
        self.__title_middle_component_font_size = x
        return self

    def set_title_middle_component_font_file_path(self, x):
        self.__title_middle_component_font_file_path = x
        return self

    def set_title_right_component_font_size(self, x):
        self.__title_right_component_font_size = x
        return self

    def set_title_right_component_font_file_path(self, x):
        self.__title_right_component_font_file_path = x
        return self

    def __get_font_for_title_x_component(self, x: Literal["left", "middle", "right"]):
        if x == "left":
            file = self.__title_left_component_font_file_path
            size = self.__title_left_component_font_size
        elif x == "right":
            file = self.__title_right_component_font_file_path
            size = self.__title_right_component_font_size
        else:
            file = self.__title_middle_component_font_file_path
            size = self.__title_middle_component_font_size

        if file is None:
            file = self.__title_font_file_path
        if file is None:
            file = self.__default_ttf_font_file_path

        if size is None:
            size = self.__title_font_size
        if size is None:
            size = self.__default_font_size

        return Paint.load_ttf_font(file, size)

    def get_font_for_title_left_component(self):
        return self.__get_font_for_title_x_component("left")

    def get_font_for_title_middle_component(self):
        return self.__get_font_for_title_x_component("middle")

    def get_font_for_title_right_component(self):
        return self.__get_font_for_title_x_component("right")

    def set_score_font_path(self, x):
        self.__score_font_path = x
        return self

    def set_score_font_size(self, x):
        self.__score_font_size = x
        return self

    def get_font_for_score(self):
        file = self.__score_font_path
        size = self.__score_font_size
        if file is None:
            file = self.__default_ttf_font_file_path
        if size is None:
            size = self.__default_font_size
        return Paint.load_ttf_font(file, size)

    def get_font_for_score_note(self):
        file = self.__score_font_path
        size = self.__score_font_size
        if file is None:
            file = self.__default_ttf_font_file_path
        if size is None:
            size = self.__default_font_size
        # size = int(size * 2 / 3.0)
        size = int(size * 0.5)
        return Paint.load_ttf_font(file, size)

    def set_lyric_font_path(self, x):
        self.__lyric_font_path = x
        return self

    def set_lyric_font_size(self, x):
        self.__lyric_font_size = x
        return self

    def set_lyric_prefix_font_path(self, x):
        self.__lyric_prefix_font_path = x
        return self

    def set_lyric_prefix_font_size(self, x):
        self.__lyric_prefix_font_size = x
        return self

    def get_font_for_lyric(self):
        file = self.__lyric_font_path
        size = self.__lyric_font_size
        if file is None:
            file = self.__default_ttf_font_file_path
        if size is None:
            size = self.__default_font_size
        return Paint.load_ttf_font(file, size)

    def get_font_for_lyric_prefix(self):
        file = self.__lyric_prefix_font_path
        size = self.__lyric_prefix_font_size
        if file is None:
            file = self.__lyric_font_path
        if size is None:
            size = self.__lyric_font_size
        if file is None:
            file = self.__default_ttf_font_file_path
        if size is None:
            size = self.__default_font_size
        return Paint.load_ttf_font(file, size)

    def set_total_cells_in_one_line(self, x: Optional[int]):
        self.__total_cells_in_one_line = x
        return self

    def get_total_cells_in_one_line(self) -> Optional[int]:
        return self.__total_cells_in_one_line
