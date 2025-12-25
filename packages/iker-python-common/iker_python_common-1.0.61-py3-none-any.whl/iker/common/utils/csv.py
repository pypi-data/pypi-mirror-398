import os
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
from typing import Any
from typing import overload

__all__ = [
    "CSVColumn",
    "CSVView",
    "column",
    "view",
]


class CSVColumn(object):
    """
    Represents a column in a CSV schema, including its name, loader function, dumper function, and the string used for
    null values.

    :param name: The name of the column.
    :param loader: A function to convert a string to the column's value type.
    :param dumper: A function to convert the column's value to a string.
    :param null_str: The string representation of a null value in this column.
    """

    def __init__(
        self,
        name: str,
        loader: Callable[[str], Any] = str,
        dumper: Callable[[Any], str] = str,
        null_str: str = "",
    ):
        self.name = name
        self.loader = loader
        self.dumper = dumper
        self.null_str = null_str


class CSVView(object):
    """
    Represents a view for reading and writing CSV data according to a schema. Supports loading and dumping lines or
    files, with options for headers and dictionary or list output.

    :param schema: The sequence of ``CSVColumn`` objects defining the schema.
    :param row_delim: The delimiter for rows (default is ``'\n'``).
    :param col_delim: The delimiter for columns (default is ``','``).
    """

    def __init__(self, schema: Sequence[CSVColumn], *, row_delim: str = "\n", col_delim: str = ","):
        self.schema = schema
        self.row_delim = row_delim
        self.col_delim = col_delim

    @overload
    def load_lines(
        self,
        lines: Iterable[str],
        has_header: bool,
        ret_dict: False = False,
    ) -> Generator[list[Any], None, None]:
        ...

    @overload
    def load_lines(
        self,
        lines: Iterable[str],
        ret_dict: False = False,
    ) -> Generator[list[Any], None, None]:
        ...

    @overload
    def load_lines(
        self,
        lines: Iterable[str],
        has_header: bool,
        ret_dict: True = True,
    ) -> Generator[dict[str, Any], None, None]:
        ...

    @overload
    def load_lines(
        self,
        lines: Iterable[str],
        ret_dict: True = True,
    ) -> Generator[dict[str, Any], None, None]:
        ...

    def load_lines(
        self,
        lines: Iterable[str],
        has_header: bool = True,
        ret_dict: bool = False,
    ) -> Generator[list[Any] | dict[str, Any], None, None]:
        """
        Loads CSV data from an iterable of lines, optionally using the first line as a header. Returns each row as a
        list or dictionary, depending on ``ret_dict``.

        :param lines: An iterable of CSV lines.
        :param has_header: Whether the first line is a header.
        :param ret_dict: Whether to return rows as dictionaries (``True``) or lists (``False``).
        :return: A generator yielding each row as a list or dictionary.
        """
        rows_iter = iter(lines)
        if has_header:
            header_row = next(rows_iter)
            header_cols = header_row.split(self.col_delim)
            if len(self.schema) != len(header_cols):
                raise ValueError("size of the schema is not identical to size of the columns")
            for c, header_col in zip(self.schema, header_cols):
                if c.name != header_col:
                    raise ValueError("name of the schema is not equal to the name of the columns")
        for row in rows_iter:
            cols = row.split(self.col_delim)
            if len(self.schema) != len(cols):
                continue
            if ret_dict:
                yield {c.name: None if col == c.null_str else c.loader(col) for c, col in zip(self.schema, cols)}
            else:
                yield [None if col == c.null_str else c.loader(col) for c, col in zip(self.schema, cols)]

    def dump_lines(
        self,
        data: Iterable[Sequence[Any] | Mapping[str, Any]],
        has_header: bool = True,
    ) -> Generator[str, None, None]:
        """
        Dumps data to CSV lines according to the schema, optionally including a header row.

        :param data: An iterable of rows, each as a sequence or mapping.
        :param has_header: Whether to include a header row.
        :return: A generator yielding CSV lines as strings.
        """
        if has_header:
            yield self.col_delim.join(c.name for c in self.schema)
        for cols in data:
            if isinstance(cols, Sequence):
                if len(self.schema) != len(cols):
                    raise ValueError("size of the schema is not identical to size of the columns")
                yield self.col_delim.join(c.null_str if col is None else c.dumper(col)
                                          for c, col in zip(self.schema, cols))
            if isinstance(cols, Mapping):
                yield self.col_delim.join(c.null_str if cols.get(c.name) is None else c.dumper(cols.get(c.name))
                                          for c in self.schema)

    @overload
    def load_file(
        self,
        file_path: os.PathLike | str,
        has_header: bool,
        ret_dict: False = False,
        **kwargs,
    ) -> Generator[list[Any], None, None]:
        ...

    @overload
    def load_file(
        self,
        file_path: os.PathLike | str,
        ret_dict: False = False,
        **kwargs,
    ) -> Generator[list[Any], None, None]:
        ...

    @overload
    def load_file(
        self,
        file_path: os.PathLike | str,
        has_header: bool,
        ret_dict: True = True,
        **kwargs,
    ) -> Generator[dict[str, Any], None, None]:
        ...

    @overload
    def load_file(
        self,
        file_path: os.PathLike | str,
        ret_dict: True = True,
        **kwargs,
    ) -> Generator[dict[str, Any], None, None]:
        ...

    def load_file(
        self,
        file_path: os.PathLike | str,
        has_header: bool = True,
        ret_dict: bool = False,
        **kwargs,
    ) -> Generator[list[Any] | dict[str, Any], None, None]:
        """
        Loads CSV data from a file, splitting by row delimiter and using the ``schema`` for parsing.

        :param file_path: The path to the CSV file.
        :param has_header: Whether the first line is a header.
        :param ret_dict: Whether to return rows as dictionaries (``True``) or lists (``False``).
        :param kwargs: Additional keyword arguments for file opening.
        :return: A generator yielding each row as a list or dictionary.
        """
        with open(file_path, mode="r", **kwargs) as fh:
            lines = fh.read().split(self.row_delim)
            yield from self.load_lines(lines, has_header, ret_dict)

    def dump_file(
        self,
        data: Iterable[Sequence[Any] | Mapping[str, Any]],
        file_path: os.PathLike | str,
        has_header: bool = True,
        **kwargs,
    ) -> None:
        """
        Dumps data to a CSV file according to the ``schema``, optionally including a header row.

        :param data: An iterable of rows, each as a sequence or mapping.
        :param file_path: The path to the output CSV file.
        :param has_header: Whether to include a header row.
        :param kwargs: Additional keyword arguments for file opening.
        """
        with open(file_path, mode="w", **kwargs) as fh:
            for line in self.dump_lines(data, has_header):
                fh.write(line)
                fh.write(self.row_delim)


column = CSVColumn
view = CSVView
