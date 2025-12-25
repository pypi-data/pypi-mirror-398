import csv
from typing import Optional, Union, Type


class CSVReaderOptions:
    def __init__(
            self,
            dialect: Optional[Union[csv.Dialect, Type[csv.Dialect], str]] = None,
            delimiter: Optional[str] = None,
            doublequote: Optional[bool] = None,
            escapechar: Optional[str] = None,
            lineterminator: Optional[str] = None,
            quotechar: Optional[str] = None,
            quoting: Optional[int] = None,
            skipinitialspace: Optional[bool] = None,
            strict: Optional[bool] = None
    ):
        self.dialect = dialect
        self.delimiter = delimiter
        self.doublequote = doublequote
        self.escapechar = escapechar
        self.lineterminator = lineterminator
        self.quotechar = quotechar
        self.quoting = quoting
        self.skipinitialspace = skipinitialspace
        self.strict = strict

        if dialect is not None:
            self.dialect = dialect
        if delimiter is not None:
            self.delimiter = delimiter
        if doublequote is not None:
            self.doublequote = doublequote
        if escapechar is not None:
            self.escapechar = escapechar
        if lineterminator is not None:
            self.lineterminator = lineterminator
        if quotechar is not None:
            self.quotechar = quotechar
        if quoting is not None:
            self.quoting = quoting
        if skipinitialspace is not None:
            self.skipinitialspace = skipinitialspace
        if strict is not None:
            self.strict = strict

    def to_dict(self):
        reader_kwargs = dict()
        if self.dialect is not None:
            reader_kwargs['dialect'] = self.dialect
        if self.delimiter is not None:
            reader_kwargs['delimiter'] = self.delimiter
        if self.doublequote is not None:
            reader_kwargs['doublequote'] = self.doublequote
        if self.escapechar is not None:
            reader_kwargs['escapechar'] = self.escapechar
        if self.lineterminator is not None:
            reader_kwargs['lineterminator'] = self.lineterminator
        if self.quotechar is not None:
            reader_kwargs['quotechar'] = self.quotechar
        if self.quoting is not None:
            reader_kwargs['quoting'] = self.quoting
        if self.skipinitialspace is not None:
            reader_kwargs['skipinitialspace'] = self.skipinitialspace
        if self.strict is not None:
            reader_kwargs['strict'] = self.strict

        return reader_kwargs
