from lazyllm.module import ModuleBase
from lazyllm.components import ChatPrompter, FunctionCallFormatter
from lazyllm import pipeline, loop, locals, Color, package, FileSystemQueue, colored_text
from .toolsManager import ToolManager
from typing import List, Any, Dict, Union, Callable
from lazyllm.components.prompter.builtinPrompt import FC_PROMPT_PLACEHOLDER
from lazyllm.common.deprecated import deprecated
import re
import json

FC_PROMPT = f'''# Tools

## You have access to the following tools:
## When you need to call a tool, please insert the following command in your reply, \
which can be called zero or multiple times according to your needs.
{FC_PROMPT_PLACEHOLDER}

Don\'t make assumptions about what values to plug into functions.
Ask for clarification if a user request is ambiguous.\n
'''


class StreamResponse():
    """StreamResponse class encapsulates streaming output behavior with configurable prefix and colors.
When streaming is enabled, calling the instance enqueues colored text to a filesystem queue for asynchronous processing or display.

Args:
    prefix (str): Prefix text before the output, typically used to indicate the source or category.
    prefix_color (Optional[str]): Color of the prefix text, supports terminal color codes, defaults to None.
    color (Optional[str]): Color of the main content text, supports terminal color codes, defaults to None.
    stream (bool): Whether to enable streaming output mode, which enqueues text to the filesystem queue, defaults to False.


Examples:
    >>> from lazyllm.tools.agent.functionCall import StreamResponse
    >>> resp = StreamResponse(prefix="[INFO]", prefix_color="green", color="white", stream=True)
    >>> resp("Hello, world!")
    Hello, world!
    """
    def __init__(self, prefix: str, prefix_color: str = None, color: str = None, stream: bool = False):
        self.stream = stream
        self.prefix = prefix
        self.prefix_color = prefix_color
        self.color = color

    def __call__(self, *inputs):
        if self.stream: FileSystemQueue().enqueue(colored_text(f'\n{self.prefix}\n', self.prefix_color))
        if len(inputs) == 1:
            if self.stream: FileSystemQueue().enqueue(colored_text(f'{inputs[0]}', self.color))
            return inputs[0]
        if self.stream: FileSystemQueue().enqueue(colored_text(f'{inputs}', self.color))
        return package(*inputs)


class FunctionCall(ModuleBase):
    """FunctionCall is a single-turn tool invocation class. It is used when the LLM alone cannot answer user queries and requires external knowledge through tool calls.
If the LLM output requires tool calls, the tools are invoked and the combined results (input, model output, tool output) are returned as a list.
If no tool calls are needed, the LLM output is returned directly as a string.

Args:
    llm (ModuleBase): The LLM instance to use, which can be either a TrainableModule or OnlineChatModule.
    tools (List[Union[str, Callable]]): A list of tool names or callable objects that the LLM can use.
    return_trace (Optional[bool]): Whether to return the invocation trace, defaults to False.
    stream (Optional[bool]): Whether to enable streaming output, defaults to False.
    _prompt (Optional[str]): Custom prompt for function call, defaults to automatic selection based on llm type.

Note: Tools in `tools` must include a `__doc__` attribute and describe their purpose and parameters according to the [Google Python Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).


Examples:
    >>> import lazyllm
    >>> from lazyllm.tools import fc_register, FunctionCall
    >>> import json
    >>> from typing import Literal
    >>> @fc_register("tool")
    >>> def get_current_weather(location: str, unit: Literal["fahrenheit", "celsius"] = 'fahrenheit'):
    ...     '''
    ...     Get the current weather in a given location
    ...
    ...     Args:
    ...         location (str): The city and state, e.g. San Francisco, CA.
    ...         unit (str): The temperature unit to use. Infer this from the users location.
    ...     '''
    ...     if 'tokyo' in location.lower():
    ...         return json.dumps({'location': 'Tokyo', 'temperature': '10', 'unit': 'celsius'})
    ...     elif 'san francisco' in location.lower():
    ...         return json.dumps({'location': 'San Francisco', 'temperature': '72', 'unit': 'fahrenheit'})
    ...     elif 'paris' in location.lower():
    ...         return json.dumps({'location': 'Paris', 'temperature': '22', 'unit': 'celsius'})
    ...     else:
    ...         return json.dumps({'location': location, 'temperature': 'unknown'})
    ...
    >>> @fc_register("tool")
    >>> def get_n_day_weather_forecast(location: str, num_days: int, unit: Literal["celsius", "fahrenheit"] = 'fahrenheit'):
    ...     '''
    ...     Get an N-day weather forecast
    ...
    ...     Args:
    ...         location (str): The city and state, e.g. San Francisco, CA.
    ...         num_days (int): The number of days to forecast.
    ...         unit (Literal['celsius', 'fahrenheit']): The temperature unit to use. Infer this from the users location.
    ...     '''
    ...     if 'tokyo' in location.lower():
    ...         return json.dumps({'location': 'Tokyo', 'temperature': '10', 'unit': 'celsius', "num_days": num_days})
    ...     elif 'san francisco' in location.lower():
    ...         return json.dumps({'location': 'San Francisco', 'temperature': '72', 'unit': 'fahrenheit', "num_days": num_days})
    ...     elif 'paris' in location.lower():
    ...         return json.dumps({'location': 'Paris', 'temperature': '22', 'unit': 'celsius', "num_days": num_days})
    ...     else:
    ...         return json.dumps({'location': location, 'temperature': 'unknown'})
    ...
    >>> tools=["get_current_weather", "get_n_day_weather_forecast"]
    >>> llm = lazyllm.TrainableModule("internlm2-chat-20b").start()  # or llm = lazyllm.OnlineChatModule("openai", stream=False)
    >>> query = "What's the weather like today in celsius in Tokyo."
    >>> fc = FunctionCall(llm, tools)
    >>> ret = fc(query)
    >>> print(ret)
    ["What's the weather like today in celsius in Tokyo.", {'role': 'assistant', 'content': '
    ', 'tool_calls': [{'id': 'da19cddac0584869879deb1315356d2a', 'type': 'function', 'function': {'name': 'get_current_weather', 'arguments': {'location': 'Tokyo', 'unit': 'celsius'}}}]}, [{'role': 'tool', 'content': '{"location": "Tokyo", "temperature": "10", "unit": "celsius"}', 'tool_call_id': 'da19cddac0584869879deb1315356d2a', 'name': 'get_current_weather'}]]
    >>> query = "Hello"
    >>> ret = fc(query)
    >>> print(ret)
    'Hello! How can I assist you today?'
    """

    def __init__(self, llm, tools: List[Union[str, Callable]], *, return_trace: bool = False,
                 stream: bool = False, _prompt: str = None):
        super().__init__(return_trace=return_trace)

        self._tools_manager = ToolManager(tools, return_trace=return_trace)
        self._prompter = ChatPrompter(instruction=_prompt or FC_PROMPT, tools=self._tools_manager.tools_description)
        self._llm = llm.share(prompt=self._prompter, format=FunctionCallFormatter()).used_by(self._module_id)
        with pipeline() as self._impl:
            self._impl.ins = StreamResponse('Received instruction:', prefix_color=Color.yellow,
                                            color=Color.green, stream=stream)
            self._impl.pre_action = self._build_history
            self._impl.llm = self._llm
            self._impl.dis = StreamResponse('Decision-making or result in this round:',
                                            prefix_color=Color.yellow, color=Color.green, stream=stream)
            self._impl.post_action = self._post_action

    def _build_history(self, input: Union[str, list]):
        history_idx = len(locals['_lazyllm_agent']['workspace'].setdefault('history', []))
        if isinstance(input, str):
            locals['_lazyllm_agent']['workspace']['history'].append({'role': 'user', 'content': input})
        elif isinstance(input, dict):
            tool_call_results = [
                {
                    'role': 'tool',
                    'content': str(tool_call['tool_call_result']),
                    'tool_call_id': tool_call['id'],
                    'name': tool_call['function']['name'],
                } for tool_call in locals['_lazyllm_agent']['workspace']['tool_call_trace']
            ]
            locals['_lazyllm_agent']['workspace']['history'].append(
                {'role': 'assistant', 'content': input.get('content', ''), 'tool_calls': input.get('tool_calls', [])}
            )
            input = {'input': tool_call_results}
            history_idx += 1
            locals['_lazyllm_agent']['workspace']['history'].extend(tool_call_results)
        locals['chat_history'][self._llm._module_id] = locals['_lazyllm_agent']['workspace']['history'][:history_idx]
        return input

    def _post_action(self, llm_output: Dict[str, Any]):
        if not llm_output.get('tool_calls'):
            if (match := re.search(r'Action:\s*Call\s+(\w+)\s+with\s+parameters\s+(\{.*?\})', llm_output['content'])):
                try:
                    llm_output['tool_calls'] = [{'function': {'name': match.group(1),
                                                              'arguments': json.loads(match.group(2))}}]
                except Exception: pass
        if tool_calls := llm_output.get('tool_calls'):
            if isinstance(tool_calls, list): [item.pop('index', None) for item in tool_calls]
            tool_calls_results = self._tools_manager(tool_calls)
            locals['_lazyllm_agent']['workspace']['tool_call_trace'] = [
                {**tool_call, 'tool_call_result': tool_result}
                for tool_call, tool_result in zip(tool_calls, tool_calls_results)
            ]
        else:
            llm_output = llm_output['content']
        return llm_output

    def forward(self, input: str, llm_chat_history: List[Dict[str, Any]] = None):
        if 'workspace' not in locals['_lazyllm_agent']:
            locals['_lazyllm_agent']['workspace'] = dict(history=llm_chat_history or [])
        result = self._impl(input)

        # If the model decides not to call any tools, the result is a string. For debugging and subsequent tasks,
        # the last non-empty tool call trace is stored in locals['_lazyllm_agent']['completed'].
        if isinstance(result, str):
            locals['_lazyllm_agent']['completed'] = locals['_lazyllm_agent'].pop('workspace')\
                .pop('tool_call_trace', locals['_lazyllm_agent'].get('completed', []))
            locals['chat_history'][self._llm._module_id] = []
        return result

@deprecated('ReactAgent')
class FunctionCallAgent(ModuleBase):
    """(FunctionCallAgent is deprecated and will be removed in a future version. Please use ReactAgent instead.) FunctionCallAgent is an agent that uses the tool calling method to perform complete tool calls. That is, when answering uesr questions, if LLM needs to obtain external knowledge through the tool, it will call the tool and feed back the return results of the tool to LLM, which will finally summarize and output them.

Args:
    llm (ModuleBase): The LLM to be used can be either TrainableModule or OnlineChatModule.
    tools (List[str]): A list of tool names for LLM to use.
    max_retries (int): The maximum number of tool call iterations. The default value is 5.
    return_trace (bool): Whether to return execution trace information, defaults to False.
    stream (bool): Whether to enable streaming output, defaults to False.


Examples:
    >>> import lazyllm
    >>> from lazyllm.tools import fc_register, FunctionCallAgent
    >>> import json
    >>> from typing import Literal
    >>> @fc_register("tool")
    >>> def get_current_weather(location: str, unit: Literal["fahrenheit", "celsius"]='fahrenheit'):
    ...     '''
    ...     Get the current weather in a given location
    ...
    ...     Args:
    ...         location (str): The city and state, e.g. San Francisco, CA.
    ...         unit (str): The temperature unit to use. Infer this from the users location.
    ...     '''
    ...     if 'tokyo' in location.lower():
    ...         return json.dumps({'location': 'Tokyo', 'temperature': '10', 'unit': 'celsius'})
    ...     elif 'san francisco' in location.lower():
    ...         return json.dumps({'location': 'San Francisco', 'temperature': '72', 'unit': 'fahrenheit'})
    ...     elif 'paris' in location.lower():
    ...         return json.dumps({'location': 'Paris', 'temperature': '22', 'unit': 'celsius'})
    ...     elif 'beijing' in location.lower():
    ...         return json.dumps({'location': 'Beijing', 'temperature': '90', 'unit': 'Fahrenheit'})
    ...     else:
    ...         return json.dumps({'location': location, 'temperature': 'unknown'})
    ...
    >>> @fc_register("tool")
    >>> def get_n_day_weather_forecast(location: str, num_days: int, unit: Literal["celsius", "fahrenheit"]='fahrenheit'):
    ...     '''
    ...     Get an N-day weather forecast
    ...
    ...     Args:
    ...         location (str): The city and state, e.g. San Francisco, CA.
    ...         num_days (int): The number of days to forecast.
    ...         unit (Literal['celsius', 'fahrenheit']): The temperature unit to use. Infer this from the users location.
    ...     '''
    ...     if 'tokyo' in location.lower():
    ...         return json.dumps({'location': 'Tokyo', 'temperature': '10', 'unit': 'celsius', "num_days": num_days})
    ...     elif 'san francisco' in location.lower():
    ...         return json.dumps({'location': 'San Francisco', 'temperature': '75', 'unit': 'fahrenheit', "num_days": num_days})
    ...     elif 'paris' in location.lower():
    ...         return json.dumps({'location': 'Paris', 'temperature': '25', 'unit': 'celsius', "num_days": num_days})
    ...     elif 'beijing' in location.lower():
    ...         return json.dumps({'location': 'Beijing', 'temperature': '85', 'unit': 'fahrenheit', "num_days": num_days})
    ...     else:
    ...         return json.dumps({'location': location, 'temperature': 'unknown'})
    ...
    >>> tools = ['get_current_weather', 'get_n_day_weather_forecast']
    >>> llm = lazyllm.TrainableModule("internlm2-chat-20b").start()  # or llm = lazyllm.OnlineChatModule(source="sensenova")
    >>> agent = FunctionCallAgent(llm, tools)
    >>> query = "What's the weather like today in celsius in Tokyo and Paris."
    >>> res = agent(query)
    >>> print(res)
    'The current weather in Tokyo is 10 degrees Celsius, and in Paris, it is 22 degrees Celsius.'
    >>> query = "Hello"
    >>> res = agent(query)
    >>> print(res)
    'Hello! How can I assist you today?'
    """
    def __init__(self, llm, tools: List[str], max_retries: int = 5, return_trace: bool = False, stream: bool = False,
                 return_last_tool_calls: bool = False):
        super().__init__(return_trace=return_trace)
        self._max_retries = max_retries
        self._return_last_tool_calls = return_last_tool_calls
        self._fc = FunctionCall(llm, tools, return_trace=return_trace, stream=stream)
        self._agent = loop(self._fc, stop_condition=lambda x: isinstance(x, str), count=self._max_retries)
        self._fc._llm.used_by(self._module_id)

    def forward(self, query: str, llm_chat_history: List[Dict[str, Any]] = None):
        ret = self._agent(query, llm_chat_history) if llm_chat_history is not None else self._agent(query)
        if isinstance(ret, str) and self._return_last_tool_calls and locals['_lazyllm_agent'].get('completed'):
            return locals['_lazyllm_agent'].pop('completed')
        return ret if isinstance(ret, str) else (_ for _ in ()).throw(ValueError(f'After retrying \
            {self._max_retries} times, the function call agent still fails to call successfully.'))
