from .datatransform import DataTransform
from .util import parse_bool
from abc import ABC, abstractmethod
import enum
import locale


class DataAdapter(DataTransform, ABC):
    @abstractmethod
    def __init__(self):
        super().__init__()
        self.data_model_uri = None


class DatabaseAdapter(DataAdapter, ABC):
    @abstractmethod
    def __init__(self):
        super().__init__()


class RelationalDatabaseAdapter(DatabaseAdapter):
    def __init__(self):
        super().__init__()


class FileAdapter(DataAdapter, ABC):
    @abstractmethod
    def __init__(self):
        super().__init__()
        self.path = None         # Use a.out


class ExcelNotebookAdapter(FileAdapter):
    def __init__(self):
        super().__init__()

Quoting = enum.Enum('Quoting', 'NONE MINIMAL NONNUMERIC ALL')

class FlatFileAdapter(FileAdapter, ABC):
    @abstractmethod
    def __init__(self):
        super().__init__()
        self.__header = False
        self.line_ending = None  # Use default
        self.quote_char = '"'
        self.__quoting = Quoting.MINIMAL
        self.encoding = locale.getpreferredencoding()

    @property
    def header(self) -> bool:
        """
        Whether the file format includes a header. The setter will accept a
        string and a parse it as a bool. See heaobject.util.parse_bool for more
        information.
        """
        return self.__header

    @header.setter
    def header(self, header: bool):
        if header is None:
            self.__header = False
        elif isinstance(header, bool):
            self.__header = header
        else:
            self.__header = parse_bool(header)

    @property
    def quoting(self) -> Quoting:
        """
        The quoting mode (NONE, MINIMAL, NONNUMERIC, ALL). The default is MINIMAL.
        """
        return self.__quoting

    @quoting.setter
    def quoting(self, quoting: Quoting):
        if quoting is None:
            self.__quoting = Quoting.MINIMAL
        elif isinstance(quoting, Quoting):
            self.__quoting = quoting
        else:
            try:
                self.__quoting = Quoting[quoting]
            except KeyError as e:
                raise ValueError(str(e)) from e


class DelimitedFileAdapter(FlatFileAdapter):
    def __init__(self):
        super().__init__()
        self.delimiter = '\t'


class FixedWidthFileAdapter(FlatFileAdapter):
    def __init__(self):
        super().__init__()
        self.col_specs = []  #list of tuples (start_index, length)
