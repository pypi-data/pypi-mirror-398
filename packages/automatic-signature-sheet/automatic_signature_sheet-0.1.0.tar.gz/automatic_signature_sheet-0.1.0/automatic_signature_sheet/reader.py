# Copyright (c) 2025 Yoann Piétri
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
"""
Module for the readers, that will read information from files and return list of persons.
"""

import os
import abc
import csv
from typing import List, IO
from dataclasses import dataclass


@dataclass
class Person:
    """
    A person, to be included in signature sheets.
    """

    last_name: str
    first_name: str
    person_id: str | None


# pylint: disable=too-few-public-methods
class BaseReader(abc.ABC):
    """A base reader, allowing for extensions."""

    file_location: os.PathLike  #: Location of the file to read from.
    sort: bool  #: If True, the returned list will be sorted by alphabetical order using the last name.

    def __init__(self, file_location: os.PathLike, sort: bool = True):
        """
        Args:
            file_location (os.PathLike): location of the file to read from.
            sort (bool, optional): If True, the returned list will be sorted by alphabetical order using the last name. Defaults to True.
        """
        self.file_location = file_location
        self.sort = sort

    def read(self) -> List[Person]:
        """Read the file and return the list of persons.

        Returns:
            List[Person]: list of persons.
        """
        with open(self.file_location, "r", encoding="utf8") as fd:
            persons = self._read(fd)
        if self.sort:
            return sorted(persons, key=lambda x: x.last_name)
        return persons

    @abc.abstractmethod
    def _read(self, file_descriptor: IO) -> List[Person]:
        pass


# pylint: disable=too-few-public-methods
class CSVReader(BaseReader):
    """Read the persons from a CSV."""

    first_name_column: int
    last_name_column: int
    person_id_column: int | None
    ignore_lines: int

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        file_location: os.PathLike,
        first_name_column: int = 0,
        last_name_column: int = 1,
        person_id_column: int | None = 2,
        ignore_lines: int = 1,
        sort: bool = True,
    ):
        """
        Args:
            file_location (os.PathLike): location of the file to read from.
            first_name_column (int, optional): column for first name (starting from 0). Defaults to 0.
            last_name_column (int, optional): column for last name (starting from 0). Defaults to 1.
            person_id_column (int | None, optional): column for id (starting from 0). If None, all ids are set to None. Defaults to 2.
            ignore_lines (int, optional): number of lines to ignore. Set 0 to ignore no lines. Defaults to 1.
            sort (bool, optional): If True, the returned list will be sorted by alphabetical order using the last name. Defaults to True.
        """
        self.first_name_column = first_name_column
        self.last_name_column = last_name_column
        self.person_id_column = person_id_column
        self.ignore_lines = ignore_lines
        super().__init__(file_location, sort)

    def _read(self, file_descriptor: IO) -> List[Person]:
        reader = csv.reader(file_descriptor)
        persons: List[Person] = []
        for i, line in enumerate(reader):
            if i >= self.ignore_lines:
                last_name = line[self.last_name_column]
                first_name = line[self.first_name_column]
                if self.person_id_column is not None:
                    person_id = line[self.person_id_column]
                else:
                    person_id = None
                student = Person(
                    last_name=last_name,
                    first_name=first_name,
                    person_id=person_id,
                )
                persons.append(student)
        return persons


DefaultReader = CSVReader
