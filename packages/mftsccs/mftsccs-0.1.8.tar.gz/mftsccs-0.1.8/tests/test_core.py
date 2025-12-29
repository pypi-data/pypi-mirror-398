"""Tests for the core module."""

import pytest
from ccs.core import example_function, ExampleClass


class TestExampleFunction:
    """Tests for example_function."""

    def test_example_function_with_string(self):
        result = example_function("hello")
        assert result == "Processed: hello"

    def test_example_function_with_number(self):
        result = example_function(42)
        assert result == "Processed: 42"

    def test_example_function_with_none(self):
        result = example_function(None)
        assert result == "Processed: None"


class TestExampleClass:
    """Tests for ExampleClass."""

    def test_init_with_name_only(self):
        obj = ExampleClass("test")
        assert obj.name == "test"
        assert obj.data is None

    def test_init_with_name_and_data(self):
        obj = ExampleClass("test", data={"key": "value"})
        assert obj.name == "test"
        assert obj.data == {"key": "value"}

    def test_process(self):
        obj = ExampleClass("test")
        result = obj.process("new data")
        assert result == "new data"
        assert obj.data == "new data"

    def test_repr(self):
        obj = ExampleClass("test", data=123)
        assert repr(obj) == "ExampleClass(name='test', data=123)"
