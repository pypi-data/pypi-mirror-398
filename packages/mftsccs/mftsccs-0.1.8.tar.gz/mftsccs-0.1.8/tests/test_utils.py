"""Tests for the utils module."""

import pytest
from ccs.utils import helper_function, validate_input, flatten_list


class TestHelperFunction:
    """Tests for helper_function."""

    def test_helper_function_with_items(self):
        result = helper_function([1, 2, 3])
        assert result == 1

    def test_helper_function_empty_list_with_default(self):
        result = helper_function([], "default")
        assert result == "default"

    def test_helper_function_empty_list_no_default(self):
        result = helper_function([])
        assert result is None


class TestValidateInput:
    """Tests for validate_input."""

    def test_validate_string(self):
        assert validate_input("hello", str) is True

    def test_validate_int(self):
        assert validate_input(42, int) is True

    def test_validate_wrong_type(self):
        assert validate_input("hello", int) is False


class TestFlattenList:
    """Tests for flatten_list."""

    def test_flatten_nested_lists(self):
        result = flatten_list([[1, 2], [3, 4], [5]])
        assert result == [1, 2, 3, 4, 5]

    def test_flatten_empty_lists(self):
        result = flatten_list([[], [], []])
        assert result == []

    def test_flatten_single_element_lists(self):
        result = flatten_list([[1], [2], [3]])
        assert result == [1, 2, 3]
