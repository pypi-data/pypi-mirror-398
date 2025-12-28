from __future__ import annotations

import collections
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

import sukta.utils.tree as tree
from sukta.sem.structure_parsing import recursive_folder_parsing


class ResultManager:
    """A manager for experimental results.
    It takes care of collecting results organized in different folders.
    """

    def __init__(
        self,
        root_dir: Path,
        parsers: List[re.Pattern],
        dataframe: Optional[pd.DataFrame] = None,
    ):
        """Initialize the ResultManager.

        :param root_dir: root directory.
        :param parsers: list of regular expression patterns.
        :param dataframe: optional dataframe of already parsed arguments.
        """
        self.root_dir = Path(root_dir)
        self.parsers = parsers
        self.df = dataframe

    @classmethod
    def from_arguments(
        cls,
        root_dir: Path,
        arguments: List[Dict[str, str] | str] | Dict[str, str] | str,
        auto_sort: bool = True,
    ) -> ResultManager:
        """Create an instance of ResultManager from the given arguments.
        The single can be specified in two ways:
        - as a single string. In this case there will be no parsing and only folders
        with the specified name will be parsed
        - as a {key: value} dictionary. In this case, every key is the name of a
        parameter, and the value is a string specifying the regular expression for
        parsing.

        If a list of arguments is provided, this specifies a hierarchical folder
        structure, every level has parsing specified by the relative list argument.
        If auto_sort is set to True, within every dictionary the arguments are sorted in
        a canonical way.

        :param root_dir: root directory
        :param arguments: arguments, see `help(ResultManager)`
        :param auto_sort: whether to sort the arguments in the canonical order
        :return: a ArgumentManager instance
        """
        if not isinstance(arguments, list):
            arguments = [arguments]

        parsers = [
            re.compile(_pattern_from_arguments(arg, auto_sort)) for arg in arguments
        ]

        return ResultManager(root_dir, parsers)

    @classmethod
    def create_default_path(
        cls,
        root_dir: str | Path,
        values: List[Dict[str, Any] | str] | Dict[str, Any] | str,
        auto_sort: bool = True,
    ) -> Path:
        """Create the default path given

        :param root_dir: root directory
        :param values: the values specifying the directory structure.
            If it is a string, it specifies a simple directory name.
            If it is a dictionary, it specifies the {parameter name: value} that the
            directory name describes.
            If it is a list, it contains the string or dictionaries of values at every
            sub-level of root:dir.
        :param auto_sort: whether to sort the values specified as dictionaries according
            to the canonical order.
        :return: the path to a sub-folder with specified names.
        """
        root_dir = Path(root_dir)
        if not isinstance(values, list | tuple):
            values = [values]

        path = root_dir
        for arg in values:
            dir_name = (
                str(arg)
                if isinstance(arg, str | int | float)
                else _dirname_from_values(arg, auto_sort)
            )
            path = path / dir_name

        return path

    @property
    def patterns(self) -> List[str]:
        return [parser.pattern for parser in self.parsers]

    def parse_paths(self, **kwargs) -> None:
        """Recursively parse the root directory according to the specified parsers."""
        records = [
            {**{"__PATH__": res_path}, **match_group_args}
            for res_path, match_group_args in recursive_folder_parsing(
                self.root_dir, self.parsers
            )
        ]
        self.df = pd.DataFrame.from_records(records, **kwargs)

    def filter_results(
        self,
        equal: Optional[Dict[str, Any]] = None,
        contained: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Filter the results in the result dataframe by row.
        The rows whose column values are equal and/or contained in those specified, are
        returned in the form of a new data frame. Notice that this method is different
        from pandas DataFrame's filter, which filters along both axes and only by
        column or row name.

        :param equal: dictionary of {column name: value} pairs.
            Rows with column value equal to that specified are returned.
        :param contained: dictionary of {column name: iterable of values} pairs:
            Rows with column values contained in those specified are returned.
        :return: a new data frame according to the specified filters.
        """
        filtered = self.df

        if equal is not None:
            for key, val in equal.items():
                mask = filtered[key] == val
                filtered = filtered[mask]

        if contained is not None:
            for key, val in contained.items():
                mask = filtered[key].isin(val)
                filtered = filtered[mask]

        return filtered


# Utility functions specifying how the ResultManager builds the patterns.
# We use the following name convention for the dictionaries of arguments and values:
# - arguments are utilized to build regular expression patterns. They consist of
#   {parameter name: string}, where the string are compiled to regular expression
#   patterns
# - values are concrete {parameter name: value} pairs.
def _pattern_from_arguments(arguments: Dict[str, str] | str, auto_sort=True) -> str:
    if isinstance(arguments, str):
        return arguments

    keys = _sorted_parameters(arguments) if auto_sort else arguments
    pattern = "_".join(_argument_pattern(key, arguments[key]) for key in keys)

    return pattern


def _dirname_from_values(
    values: Dict[str, str] | List[str] | str, auto_sort=True
) -> str:
    # if isinstance(values, list | tuple):
    #     return Path(*(_dirname_from_values(v) for v in values)).as_posix()
    if isinstance(values, str | int | float):
        return str(values)
    flat_dicts = _dict_to_multi_level(values)
    dirname = []
    for d in flat_dicts:
        keys = _sorted_parameters(d) if auto_sort else d
        dirname.append("_".join(_value_pattern(key, d[key]) for key in keys))
    return Path(*dirname).as_posix()


def _dict_to_multi_level(d: Dict):
    L = collections.defaultdict(dict)
    for kp, v in tree.iter_path(d):
        kstr = ".".join(kp)
        L[len(kp)][kstr] = v
    levels = sorted(L)
    return [L[i] for i in levels]


def _sorted_parameters(*params):
    return sorted(*params)


def _argument_pattern(argument: str, expr: str) -> str:
    pattern = f"{argument}=(?P<{argument}>{expr})"
    return pattern


def _value_pattern(argument: str, expr: Any) -> str:
    pattern = f"{argument}={expr}"
    return pattern
