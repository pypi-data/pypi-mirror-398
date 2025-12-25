from abc import ABC
from string import Formatter
from pydantic import BaseModel


class BasePromptTemplate(BaseModel, ABC):

    @staticmethod
    def get_template_variables(template: str) -> list[str]:
        """Extracts all placeholder variable names from a given template string.

Uses Python's built-in string.Formatter to parse the template and identify placeholders 
. Returns a sorted list of unique variable names.

Args:
    template (str): A prompt template string containing placeholders
                    

Returns:
    list[str]: A sorted list of placeholder variable names

Raises:
    ValueError: If the template is malformed or parsing fails
"""
        try:
            input_variables = {
                v for _, v, _, _ in Formatter().parse(template) if v is not None
            }
            return sorted(input_variables)
        except Exception as e:
            raise ValueError(f'Error getting template variables: {e}')
