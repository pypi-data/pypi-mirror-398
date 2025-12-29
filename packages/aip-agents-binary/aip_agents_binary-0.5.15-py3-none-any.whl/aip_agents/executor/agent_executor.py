"""AgentExecutor and GLLMMultiActionAgent for AIP Agents.

This module provides a custom implementation of LangChain's AgentExecutor
and a GLLMMultiActionAgent that bridges between the GLLM Agent implementation
and LangChain's BaseMultiActionAgent interface.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from gllm_core.constants import EventLevel, EventType
from gllm_core.event import EventEmitter
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker
from gllm_inference.schema import (
    LMOutput,
    MessageRole,
    ToolCall,
    ToolResult,
)
from langchain.agents import (
    AgentExecutor as LangchainAgentExecutor,
)  # Alias for clarity
from langchain.agents import BaseMultiActionAgent
from langchain.agents.tools import InvalidTool
from langchain_core.agents import AgentAction, AgentFinish, AgentStep
from langchain_core.callbacks import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
    Callbacks,
)
from langchain_core.tools import BaseTool
from pydantic import ConfigDict

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutorConfig:
    """Configuration for AgentExecutor."""

    instruction: str
    invoker: BaseLMInvoker
    tools: Sequence[BaseTool]
    max_iterations: int | None = 15
    max_execution_time: float | None = None
    verbose: bool = False
    event_emitter: EventEmitter | None = None
    handle_parsing_errors: bool = True
    prompt_memory: list | None = None


class GLLMMultiActionAgent(BaseMultiActionAgent):
    """Bridges a GLLM Agent with LangChain's BaseMultiActionAgent interface.

    This class allows a GLLM Agent (which uses an LMInvoker internally) to be
    used within LangChain's execution framework (e.g., with an AgentExecutor).
    It handles the conversion of prompts and responses between the GLLM Agent's
    LMInvoker system and the format expected by LangChain.

    Primarily designed for asynchronous operation via the `aplan` method.

    Attributes:
        instruction (str): The system instruction for the language model.
        invoker (BaseLMInvoker): The LMInvoker instance associated with the GLLM Agent,
            used for making calls to the language model.
        tools (list[BaseTool]): A list of tools available to the GLLM Agent.
        event_emitter (Optional[EventEmitter]): An optional event emitter for streaming
            intermediate steps and other events. Defaults to None.
        input_keys_arg (list[str]): The list of input keys that the agent expects.
            Defaults to ["input"].
        return_keys_arg (list[str]): The list of keys for the agent's return values.
            Defaults to ["output"].
        prompt_memory (list[tuple[MessageRole, list[Any]]]): Pre-formatted prompt memory.
    """

    instruction: str
    invoker: BaseLMInvoker
    tools: list[BaseTool]
    event_emitter: EventEmitter | None = None
    input_keys_arg: list[str] = ["input"]
    return_keys_arg: list[str] = ["output"]
    prompt_memory: list | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        instruction: str,
        invoker: BaseLMInvoker,
        tools: list[BaseTool],
        event_emitter: EventEmitter | None = None,
        prompt_memory: list | None = None,
    ):
        """Initializes the GLLMMultiActionAgent.

        Args:
            instruction (str): The system instruction for the language model.
            invoker (BaseLMInvoker): The LMInvoker from the GLLM Agent.
            tools (list[BaseTool]): Tools available to the GLLM Agent.
            event_emitter (Optional[EventEmitter], optional): Event emitter for streaming.
                Defaults to None.
            prompt_memory (Optional[list], optional):
                Pre-formatted prompt memory. Defaults to None.
        """
        super().__init__(
            instruction=instruction,
            invoker=invoker,
            tools=tools,
            event_emitter=event_emitter,
            prompt_memory=prompt_memory,
        )

    @property
    def input_keys(self) -> list[str]:
        """Input keys for the agent."""
        return self.input_keys_arg

    @property
    def return_values(self) -> list[str]:
        """Return values of the agent."""
        return self.return_keys_arg

    def plan(
        self,
        intermediate_steps: list[tuple[AgentAction, str]],
        _callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> list[AgentAction] | AgentFinish:
        """Synchronous planning. (Not Implemented).

        This method is intentionally not implemented to encourage asynchronous
        operations. Please use the `aplan` method.

        Args:
            intermediate_steps: Steps the LLM has taken to date, along with observations.
            _callbacks: Callbacks to run.
            **kwargs: User inputs.

        Raises:
            NotImplementedError: This method is not implemented.
        """
        logger.warning(
            "GLLMMultiActionAgent synchronous 'plan' method was called but is not implemented. Use 'aplan' instead."
        )
        raise NotImplementedError("Synchronous planning is not implemented. Please use the 'aplan' method.")

    async def aplan(
        self,
        intermediate_steps: list[tuple[AgentAction, str]],
        _callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> list[AgentAction] | AgentFinish:
        """Asynchronously decides the next action(s) or finishes execution.

        Args:
            intermediate_steps (list[tuple[AgentAction, str]]): A list of previous
                agent actions and their corresponding string observations.
            _callbacks (Callbacks, optional): LangChain callbacks. Not directly used by
                this method but maintained for interface compatibility. Defaults to None.
            **kwargs (Any): Additional keyword arguments representing the initial inputs
                to the agent (e.g., `input="user's query"`).

        Returns:
            list[AgentAction] | AgentFinish: A list of `AgentAction` objects if the
                agent decides to take one or more actions, or an `AgentFinish` object
                if the agent has completed its work.
        """
        prompt_messages: list = self._create_prompt(intermediate_steps, **kwargs)

        logger.debug(f"Prompt messages for GLLMMultiActionAgent aplan: {prompt_messages}")
        response = await self.invoker.invoke(prompt=prompt_messages, event_emitter=self.event_emitter)

        parsed_response = await self._parse_response(response)
        return parsed_response

    def get_allowed_tools(self) -> list[str] | None:
        """Returns a list of tool names that this agent is allowed to use."""
        return [tool.name for tool in self.tools]

    def return_stopped_response(
        self,
        early_stopping_method: str,
        _intermediate_steps: list[tuple[AgentAction, str]],
        **kwargs: Any,
    ) -> AgentFinish:
        """Returns an AgentFinish object when the agent is stopped early.

        Args:
            early_stopping_method (str): The method used for early stopping.
                Currently, only "force" is supported.
            _intermediate_steps (list[tuple[AgentAction, str]]): The history of
                actions and observations.
            **kwargs (Any): Additional inputs.

        Returns:
            AgentFinish: An AgentFinish object indicating the agent stopped.

        Raises:
            ValueError: If `early_stopping_method` is not "force".
        """
        if early_stopping_method == "force":
            return AgentFinish(
                return_values={"output": "Agent stopped due to iteration limit or time limit."},
                log="Agent stopped due to iteration limit or time limit.\n",
            )
        raise ValueError(f"Got unsupported early_stopping_method `{early_stopping_method}`")

    def tool_run_logging_kwargs(self) -> dict[str, Any]:
        """Returns keyword arguments for logging tool runs. Currently empty."""
        return {}

    def _create_prompt(self, intermediate_steps: list[tuple[AgentAction, str]], **kwargs: Any) -> list:
        """Create a multimodal prompt from intermediate steps and inputs.

        Args:
            intermediate_steps: Steps the LLM has taken to date, along with observations.
            **kwargs: User inputs.

        Returns:
            A list (list of prompt message tuples).
        """
        prompt_msgs: list = []

        # 1. System instruction
        prompt_msgs.append((MessageRole.SYSTEM, [self.instruction]))

        # 2. Prepend chat history
        if self.prompt_memory:
            prompt_msgs.extend(self.prompt_memory)

        # 3. Current user input
        if "input" in kwargs:
            prompt_msgs.append((MessageRole.USER, [kwargs["input"]]))

        # 4. Intermediate steps (tool calls and observations for the current turn)
        for i, (action, observation) in enumerate(intermediate_steps):
            tool_call_id = f"call_{action.tool}_{i}"
            if isinstance(action.tool_input, dict):
                args = action.tool_input
            else:
                args = {"query": action.tool_input}
            tool_call = ToolCall(id=tool_call_id, name=action.tool, args=args)
            prompt_msgs.append((MessageRole.ASSISTANT, [tool_call]))
            tool_result = ToolResult(id=tool_call_id, output=observation)
            prompt_msgs.append((MessageRole.USER, [tool_result]))

        return prompt_msgs

    async def _handle_tool_calls(self, tool_calls: list[ToolCall]) -> list[AgentAction] | None:
        """Handles tool calls by converting them to AgentActions.

        Args:
            tool_calls: list of tool calls to process.

        Returns:
            Optional[list[AgentAction]]: List of agent actions if any tool calls exist.
        """
        if not tool_calls:
            return None

        actions = []
        for tool_call in tool_calls:
            tool_input = tool_call.args if tool_call.args else {}
            action_log = f"Invoking: `{tool_call.name}` with `{tool_input}`\n"
            actions.append(
                AgentAction(
                    tool=tool_call.name,
                    tool_input=tool_input,
                    log=f"\n{action_log}\n",
                )
            )
            if self.event_emitter:
                await self.event_emitter.emit(
                    event_type=EventType.DATA,
                    event_level=EventLevel.INFO,
                    value=action_log,
                )
        return actions

    async def _parse_response(self, response: LMOutput) -> list[AgentAction] | AgentFinish:
        """Parses the LMInvoker's response into LangChain actions or finish signal.

        If the response contains tool calls, they are converted to `AgentAction` objects.
        Otherwise, the response is treated as a final answer and converted to an
        `AgentFinish` object.

        Args:
            response (LMOutput): The output from the LMInvoker.

        Returns:
            list[AgentAction] | AgentFinish: LangChain actions or finish signal.
        """
        logger.debug(f"Response from LM Invoker in GLLMMultiActionAgent: {response}")

        if not isinstance(response, LMOutput):
            return AgentFinish(return_values={"output": response}, log=response)

        actions = await self._handle_tool_calls(response.tool_calls)
        if actions:
            return actions

        return AgentFinish(
            return_values={"output": str(response.response)},
            log=str(response.response),
        )


class AgentExecutor(LangchainAgentExecutor):
    """Custom GLLM AgentExecutor extending LangChain's AgentExecutor.

    This executor orchestrates the execution loop for a GLLM Agent. It receives
    the GLLM Agent instance and necessary components (invoker, tools) and internally
    creates the `GLLMMultiActionAgent` adapter needed for the LangChain execution flow.

    It prioritizes asynchronous operations (`_aperform_agent_action`) and integrates
    with the GLLM event emitter system.
    """

    def __init__(
        self,
        config: ExecutorConfig,
        **kwargs: Any,
    ):
        """Initializes the custom AgentExecutor.

        Args:
            config: Configuration object containing all executor parameters.
            **kwargs: Additional keyword arguments passed to the parent
                `LangchainAgentExecutor` constructor.
        """
        action_agent = GLLMMultiActionAgent(
            instruction=config.instruction,
            invoker=config.invoker,
            tools=list(config.tools),
            event_emitter=config.event_emitter,
            prompt_memory=config.prompt_memory,
        )

        super().__init__(
            agent=action_agent,
            tools=config.tools,
            max_iterations=config.max_iterations,
            max_execution_time=config.max_execution_time,
            verbose=config.verbose,
            handle_parsing_errors=config.handle_parsing_errors,
            **kwargs,
        )
        self._event_emitter = config.event_emitter

    @property
    def event_emitter(self) -> EventEmitter | None:
        """Get the event emitter."""
        return self._event_emitter

    async def _aperform_agent_action(
        self,
        name_to_tool_map: dict[str, BaseTool],
        color_mapping: dict[str, str],
        agent_action: AgentAction,
        run_manager: AsyncCallbackManagerForChainRun | None = None,
    ) -> AgentStep:
        """Asynchronously performs a single agent action (tool execution).

        This method executes the specified tool with the given input and logs
        the action and observation. If an `event_emitter` is configured, it emits
        events for tool responses and invalid tool requests.

        Args:
            name_to_tool_map (dict[str, BaseTool]): Mapping of tool names to tool instances.
            color_mapping (dict[str, str]): Mapping of tool names to colors for logging.
            agent_action (AgentAction): The agent action to perform, specifying the tool
                and tool input.
            run_manager (Optional[AsyncCallbackManagerForChainRun], optional): LangChain
                callback manager for the current run. Defaults to None.

        Returns:
            AgentStep: An `AgentStep` object containing the performed action and the
                resulting observation from the tool.
        """
        if run_manager:
            await run_manager.on_agent_action(agent_action, verbose=self.verbose, color="green")

        observation = ""
        tool_to_run: BaseTool | None = name_to_tool_map.get(agent_action.tool)

        if tool_to_run:
            tool_run_kwargs = self._action_agent.tool_run_logging_kwargs()
            if tool_to_run.return_direct:
                tool_run_kwargs["llm_prefix"] = ""

            tool_input = await self._preprocess_tool_input(agent_action.tool_input)
            observation = await tool_to_run.arun(
                tool_input,
                verbose=self.verbose,
                color=color_mapping.get(agent_action.tool),
                callbacks=run_manager.get_child() if run_manager else None,
                **tool_run_kwargs,
            )
            observation = await self._postprocess_tool_output(observation)
            logger.info(f"Tool {agent_action.tool} responded: {observation}")
        else:
            tool_run_kwargs = self._action_agent.tool_run_logging_kwargs()
            observation = await InvalidTool().arun(
                tool_input={
                    "requested_tool_name": agent_action.tool,
                    "available_tool_names": list(name_to_tool_map.keys()),
                },
                verbose=self.verbose,
                color=None,
                callbacks=run_manager.get_child() if run_manager else None,
                **tool_run_kwargs,
            )
            logger.warning(f"Invalid tool requested: {agent_action.tool}. Observation: {observation}")
        return AgentStep(action=agent_action, observation=observation)

    async def _preprocess_tool_input(self, tool_input: Any) -> Any:
        """Preprocess the tool input.

        Args:
            tool_input (Any): The tool input to preprocess.

        Returns:
            Any: The preprocessed tool input.
        """
        return tool_input

    async def _postprocess_tool_output(self, tool_output: Any) -> Any:
        """Postprocess the tool output.

        Args:
            tool_output (Any): The tool output to postprocess.

        Returns:
            Any: The postprocessed tool output.
        """
        return tool_output

    def _perform_agent_action(
        self,
        name_to_tool_map: dict[str, BaseTool],
        color_mapping: dict[str, str],
        agent_action: AgentAction,
        run_manager: CallbackManagerForChainRun | None = None,
    ) -> AgentStep:
        """Synchronous agent action. (Not Implemented).

        This method is intentionally not implemented to encourage asynchronous
        operations. Please use the `_aperform_agent_action` method.

        Args:
            name_to_tool_map (dict[str, BaseTool]): Mapping of tool names to tools.
            color_mapping (dict[str, str]): Mapping of tool names to colors.
            agent_action (AgentAction): The action to execute.
            run_manager (Optional[CallbackManagerForChainRun], optional): Callback manager.
                Defaults to None.

        Raises:
            NotImplementedError: This method is not implemented.
        """
        logger.warning(
            "AgentExecutor synchronous '_perform_agent_action' was called but is not implemented. "
            "Use '_aperform_agent_action' instead."
        )
        raise NotImplementedError(
            "Synchronous agent action execution is not implemented. Please use the '_aperform_agent_action' method."
        )
