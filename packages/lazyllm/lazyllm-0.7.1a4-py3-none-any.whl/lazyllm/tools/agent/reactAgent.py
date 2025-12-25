from lazyllm.module import ModuleBase
from lazyllm import loop, locals
from .functionCall import FunctionCall
from typing import List, Any, Dict
from lazyllm.components.prompter.builtinPrompt import FC_PROMPT_PLACEHOLDER

INSTRUCTION = f'''You are designed to help with a variety of tasks, from answering questions to providing \
summaries to other types of analyses.

## Tools

You have access to a wide variety of tools. You are responsible for using the tools in any sequence \
you deem appropriate to complete the task at hand.
This may require breaking the task into subtasks and using different tools to complete each subtask.

You have access to the following tools:

## Output Format

Please answer in the same language as the question and use the following format:

Thought: The current language of the user is: (user's language). I need to use a tool to help answer the question.
{FC_PROMPT_PLACEHOLDER}
Answering questions should include Thought regardless of whether or not you need to \
call a tool.(Thought is required, tool_calls is optional.)

Please ALWAYS start with a Thought and Only ONE Thought at a time.

You should keep repeating the above format till you have enough information to answer the question without using \
any more tools. At that point, you MUST respond in the following formats:

Answer: your answer here (In the same language as the user's question)

## Current Conversation

Below is the current conversation consisting of interleaving human and assistant messages. Think step by step.'''


class ReactAgent(ModuleBase):
    """ReactAgent follows the process of `Thought->Action->Observation->Thought...->Finish` step by step through LLM and tool calls to display the steps to solve user questions and the final answer to the user.

Args:
    llm: Large language model instance for generating reasoning and tool calling decisions
    tools (List[str]): List of available tools, can be tool functions or tool names
    max_retries (int): Maximum retry count, automatically retries when tool calling fails, defaults to 5
    return_trace (bool): Whether to return complete execution trace for debugging and analysis, defaults to False
    prompt (str): Custom prompt template, uses built-in template if None
    stream (bool): Whether to enable streaming output for real-time generation display, defaults to False



Examples:
    >>> import lazyllm
    >>> from lazyllm.tools import fc_register, ReactAgent
    >>> @fc_register("tool")
    >>> def multiply_tool(a: int, b: int) -> int:
    ...     '''
    ...     Multiply two integers and return the result integer
    ...
    ...     Args:
    ...         a (int): multiplier
    ...         b (int): multiplier
    ...     '''
    ...     return a * b
    ...
    >>> @fc_register("tool")
    >>> def add_tool(a: int, b: int):
    ...     '''
    ...     Add two integers and returns the result integer
    ...
    ...     Args:
    ...         a (int): addend
    ...         b (int): addend
    ...     '''
    ...     return a + b
    ...
    >>> tools = ["multiply_tool", "add_tool"]
    >>> llm = lazyllm.TrainableModule("internlm2-chat-20b").start()   # or llm = lazyllm.OnlineChatModule(source="sensenova")
    >>> agent = ReactAgent(llm, tools)
    >>> query = "What is 20+(2*4)? Calculate step by step."
    >>> res = agent(query)
    >>> print(res)
    'Answer: The result of 20+(2*4) is 28.'
    """
    def __init__(self, llm, tools: List[str], max_retries: int = 5, return_trace: bool = False,
                 prompt: str = None, stream: bool = False, return_last_tool_calls: bool = False):
        super().__init__(return_trace=return_trace)
        self._max_retries = max_retries
        self._return_last_tool_calls = return_last_tool_calls
        prompt = prompt or INSTRUCTION
        if self._return_last_tool_calls:
            prompt += '\nIf no more tool calls are needed, reply with ok and skip any summary.'
        assert llm and tools, 'llm and tools cannot be empty.'
        self._agent = loop(FunctionCall(llm, tools, _prompt=prompt, return_trace=return_trace, stream=stream),
                           stop_condition=lambda x: isinstance(x, str), count=self._max_retries)

    def forward(self, query: str, llm_chat_history: List[Dict[str, Any]] = None):
        ret = self._agent(query, llm_chat_history or [])
        if isinstance(ret, str) and self._return_last_tool_calls and locals['_lazyllm_agent'].get('completed'):
            return locals['_lazyllm_agent'].pop('completed')
        return ret if isinstance(ret, str) else (_ for _ in ()).throw(ValueError(f'After retrying \
            {self._max_retries} times, the react agent still failes to call successfully.'))
