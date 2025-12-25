from lazyllm.module import ModuleBase
from lazyllm import pipeline, LOG, bind, Color, locals, ifs
from .toolsManager import ToolManager
from typing import List, Dict, Union, Callable
import re
import json

P_PROMPT_PREFIX = ('For the following tasks, make plans that can solve the problem step-by-step. '
                   'For each plan, indicate which external tool together with tool input to retrieve '
                   'evidence. You can store the evidence into a variable #E that can be called by '
                   'later tools. (Plan, #E1, Plan, #E2, Plan, #E3...) \n\n')

P_FEWSHOT = '''For example,
Task: We are planning to visit the capital city of China this week. What clothing should we wear for the trip?
Plan: First, search for the capital city of China.
#E1 = search[{"query": "What\'s the capital city of China?"}]
Plan: Next, obtain the weather forecast for this week in the capital city of China.
#E2 = weather[{"location": "#E1", "days": 7}]
Plan: Finally, use a language model to generate clothing recommendations based on the weekly weather.
#E3 = llm[{"input": "Using the 7-day forecast in #E2, provide clothing suggestions for visiting #E1 this week."}]'''

P_PROMPT_SUFFIX = '''Begin! Describe your plans with rich details. Each Plan should be followed by only one #E,
and the params_dict is the input of the tool, should be a valid json string wrapped in [],
(e.g. [{{'input': 'hello world', 'num_beams': 5}}]).\n\n'''

S_PROMPT_PREFIX = ('Solve the following task or problem. To assist you, we provide some plans and '
                   'corresponding evidences that might be helpful. Notice that some of these information '
                   'contain noise so you should trust them with caution.\n\n')

S_PROMPT_SUFFIX = ('\nNow begin to solve the task or problem. Respond with '
                   'the answer directly with no extra words.\n\n')

class ReWOOAgent(ModuleBase):
    """ReWOOAgent consists of three parts: Planer, Worker and Solver. The Planner uses predictive reasoning capabilities to create a solution blueprint for a complex task; the Worker interacts with the environment through tool calls and fills in actual evidence or observations into instructions; the Solver processes all plans and evidence to develop a solution to the original task or problem.

Args:
    llm (ModuleBase): The LLM to be used can be TrainableModule or OnlineChatModule. It is mutually exclusive with plan_llm and solve_llm. Either set llm(the planner and sovler share the same LLM), or set plan_llm and solve_llm,or only specify llm(to set the planner) and solve_llm. Other cases are considered invalid.
    tools (List[str]): A list of tool names for LLM to use.
    plan_llm (ModuleBase): The LLM to be used by the planner, which can be either TrainableModule or OnlineChatModule.
    solve_llm (ModuleBase): The LLM to be used by the solver, which can be either TrainableModule or OnlineChatModule.
    return_trace (bool): If True, return intermediate steps and tool calls.
    stream (bool): Whether to stream the planning and solving process.


Examples:
    >>> import lazyllm
    >>> import wikipedia
    >>> from lazyllm.tools import fc_register, ReWOOAgent
    >>> @fc_register("tool")
    >>> def WikipediaWorker(input: str):
    ...     '''
    ...     Worker that search for similar page contents from Wikipedia. Useful when you need to get holistic knowledge about people, places, companies, historical events, or other subjects. The response are long and might contain some irrelevant information. Input should be a search query.
    ...
    ...     Args:
    ...         input (str): search query.
    ...     '''
    ...     try:
    ...         evidence = wikipedia.page(input).content
    ...         evidence = evidence.split("\\n\\n")[0]
    ...     except wikipedia.PageError:
    ...         evidence = f"Could not find [{input}]. Similar: {wikipedia.search(input)}"
    ...     except wikipedia.DisambiguationError:
    ...         evidence = f"Could not find [{input}]. Similar: {wikipedia.search(input)}"
    ...     return evidence
    ...
    >>> @fc_register("tool")
    >>> def LLMWorker(input: str):
    ...     '''
    ...     A pretrained LLM like yourself. Useful when you need to act with general world knowledge and common sense. Prioritize it when you are confident in solving the problem yourself. Input can be any instruction.
    ...
    ...     Args:
    ...         input (str): instruction
    ...     '''
    ...     llm = lazyllm.OnlineChatModule(source="glm")
    ...     query = f"Respond in short directly with no extra words.\\n\\n{input}"
    ...     response = llm(query, llm_chat_history=[])
    ...     return response
    ...
    >>> tools = ["WikipediaWorker", "LLMWorker"]
    >>> llm = lazyllm.TrainableModule("GLM-4-9B-Chat").deploy_method(lazyllm.deploy.vllm).start()  # or llm = lazyllm.OnlineChatModule(source="sensenova")
    >>> agent = ReWOOAgent(llm, tools)
    >>> query = "What is the name of the cognac house that makes the main ingredient in The Hennchata?"
    >>> res = agent(query)
    >>> print(res)
    '
    Hennessy '
    """
    def __init__(self, llm: Union[ModuleBase, None] = None, tools: List[Union[str, Callable]] = [], *,  # noqa B006
                 plan_llm: Union[ModuleBase, None] = None, solve_llm: Union[ModuleBase, None] = None,
                 return_trace: bool = False, stream: bool = False, return_last_tool_calls: bool = False):
        super().__init__(return_trace=return_trace)
        self._return_last_tool_calls = return_last_tool_calls
        assert (llm is None and plan_llm and solve_llm) or (llm and plan_llm is None), 'Either specify only llm \
               without specify plan and solve, or specify only plan and solve without specifying llm, or specify \
               both llm and solve. Other situations are not allowed.'
        assert tools, 'tools cannot be empty.'
        self._planner = (plan_llm or llm).share(stream=dict(
            prefix='\nI will give a plan first:\n', prefix_color=Color.blue, color=Color.green) if stream else False)
        self._solver = (solve_llm or llm).share(stream=dict(
            prefix='\nI will solve the problem:\n', prefix_color=Color.blue, color=Color.green) if stream else False)
        self._tools_manager = ToolManager(tools, return_trace=return_trace)
        with pipeline() as self._agent:
            self._agent.planner_pre_action = self._build_planner_prompt
            self._agent.planner = self._planner
            self._agent.worker_evidences = self._get_worker_evidences
            self._agent.solver_pre_action = self._build_solver_prompt | bind(input=self._agent.input)
            self._agent.solver = ifs(self._return_last_tool_calls, lambda x: 'ok', self._solver)

    def _build_planner_prompt(self, input: str):
        prompt = P_PROMPT_PREFIX + 'Tools can be one of the following:\n'
        for name, tool in self._tools_manager.tools_info.items():
            prompt += f'{name}[params_dict]: {tool.description}\n'
        prompt += P_FEWSHOT + '\n' + P_PROMPT_SUFFIX + input + '\n'
        locals['chat_history'][self._planner._module_id] = []
        return prompt

    def _parse_and_call_tool(self, tool_call: str, evidence: Dict[str, str]):
        tool_name, tool_arguments = tool_call.split('[', 1)
        tool_arguments = tool_arguments.split(']')[0]
        for var in re.findall(r'#E\d+', tool_arguments):
            if var in evidence:
                tool_arguments = tool_arguments.replace(var, str(evidence[var]))
        tool_calls = [{'function': {'name': tool_name, 'arguments': tool_arguments}}]
        result = self._tools_manager(tool_calls)
        locals['_lazyllm_agent']['workspace']['tool_call_trace'].append(
            {**tool_calls[0], 'tool_call_result': result[0]}
        )
        return json.dumps(result[0]).strip('\"')

    def _get_worker_evidences(self, response: str):
        LOG.debug(f'planner plans: {response}')
        evidence = {}
        worker_evidences = ''
        for line in response.splitlines():
            if line.startswith('Plan'):
                worker_evidences += line + '\n'
            elif re.match(r'#E\d+\s*=', line.strip()):
                e, tool_call = line.split('=', 1)
                evidence[e.strip()] = self._parse_and_call_tool(tool_call.strip(), evidence)
                worker_evidences += f'Evidence:\n{evidence[e.strip()]}\n'

        LOG.debug(f'worker_evidences: {worker_evidences}')
        return worker_evidences

    def _build_solver_prompt(self, worker_evidences, input):
        prompt = S_PROMPT_PREFIX + input + '\n' + worker_evidences + S_PROMPT_SUFFIX + input + '\n'
        locals['chat_history'][self._solver._module_id] = []
        return prompt

    def forward(self, query: str):
        locals['_lazyllm_agent']['workspace'] = {'tool_call_trace': []}
        result = self._agent(query)
        if self._return_last_tool_calls and locals['_lazyllm_agent']['workspace']['tool_call_trace']:
            return locals['_lazyllm_agent'].pop('workspace').pop('tool_call_trace')
        return result
