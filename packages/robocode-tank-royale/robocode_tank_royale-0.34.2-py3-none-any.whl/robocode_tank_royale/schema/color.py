"""
Generated Python class from color.schema.yaml
This file is auto-generated. Do not edit manually.
"""


class Color:
    """Represents a color using hexadecimal format for web colors. Note that colors must have a leading number sign (#).
See https://en.wikipedia.org/wiki/Web_colors
"""

    def __init__(self, value: str | None):
        if value is None:
            raise ValueError("The 'value' parameter must be provided.")
        self.value = value
