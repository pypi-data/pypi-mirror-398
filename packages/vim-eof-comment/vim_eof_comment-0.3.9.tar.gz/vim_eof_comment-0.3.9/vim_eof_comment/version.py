# -*- coding: utf-8 -*-
# Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
Custom vim-eof-comment versioning objects.

Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
__all__ = ["VersionInfo", "list_versions", "version_info"]

from typing import List, NoReturn, Tuple

from .util import die


class VersionInfo():
    """
    A sys-inspired version_info object type.

    Parameters
    ----------
    all_versions : List[Tuple[int, int, int]]
        A list of three number tuples, containing (in order) the major, minor and patch
        components.

    Attributes
    ----------
    major : int
        The major component of the version.
    minor : int
        The minor component of the version.
    patch : int
        The patch component of the version.
    all_versions : List[Tuple[int, int, int]]
        A list of tuples containing all the versions in the object instance.

    Methods
    -------
    get_all_versions()
    """

    major: int
    minor: int
    patch: int
    all_versions: List[Tuple[int, int, int]]

    def __init__(self, all_versions: List[Tuple[int, int, int]]):
        """
        Initialize VersionInfo object.

        Parameters
        ----------
        all_versions : List[Tuple[int, int, int]]
            A list of tuples of three-integers, containing (in order) the major, minor and patch
            components.
        """
        self.all_versions = all_versions.copy()

        all_versions = all_versions.copy()[::-1]
        self.major = all_versions[0][0]
        self.minor = all_versions[0][1]
        self.patch = all_versions[0][2]

    def __str__(self) -> str:
        """
        Representate this object as a string.

        This is what is returned when using ``str(VersionInfo(...))``.

        Returns
        -------
        str
            The string representation of the instance.

        Examples
        --------
        Only one definition in constructor.

        >>> from vim_eof_comment.version import VersionInfo
        >>> print(str(VersionInfo([(0, 0, 1)])))
        0.0.1

        Multiple definitions in constructor.

        >>> from vim_eof_comment.version import VersionInfo
        >>> print(str(VersionInfo([(0, 0, 1), (0, 0, 2)])))
        0.0.2
        """
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        """
        Representate this object as a string.

        This is what is returned when using ``print(VersionInfo(...))``.

        Returns
        -------
        str
            The string representation of the instance.

        Examples
        --------
        Only one definition in constructor.

        >>> from vim_eof_comment.version import VersionInfo
        >>> print(VersionInfo([(0, 0, 1)]))
        0.0.1

        Multiple definitions in constructor.

        >>> from vim_eof_comment.version import VersionInfo
        >>> print(VersionInfo([(0, 0, 1), (0, 0, 2)]))
        0.0.2
        """
        return self.__str__()

    def __eq__(self, b) -> bool:
        """
        Check the equality between two ``VersionInfo`` instances.

        Parameters
        ----------
        b : VersionInfo
            The other instance to compare.

        Returns
        -------
        bool
            Whether they are equal or not.
        """
        if not isinstance(b, VersionInfo):
            return False

        b: VersionInfo = b
        return self.major == b.major and self.minor == b.minor and self.patch == b.patch

    def get_all_versions(self) -> str:
        r"""
        Retrieve all versions as a string.

        Returns
        -------
        str
            A string, containing the program versions, in ascending order.

        Examples
        --------
        To generate a single string.
        >>> from vim_eof_comment.version import VersionInfo
        >>> print(VersionInfo([(0, 0, 1), (0, 0, 2), (0, 1, 0)]).get_all_versions())
        0.0.1
        0.0.2
        0.0.3 (latest)
        """
        result = ""
        for i, info in enumerate(self.all_versions):
            result += f"{info[0]}.{info[1]}.{info[2]}"
            if i == len(self.all_versions) - 1:
                result += " (latest)"
            else:
                result += "\n"

        return result


version_info: VersionInfo = VersionInfo([
    (0, 1, 1),
    (0, 1, 2),
    (0, 1, 3),
    (0, 1, 4),
    (0, 1, 5),
    (0, 1, 6),
    (0, 1, 7),
    (0, 1, 8),
    (0, 1, 9),
    (0, 1, 10),
    (0, 1, 11),
    (0, 1, 12),
    (0, 1, 13),
    (0, 1, 14),
    (0, 1, 15),
    (0, 1, 16),
    (0, 1, 17),
    (0, 1, 18),
    (0, 1, 19),
    (0, 1, 20),
    (0, 1, 21),
    (0, 1, 22),
    (0, 1, 23),
    (0, 1, 24),
    (0, 1, 25),
    (0, 1, 26),
    (0, 1, 27),
    (0, 1, 28),
    (0, 1, 29),
    (0, 1, 30),
    (0, 1, 31),
    (0, 1, 32),
    (0, 1, 33),
    (0, 1, 34),
    (0, 1, 35),
    (0, 1, 36),
    (0, 1, 37),
    (0, 1, 38),
    (0, 2, 0),
    (0, 2, 1),
    (0, 2, 2),
    (0, 2, 3),
    (0, 3, 0),
    (0, 3, 1),
    (0, 3, 2),
    (0, 3, 3),
    (0, 3, 4),
    (0, 3, 5),
    (0, 3, 6),
    (0, 3, 7),
    (0, 3, 8),
    (0, 3, 9),
])


def list_versions() -> NoReturn:
    """List all versions."""
    all_versions: str = version_info.get_all_versions()
    die(all_versions, code=0)

# vim: set ts=4 sts=4 sw=4 et ai si sta:
