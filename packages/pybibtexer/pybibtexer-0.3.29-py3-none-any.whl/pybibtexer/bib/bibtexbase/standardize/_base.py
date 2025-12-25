"""Base utilities for BibTeX standardization.

This module provides fundamental utility functions used throughout the
standardization process, particularly for text processing and pattern matching.

Functions:
    split_data_list: Splits a list of strings according to a regex pattern,
        with options for handling the last element differently.
"""

import re


def split_data_list(split_pattern: str, data_list: list[str], last_next: str = "next") -> list[str]:
    r"""Split data list according to the split pattern.

    The capturing parentheses must be used in the pattern, such as `(\n)`.

    Args:
        split_pattern (str): split pattern.
        data_list (list[str]): data list.
        last_next (str): "next" or "last".

    Returns:
        list[str]: new data list.

    Examples:
        split_pattern = r"(\n)", last_next = "next" or "last".
    """
    new_data_list = []
    for line in data_list:
        split_list = re.split(split_pattern, line)
        list_one = split_list[0 : len(split_list) : 2]
        list_two = split_list[1 : len(split_list) : 2]

        temp = []
        if last_next == "next":
            list_two.insert(0, "")
            temp = [list_two[i] + list_one[i] for i in range(len(list_one))]
        if last_next == "last":
            list_two.append("")
            temp = [list_one[i] + list_two[i] for i in range(len(list_one))]
        new_data_list.extend(temp)
    new_data_list = [line for line in new_data_list if line.strip()]
    return new_data_list
