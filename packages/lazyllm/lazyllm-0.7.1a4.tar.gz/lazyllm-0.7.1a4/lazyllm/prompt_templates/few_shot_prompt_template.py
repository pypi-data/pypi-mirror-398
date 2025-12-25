from typing import Dict, List, Any, Set
from pydantic import ConfigDict, Field, model_validator

from lazyllm.prompt_templates.base import BasePromptTemplate
from lazyllm.prompt_templates.prompt_template import PromptTemplate


class FewShotPromptTemplate(BasePromptTemplate):
    """A few-shot prompt template class for constructing structured prompts with examples.

The template consists of three parts: a prefix, multiple formatted examples, and a suffix.
Each example is rendered using the provided egs_prompt_template. It supports partial variable binding,
allowing some variables to be pre-filled while others are supplied at final formatting time.

All template variables (from prefix and suffix) must be exactly covered by the union of 
required_vars (provided at runtime) and partial_vars (pre-bound).

Attributes:
    prefix (str): Introductory text before examples, may contain variable placeholders
    suffix (str): Instruction or question after examples, may contain variable placeholders
    examples (List[Dict]): List of example dictionaries, each must match egs_prompt_template's variables
    egs_prompt_template (PromptTemplate): Sub-template used to format each example
    required_vars (List[str]): List of variable names that must be provided in the final format call
    partial_vars (Dict[str, Any]): Pre-bound variables; values can be constants or zero-argument callables
    separator_for_egs (str): Separator between examples, defaults to newline '\n'
"""
    model_config = ConfigDict(frozen=True)
    prefix: str = Field(..., description='The prefix text that comes before examples, it may include variables')
    suffix: str = Field(..., description='The suffix text that comes after examples, it may include variables')
    examples: List[Dict[str, Any]] = Field(default_factory=list, description='List of example dictionaries')
    egs_prompt_template: PromptTemplate = Field(..., description='Template for formatting each example')
    required_vars: List[str] = Field(
        default_factory=list, description='List of required variable names for the final prompt'
    )
    partial_vars: Dict[str, Any] = Field(
        default_factory=dict, description='Dictionary of partial variable functions or values'
    )
    separator_for_egs: str = Field(default='\n', description='The separator between examples')

    @model_validator(mode='after')
    def validate_variables(self):
        """A model validator automatically invoked after instance creation to ensure consistency 
between template variables and examples.

Performs the following checks:
1. All keys in partial_vars must appear as variables in the prefix or suffix;
2. required_vars and partial_vars must be disjoint (no overlap);
3. The union of required_vars and partial_vars must exactly match all variables in prefix and suffix;
4. Each example dictionary must contain all variables required by egs_prompt_template.

Raises ValueError if any check fails.

This method guarantees that the template is valid and self-consistent before use.
"""
        # 1. All keys in partial_vars must exist in the combined prefix+suffix variables
        # 2. required_vars + partial_vars keys must exactly equal all template variables
        # 3. Examples must be compatible with egs_prompt_template

        # all variables: variables in prefix + suffix.
        # Note: egs_prompt_template variables are not included here.
        all_vars = self._get_all_variables()

        # Check if partial_vars.keys() exist in template variables
        partial_vars_keys = set(self.partial_vars.keys())
        invalid_partial_vars = partial_vars_keys - all_vars
        if invalid_partial_vars:
            raise ValueError(f'partial_vars contains variables not found in template: {invalid_partial_vars}')

        required_vars_set = set(self.required_vars)
        # Check if required_vars and partial_vars have overlap
        overlap_vars = required_vars_set & partial_vars_keys
        if overlap_vars:
            raise ValueError(f'required_vars and partial_vars have overlap: {overlap_vars}')

        # Check if required_vars + partial_vars keys exactly equal all template variables
        combined_vars = required_vars_set | partial_vars_keys
        if combined_vars != all_vars:
            missing_vars = all_vars - combined_vars
            extra_vars = combined_vars - all_vars
            error_msg = []
            if missing_vars:
                error_msg.append(f'Missing variables in required_vars or partial_vars: {missing_vars}')
            if extra_vars:
                error_msg.append(f'Extra variables not found in template: {extra_vars}')
            raise ValueError('; '.join(error_msg))

        # Check each example is compatible with egs_prompt_template
        if self.examples:
            egs_required_vars = set(self.egs_prompt_template.required_vars)
            for i, example in enumerate(self.examples):
                example_keys = set(example.keys())
                missing_egs_vars = egs_required_vars - example_keys
                if missing_egs_vars:
                    raise ValueError(f'Example {i} missing required variables : {missing_egs_vars}')
        return self

    def format(self, **kwargs) -> str:
        """Generates a complete few-shot prompt string by filling in the provided variables.

All variables listed in required_vars must be provided via kwargs. Variables in partial_vars 
are automatically applied (callable values are invoked) and will override any same-named kwargs.
Each example is formatted using egs_prompt_template, joined by separator_for_egs, and combined 
with prefix and suffix to produce the final prompt.

Args:
    **kwargs: Keyword arguments containing all required_vars

Returns:
    str: The fully rendered prompt text

Raises:
    KeyError: If any required variable is missing or an unbound variable exists in the template
    ValueError: If example formatting or final template rendering fails
"""
        # Check if all required variables are provided
        missing_vars = set(self.required_vars) - set(kwargs.keys())
        if missing_vars:
            raise KeyError(f'Missing required variables: {missing_vars}')

        # 1. Apply partial variables. Note: Overrides the values in kwargs if var_name exists in partial_vars
        format_kwargs = {**kwargs}
        for var_name in self.partial_vars:
            try:
                # Apply partial variable function
                val = self.partial_vars[var_name]
                if callable(val):
                    format_kwargs[var_name] = val()
                else:
                    format_kwargs[var_name] = val
            except Exception as e:
                raise TypeError(f'Error applying partial function for variable "{var_name}": {e}')

        # 2. Format examples
        formatted_examples = []
        sep = self.separator_for_egs
        for example in self.examples:
            try:
                formatted_example = self.egs_prompt_template.format(**example)
                formatted_examples.append(formatted_example)
            except Exception as e:
                raise ValueError(f'Error formatting example {example}: {e}')

        # 3. Combine prefix, examples(already formatted), and suffix
        examples_text = sep.join(formatted_examples)

        # 4. Format the final prompt
        try:
            final_template = f'{self.prefix}\n{examples_text}\n{self.suffix}'
            return final_template.format(**format_kwargs)
        except KeyError as e:
            raise KeyError(f'Template variable not found: {e}')
        except Exception as e:
            raise ValueError(f'Error formatting template: {e}')

    def partial(self, **kwargs) -> 'FewShotPromptTemplate':
        """Partially binds variables to the template and returns a new FewShotPromptTemplate instance.

The provided variables are moved from required_vars to partial_vars in the new instance,
so they no longer need to be supplied in subsequent format calls. Useful for incrementally 
binding variables or creating reusable partially-filled templates.

Args:
    **kwargs: Variable names and values to pre-bind (values can be constants or zero-argument callables)

Returns:
    FewShotPromptTemplate: A new template instance with the specified variables bound

Raises:
    KeyError: If any variable in kwargs is not present in the template
"""
        # Check if all partial variables exist in the template
        all_vars = self._get_all_variables()

        invalid_vars = set(kwargs.keys()) - all_vars
        if invalid_vars:
            raise KeyError(f'Variables not found in template: {invalid_vars}')

        # Create new partial_vars dict with additional partial functions
        new_partial_vars = self.partial_vars.copy()
        new_required_vars = list(set(self.required_vars) - set(kwargs.keys()))
        for var_name, var_value in kwargs.items():
            new_partial_vars[var_name] = var_value

        # Create new template with updated partial_vars
        return FewShotPromptTemplate(
            prefix=self.prefix,
            suffix=self.suffix,
            examples=self.examples.copy(),
            egs_prompt_template=self.egs_prompt_template,
            required_vars=new_required_vars,
            partial_vars=new_partial_vars
        )

    def _get_all_variables(self) -> Set[str]:
        prefix_vars = set(BasePromptTemplate.get_template_variables(self.prefix))
        suffix_vars = set(BasePromptTemplate.get_template_variables(self.suffix))
        return prefix_vars | suffix_vars
