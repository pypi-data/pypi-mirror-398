"""
Core module containing the main functionality of the CCS library.

Add your main functions and classes here that you want to expose
to other projects.
"""

from typing import Any, Optional


def example_function(value: Any) -> str:
    """
    An example function demonstrating how to create exportable functions.

    Args:
        value: Any value to be processed.

    Returns:
        A string representation of the processed value.

    Example:
        >>> from ccs import example_function
        >>> result = example_function("hello")
        >>> print(result)
        'Processed: hello'
    """
    return f"Processed: {value}"


class ExampleClass:
    """
    An example class demonstrating how to create exportable classes.

    This class can be imported by other projects using:
        from ccs import ExampleClass

    Attributes:
        name: The name identifier for this instance.
        data: Optional data storage.

    Example:
        >>> from ccs import ExampleClass
        >>> obj = ExampleClass("my_instance")
        >>> obj.process("some data")
    """

    def __init__(self, name: str, data: Optional[Any] = None) -> None:
        """
        Initialize the ExampleClass.

        Args:
            name: A name identifier for this instance.
            data: Optional initial data.
        """
        self.name = name
        self.data = data

    def process(self, input_data: Any) -> Any:
        """
        Process the input data.

        Args:
            input_data: Data to be processed.

        Returns:
            The processed data.
        """
        self.data = input_data
        return self.data

    def __repr__(self) -> str:
        return f"ExampleClass(name='{self.name}', data={self.data})"
