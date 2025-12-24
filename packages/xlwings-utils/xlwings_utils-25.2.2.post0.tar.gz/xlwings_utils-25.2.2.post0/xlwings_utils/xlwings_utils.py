#         _            _                                   _    _  _
#  __  __| |__      __(_) _ __    __ _  ___         _   _ | |_ (_)| | ___
#  \ \/ /| |\ \ /\ / /| || '_ \  / _` |/ __|       | | | || __|| || |/ __|
#   >  < | | \ V  V / | || | | || (_| |\__ \       | |_| || |_ | || |\__ \
#  /_/\_\|_|  \_/\_/  |_||_| |_| \__, ||___/ _____  \__,_| \__||_||_||___/
#                                |___/      |_____|

__version__ = "25.2.2"

from pathlib import Path
import sys
import math
import base64
import datetime
import functools

Pythonista = sys.platform == "ios"

try:
    import xlwings
except ImportError:
    xlwings = False

missing = object()


class block:
    """
    block is 2 dimensional data structure with 1 as lowest index (like xlwings range)

    Parameters
    ----------
    number_of_rows : int
        number of rows (dedault 1)

    number_of_columns : int
        number of columns (default 1)

    Returns
    -------
    block
    """

    def __init__(self, number_of_rows=1, number_of_columns=1):
        self.dict = {}
        self.number_of_rows = number_of_rows
        self.number_of_columns = number_of_columns
        self._invalidate_highest_used_cache()

    def __eq__(self, other):
        if isinstance(other, block):
            return self.value == other.value
        return False

    @classmethod
    def from_value(cls, value, column_like=False):
        """
        makes a block from a given value

        Parameters
        ----------
        value : scalar, list of scalars, list of lists of scalars or block
            value to be used in block, possibly expanded to a list of lists of scalars

        column_like : boolean
            if value is a list of scalars, values is interpreted as a column if True, as a row otherwise

        Returns
        -------
        block : block
        """
        if isinstance(value, block):
            value = value.value
        if not isinstance(value, list):
            value = [[value]]
        if not isinstance(value[0], list):
            if column_like:
                value = [[item] for item in value]
            else:
                value = [value]
        bl = cls(len(value), 1)

        for row, row_contents in enumerate(value, 1):
            for column, item in enumerate(row_contents, 1):
                if item and not (isinstance(item, float) and math.isnan(item)):
                    bl.dict[row, column] = item
                bl._number_of_columns = max(bl.number_of_columns, column)
        return bl

    @classmethod
    def from_range(cls, rng):
        """
        makes a block from a given range

        Parameters
        ----------
        rng : xlwings.Range
            range to be used be used in block

        Returns
        -------
        block : block
        """
        number_of_rows, number_of_columns = rng.shape
        return cls.from_value(rng.value, column_like=(number_of_columns == 1))

    @classmethod
    def from_xlrd_sheet(cls, sheet):
        """
        makes a block from a xlrd sheet

        Parameters
        ----------
        sheet : xlrd sheet
            sheet to be used be used in block

        Returns
        -------
        block : block
        """
        v = [sheet.row_values(row_idx)[0 : sheet.ncols] for row_idx in range(0, sheet.nrows)]
        return cls.from_value(v)

    @classmethod
    def from_openpyxl_sheet(cls, sheet):
        """
        makes a block from an openpyxl sheet

        Parameters
        ----------
        sheet : xlrd sheet
            sheet to be used be used in block

        Returns
        -------
        block : block
        """
        v = [[cell.value for cell in row] for row in sheet.iter_rows()]
        return cls.from_value(v)

    @classmethod
    def from_file(cls, filename):
        """
        makes a block from a file

        Parameters
        ----------
        filename : str
            file to be used be used in block

        Returns
        -------
        block : block
        """
        with open(filename, "r") as f:
            v = [[line if line else missing] for line in f.read().splitlines()]
        return cls.from_value(v)

    @classmethod
    def from_dataframe(cls, df):
        """
        makes a block from a given dataframe

        Parameters
        ----------
        df : pandas dataframe
            dataframe to be used be used in block

        Returns
        -------
        block : block
        """
        v = df.values.tolist()
        return cls.from_value(v)

    def to_openpyxl_sheet(self, sheet):
        """
        appends a block to a given openpyxl sheet

        Parameters
        ----------
        sheet: openpyxl sheet
            sheet to be used be used

        Returns
        -------
        block : block
        """
        for row in self.value:
            sheet.append(row)

    def reshape(self, number_of_rows=missing, number_of_columns=missing):
        """
        makes a new block with given dimensions

        Parameters
        ----------
        number_of_rows : int
            if given, expand or shrink to the given number of rows

        number_of_columns : int
            if given, expand or shrink to the given number of columns

        Returns
        -------
        block : block
        """
        if number_of_rows is missing:
            number_of_rows = self.number_of_rows
        if number_of_columns is missing:
            number_of_columns = self.number_of_columns
        bl = block(number_of_rows=number_of_rows, number_of_columns=number_of_columns)
        for (row, column), value in self.dict.items():
            if row <= number_of_rows and column <= number_of_columns:
                bl[row, column] = value
        return bl

    @property
    def value(self):
        return [[self.dict.get((row, column)) for column in range(1, self.number_of_columns + 1)] for row in range(1, self.number_of_rows + 1)]

    def _invalidate_highest_used_cache(self):
        self._highest_used_row_number = None
        self._highest_used_column_number = None

    def __setitem__(self, row_column, value):
        row, column = row_column
        if row < 1 or row > self.number_of_rows:
            raise IndexError(f"row must be between 1 and {self.number_of_rows}; not {row}")
        if column < 1 or column > self.number_of_columns:
            raise IndexError(f"column must be between 1 and {self.number_of_columns}; not {column}")
        if value is None:
            if (row, column) in self.dict:
                del self.dict[row, column]
                self._invalidate_highest_used_cache()

        else:
            self.dict[row, column] = value
            if self._highest_used_row_number:
                self._highest_used_row_number = max(self._highest_used_row_number, row)
            if self._highest_used_column_number:
                self._highest_used_column_number = max(self._highest_used_column_number, column)

    def __getitem__(self, row_column):
        row, column = row_column
        if row < 1 or row > self.number_of_rows:
            raise IndexError(f"row must be between 1 and {self.number_of_rows} not {row}")
        if column < 1 or column > self.number_of_columns:
            raise IndexError(f"column must be between 1 and {self.number_of_columns} not {column}")
        return self.dict.get((row, column))

    def minimized(self):
        """
        Returns
        -------
        minimized block : block
             uses highest_used_row_number and highest_used_column_number to minimize the block
        """
        return self.reshape(number_of_rows=self.highest_used_row_number, number_of_columns=self.highest_used_column_number)

    @property
    def number_of_rows(self):
        return self._number_of_rows

    @number_of_rows.setter
    def number_of_rows(self, value):
        if value < 1:
            raise ValueError(f"number_of_rows should be >=1; not {value}")
        self._invalidate_highest_used_cache()
        self._number_of_rows = value
        for row, column in list(self.dict):
            if row > self._number_of_rows:
                del self.dict[row, column]

    @property
    def number_of_columns(self):
        return self._number_of_columns

    @number_of_columns.setter
    def number_of_columns(self, value):
        if value < 1:
            raise ValueError(f"number_of_columns should be >=1; not {value}")
        self._invalidate_highest_used_cache()
        self._number_of_columns = value
        for row, column in list(self.dict):
            if column > self._number_of_columns:
                del self.dict[row, column]

    @property
    def highest_used_row_number(self):
        if not self._highest_used_row_number:
            if self.dict:
                self._highest_used_row_number = max(row for (row, column) in self.dict)
            else:
                self._highest_used_row_number = 1
        return self._highest_used_row_number

    @property
    def highest_used_column_number(self):
        if not self._highest_used_column_number:
            if self.dict:
                self._highest_used_column_number = max(column for (row, column) in self.dict)
            else:
                self._highest_used_column_number = 1

        return self._highest_used_column_number

    def __repr__(self):
        return f"block({self.value})"

    def _check_row(self, row, name):
        if row < 1:
            raise ValueError(f"{name}={row} < 1")
        if row > self.number_of_rows:
            raise ValueError(f"{name}={row} > number_of_rows={self.number_of_rows}")

    def _check_column(self, column, name):
        if column < 1:
            raise ValueError(f"{name}={column} < 1")
        if column > self.number_of_columns:
            raise ValueError(f"{name}={column} > number_of_columns={self.number_of_columns}")

    def transposed(self):
        """
        transpose block

        Returns
        -------
        transposed block : block
        """
        bl = block(number_of_rows=self.number_of_columns, number_of_columns=self.number_of_rows)
        for (row, column), value in self.dict.items():
            bl[column, row] = value
        return bl

    def vlookup(self, s, *, row_from=1, row_to=missing, column1=1, column2=missing, default=missing):
        """
        searches in column1 for row between row_from and row_to for s and returns the value found at (that row, column2)

        Parameters
        ----------
        s : any
            value to seach for

        row_from : int
             row to start search (default 1)

             should be between 1 and number_of_rows

        row_to : int
             row to end search (default number_of_rows)

             should be between 1 and number_of_rows

        column1 : int
             column to search in (default 1)

             should be between 1 and number_of_columns

        column2 : int
             column to return looked up value from (default column1 + 1)

             should be between 1 and number_of_columns

        default : any
             if s is not found, returns the default.

             if omitted, a ValueError exception will be raised in that case

        Returns
        -------
        block[found row number, column2] : any
        """
        if column2 is missing:
            column2 = column1 + 1
        self._check_column(column2, "column2")
        row = self.lookup_row(s, row_from=row_from, row_to=row_to, column1=column1, default=-1)
        if row == -1:
            if default is missing:
                raise ValueError(f"{s} not found]")
            else:
                return default
        else:
            return self[row, column2]

    def lookup_row(self, s, *, row_from=1, row_to=missing, column1=1, default=missing):
        """
        searches in column1 for row between row_from and row_to for s and returns that row number

        Parameters
        ----------
        s : any
            value to seach for

        row_from : int
             row to start search (default 1)

             should be between 1 and number_of_rows

        row_to : int
             row to end search (default number_of_rows)

             should be between 1 and number_of_rows

        column1 : int
             column to search in (default 1)

             should be between 1 and number_of_columns

        column2 : int
             column to return looked up value from (default column1 + 1)

        default : any
             if s is not found, returns the default.

             if omitted, a ValueError exception will be raised

        default : any
             if s is not found, returns the default.

             if omitted, a ValueError exception will be raised in that case


        Returns
        -------
        row number where block[row nunber, column1] == s : int
        """
        if row_to is missing:
            row_to = self.highest_used_row_number
        self._check_row(row_from, "row_from")
        self._check_row(row_to, "row_to")
        self._check_column(column1, "column1")

        for row in range(row_from, row_to + 1):
            if self[row, column1] == s:
                return row
        if default is missing:
            raise ValueError(f"{s} not found")
        else:
            return default

    def hlookup(self, s, *, column_from=1, column_to=missing, row1=1, row2=missing, default=missing):
        """
        searches in row1 for column between column_from and column_to for s and returns the value found at (that column, row2)

        Parameters
        ----------
        s : any
            value to seach for

        column_from : int
             column to start search (default 1)

             should be between 1 and number_of_columns

        column_to : int
             column to end search (default number_of_columns)

             should be between 1 and number_of_columns

        row1 : int
             row to search in (default 1)

             should be between 1 and number_of_rows

        row2 : int
             row to return looked up value from (default row1 + 1)

             should be between 1 and number_of_rows

        default : any
             if s is not found, returns the default.

             if omitted, a ValueError exception will be raised in that case

        Returns
        -------
        block[row, found column, row2] : any
        """
        if row2 is missing:
            row2 = row1 + 1
        self._check_row(row2, "row2")
        column = self.lookup_column(s, column_from=column_from, column_to=column_to, row1=row1, default=-1)
        if column == -1:
            if default is missing:
                raise ValueError(f"{s} not found")
            else:
                return default
        else:
            return self[row2, column]

    def lookup_column(self, s, *, column_from=1, column_to=missing, row1=1, default=missing):
        """
        searches in row1 for column between column_from and column_to for s and returns that column number

        Parameters
        ----------
        s : any
            value to seach for

        column_from : int
             column to start search (default 1)

             should be between 1 and number_of_columns

        column_to : int
             column to end search (default number_of_columns)

             should be between 1 and number_of_columns

        row1 : int
             row to search in (default 1)

             should be between 1 and number_of_rows

        row2 : int
             row to return looked up value from (default row1 + 1)

        default : any
             if s is not found, returns the default.

             if omitted, a ValueError exception will be raised in that case

        Returns
        -------
        column number where block[row1, column number] == s : int
        """
        if column_to is missing:
            column_to = self.highest_used_column_number
        self._check_column(column_from, "column_from")
        self._check_column(column_to, "column_to")
        self._check_row(row1, "row1")

        for column in range(column_from, column_to + 1):
            if self[row1, column] == s:
                return column
        if default is missing:
            raise ValueError(f"{s} not found")
        else:
            return default

    def lookup(self, s, *, row_from=1, row_to=missing, column1=1, column2=missing, default=missing):
        """
        searches in column1 for row between row_from and row_to for s and returns the value found at (that row, column2)

        Parameters
        ----------
        s : any
            value to seach for

        row_from : int
             row to start search (default 1)

             should be between 1 and number_of_rows

        row_to : int
             row to end search (default number_of_rows)

             should be between 1 and number_of_rows

        column1 : int
             column to search in (default 1)

             should be between 1 and number_of_columns

        column2 : int
             column to return looked up value from (default column1 + 1)

             should be between 1 and number_of_columns

        default : any
             if s is not found, returns the default.

             if omitted, a ValueError exception will be raised in that case

        Returns
        -------
        block[found row number, column2] : any

        Note
        ----
        This is exactly the same as vlookup.
        """
        return self.vlookup(s, row_from=row_from, row_to=row_to, column1=column1, column2=column2, default=default)

    def decode_to_files(self):
        """
        decode the block with encoded file(s) to individual pyoidide file(s)

        Returns
        -------
        count : int
            number of files decoded

        Note
        ----
        if the block does not contain an encode file, the method just returns 0
        """
        count = 0
        for column in range(1, self.number_of_columns + 1):
            row = 1
            bl = self.minimized()
            while row <= self.number_of_rows:
                if self[row, column] and self[row, column].startswith("<file=") and self[row, column].endswith(">"):
                    filename = self[row, column][6:-1]
                    collect = []
                    row += 1
                    while bl[row, column] != "</file>":
                        if bl[row, column]:
                            collect.append(bl[row, column])
                        row += 1
                    decoded = base64.b64decode("".join(collect))
                    open(filename, "wb").write(decoded)
                    count += 1
                row += 1
        return count

    @classmethod
    def encode_file(cls, file):
        """
        make a block with the given pyodide file encoded

        Parameters
        ----------
        file : file name (str)
            file to be encoded

        Returns
        -------
        block with encoded file : block (minimized)
        """

        bl = cls(number_of_rows=100000, number_of_columns=1)

        n = 5000  # block size
        row = 1
        bl[row, 1] = f"<file={file}>"
        row += 1
        b64 = base64.b64encode(open(file, "rb").read()).decode("utf-8")
        while b64:
            b64_n = b64[:n]
            bl[row, 1] = b64_n
            row += 1
            b64 = b64[n:]
        bl[row, 1] = f"</file>"
        row += 1
        return bl.minimized()


class Capture:
    """
    specifies how to capture stdout

    Parameters
    ----------
    enabled : bool
        if True (default), all stdout output is captured

        if False, stdout output is printed

    include_print : bool
        if False (default), nothing will be printed if enabled is True

        if True, output will be printed (and captured if enabled is True)

    Note
    ----
    Use this like ::

        capture = xwu.Capture()
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        # singleton
        if cls._instance is None:
            cls._instance = super(Capture, cls).__new__(cls)
        return cls._instance

    def __init__(self, enabled=missing, include_print=missing):
        if hasattr(self, "stdout"):
            if enabled is not missing:
                self.enabled = enabled
            if include_print is not missing:
                self.include_print = include_print
            return
        self.stdout = sys.stdout
        self._buffer = []
        self.enabled = True if enabled is missing else enabled
        self.include_print = False if include_print is missing else include_print

    def __call__(self, enabled=missing, include_print=missing):
        return self.__class__(enabled, include_print)

    def __enter__(self):
        self.enabled = True

    def __exit__(self, exc_type, exc_value, tb):
        self.enabled = False

    def write(self, data):
        self._buffer.append(data)
        if self._include_print:
            self.stdout.write(data)

    def flush(self):
        if self._include_print:
            self.stdout.flush()
        self._buffer.append("\n")

    @property
    def enabled(self):
        return sys.out == self

    @enabled.setter
    def enabled(self, value):
        if value:
            sys.stdout = self
        else:
            sys.stdout = self.stdout

    @property
    def value(self):
        result = self.value_keep
        self.clear()
        return result

    @property
    def value_keep(self):
        result = [[line] for line in self.str_keep.splitlines()]
        return result

    @property
    def str(self):
        result = self.str_keep
        self._buffer.clear()
        return result

    @property
    def str_keep(self):
        result = "".join(self._buffer)
        return result

    def clear(self):
        self._buffer.clear()

    @property
    def include_print(self):
        return self._include_print

    @include_print.setter
    def include_print(self, value):
        self._include_print = value


def trigger_macro(sheet):
    """
    triggers the macro on sheet

    Parameters
    ----------
    sheet : sheet
        sheet to use

    """

    sheet["A1"].value = "=NOW()"


def timer(func):
    """
    this decorator should be placed after the @xw.script decorator

    it will show the name, entry time, exit time and the duration, like
    Done MyScript  11:51:13.24 - 11:51:20.28 (7.04s)

    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        now0 = datetime.datetime.now()
        result = func(*args, **kwargs)
        now1 = datetime.datetime.now()
        diff = (now1 - now0).total_seconds()
        print(f"Done {func.__name__}  {now0:%H:%M:%S.}{int(now0.microsecond / 10000):02d} - {now1:%H:%M:%S.}{int(now1.microsecond / 10000):02d} ({diff:.2f}s)")

        return result

    return wrapper


if __name__ == "__main__":
    ...
