class CSVReaderRowHandleResult:
    def __init__(self):
        self.__should_continue = True

    def set_should_continue(self, should_continue: bool):
        self.__should_continue = should_continue
        return self

    def get_should_continue(self):
        return self.__should_continue
