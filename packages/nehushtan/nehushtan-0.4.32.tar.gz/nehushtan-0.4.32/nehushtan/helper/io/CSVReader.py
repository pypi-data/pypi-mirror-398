import csv
from typing import Optional, IO, Callable, Sequence

from nehushtan.helper.io.CSVReaderOptions import CSVReaderOptions
from nehushtan.helper.io.CSVReaderRowHandleResult import CSVReaderRowHandleResult


class CSVReader:
    """
    https://docs.python.org/zh-cn/3/library/csv.html
    """

    def __init__(self, filename: str, options: Optional[CSVReaderOptions]):
        self.__filename = filename
        self.__csv_file: IO = open(self.__filename, newline='')

        self.__field_names = None

        self.__csv_reader = csv.reader(self.__csv_file, **(options.to_dict()))
        self.__current_index_of_line_to_read = 0

        self.__row_handler = None
        self.__should_handle_next_row_judge = None
        self.__row_transformer = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__csv_file is not None:
            self.__csv_file.close()

    def total_lines(self) -> int:
        return self.__csv_reader.line_num

    def next_line_index(self) -> int:
        return self.__current_index_of_line_to_read

    def set_field_names(self, field_names: Sequence[str]):
        self.__field_names = field_names
        return self

    def take_first_row_as_field_names(self):
        if self.__current_index_of_line_to_read != 0:
            raise RuntimeError("The first row had been read")
        for row in self.__csv_reader:
            self.set_field_names(row)
            break

    def set_row_handler(self, row_handler: Callable[[any, int], any]):
        self.__row_handler = row_handler
        return self

    def _row_handler(self, row, index: int, result: CSVReaderRowHandleResult):
        self.__row_handler(row, index, result)

    def set_row_transformer(self, row_transformer: Callable[[any, int, Optional[Sequence[str]]], any]):
        self.__row_transformer = row_transformer
        return self

    def _transform_row(self, row, index: int):
        if self.__row_transformer is None:
            return row
        return self.__row_transformer(row, index, self.__field_names)

    def handle_next_line(self, result: Optional[CSVReaderRowHandleResult] = None):
        """
        row_handler is a callable defined as
            def row_handler(row,index) -> any:
                pass
        """
        for row in self.__csv_reader:
            if result is None:
                result = CSVReaderRowHandleResult()
            transformed_row = self._transform_row(row, self.__current_index_of_line_to_read)
            self._row_handler(transformed_row, self.__current_index_of_line_to_read, result)
            self.__current_index_of_line_to_read += 1
            break

    def handle_next_lines(self, result: Optional[CSVReaderRowHandleResult] = None):
        """
        row_handler is a callable defined as
            def row_handler(row,index) -> bool:
                return should_continue
        """
        for row in self.__csv_reader:
            if result is None:
                result = CSVReaderRowHandleResult()
            transformed_row = self._transform_row(row, self.__current_index_of_line_to_read)
            self._row_handler(transformed_row, self.__current_index_of_line_to_read, result)
            self.__current_index_of_line_to_read += 1
            if not result.get_should_continue():
                break

    @staticmethod
    def basic_row_to_dict_transformer(row, index: int, field_names: Sequence[str]) -> any:
        rest_key = None
        rest_val = None
        rest_list = []

        d = dict()
        for i in range(max(len(row), len(field_names))):
            if i < len(row):
                if i < len(field_names):
                    d[field_names[i]] = row[i]
                else:
                    rest_list.append(row[i])
            else:
                d[field_names[i]] = rest_val

        if len(rest_list) > 0:
            d[rest_key] = rest_list

        return d
