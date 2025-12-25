from nehushtan.helper.io.CSVReader import CSVReader
from nehushtan.helper.io.CSVReaderOptions import CSVReaderOptions
from nehushtan.helper.io.CSVReaderRowHandleResult import CSVReaderRowHandleResult

csv_file = "/Users/leqee/code/nehushtan/debug/attachments/1.csv"


# def row_transformer(row, index: int, field_names: Sequence[str]) -> any:
#     rest_key = None
#     rest_val = None
#     rest_list = []
#
#     d = dict()
#     for i in range(max(len(row), len(field_names))):
#         if i < len(row):
#             if i < len(field_names):
#                 d[field_names[i]] = row[i]
#             else:
#                 rest_list.append(row[i])
#         else:
#             d[field_names[i]] = rest_val
#
#     if len(rest_list) > 0:
#         d[rest_key] = rest_list
#
#     return d


def row_handler_1(row, index: int, result: CSVReaderRowHandleResult) -> bool:
    if index == 2 or index == 4:
        result.set_should_continue(False)
    print(index, row, result.get_should_continue())


if __name__ == '__main__':
    csv_reader = CSVReader(csv_file, CSVReaderOptions())

    csv_reader.set_row_transformer(CSVReader.basic_row_to_dict_transformer)
    csv_reader.set_row_handler(row_handler_1)
    csv_reader.take_first_row_as_field_names()

    print("from", csv_reader.next_line_index())
    csv_reader.handle_next_line()
    print("to", csv_reader.next_line_index())

    print("from", csv_reader.next_line_index())
    csv_reader.handle_next_lines()
    print("to", csv_reader.next_line_index())

    print("from", csv_reader.next_line_index())
    csv_reader.handle_next_line()
    print("to", csv_reader.next_line_index())

    print("from", csv_reader.next_line_index())
    csv_reader.handle_next_lines()
    print("to", csv_reader.next_line_index())

    print("from", csv_reader.next_line_index())
    csv_reader.handle_next_line()
    print("to", csv_reader.next_line_index())
