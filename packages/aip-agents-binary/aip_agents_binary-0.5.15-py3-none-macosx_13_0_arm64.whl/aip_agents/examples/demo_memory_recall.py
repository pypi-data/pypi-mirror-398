"""Demo memory recall scenarios for demo@glair user data.

This script tests the exact scenarios mentioned by the user:
1. Recall memory by query semantically (without time period)
2. Recall memory by query semantically AND with time period
3. Recall memory by date (without query semantic)
4. Recall memory from last week (calendar week period)
5. General knowledge questions (to verify responses are not inappropriately grounded in personal memory)

These tests are designed to work with the demo@glair user data
from September 17-24, 2025.

Note: Uses a single reused LangGraphAgent instance across all scenarios
to avoid reinitialization. Model set to openai/gpt-4.1.
The base LangGraphAgent automatically registers the memory search tool
and adds memory recall guidance to the system instruction when memory_backend="mem0".

Evaluation: instead of keyword checks, we use a dedicated
"Judge LLM" (memoryless) to classify the agent's answer as grounded in
fetched memory vs likely hallucination.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from aip_agents.agent import LangGraphAgent

load_dotenv()


class MemoryTestResult:
    """Container for test scenario results."""

    JUDGE_SUCCESS_THRESHOLD = 0.7
    MEMORY_DISPLAY_LIMIT = 300

    def __init__(
        self, scenario_name: str, query: str, response: str = None, memory_fetched: str = None, error: str = None
    ) -> None:
        """Initialize a memory test result.

        Args:
            scenario_name: Name of the test scenario.
            query: The input query for the scenario.
            response: The agent's response (optional).
            memory_fetched: The raw memory retrieved from the tool (optional).
            error: Any error message (optional).
        """
        self.scenario_name = scenario_name
        self.query = query
        self.response = response
        self.memory_fetched = memory_fetched
        self.error = error
        self.success = error is None
        # Judge outputs
        self.judge_verdict = None  # "grounded" | "hallucination" | "general_knowledge"
        self.judge_score = None  # float 0..1

    def set_success_from_judge(self, verdict: str, score: float | None):
        """Set success using judge verdict and confidence score.

        Success criteria: (verdict == "grounded" or verdict == "general_knowledge") and
        score >= JUDGE_SUCCESS_THRESHOLD.

        Args:
            verdict (str): The judge's verdict ("grounded", "hallucination", or "general_knowledge").
            score (float | None): The confidence score (0.0 to 1.0).
        """
        if self.error or not self.response or verdict is None:
            self.success = False
            return
        try:
            self.success = (verdict.lower() in ["grounded", "general_knowledge"]) and (
                score is not None and float(score) >= self.JUDGE_SUCCESS_THRESHOLD
            )
        except Exception:
            self.success = False


def _print_memory_summary(memory_fetched: str):
    """Print memory with truncation.

    Args:
        memory_fetched (str): The memory content to print.
    """
    limit = MemoryTestResult.MEMORY_DISPLAY_LIMIT
    truncated_memory = memory_fetched[:limit]
    suffix = "..." if len(memory_fetched) > limit else ""
    print(f"Memory: {truncated_memory}{suffix}")


def _print_success_result(result: MemoryTestResult):
    """Print successful result details.

    Args:
        result (MemoryTestResult): The test result to print.
    """
    print("✅ Status: SUCCESS")
    print(f"Output: {result.response}")
    if result.memory_fetched:
        _print_memory_summary(result.memory_fetched)
    if result.judge_verdict is not None:
        print(f"Judge: verdict={result.judge_verdict}, score={result.judge_score}")


def _print_failure_result(result: MemoryTestResult):
    """Print failure result details.

    Args:
        result (MemoryTestResult): The test result to print.
    """
    print("❌ Status: FAILED")
    if result.error:
        print(f"Error:  {result.error}")
    else:
        print("Judge flagged as not grounded or low confidence")
        if result.memory_fetched:
            _print_memory_summary(result.memory_fetched)
        if result.judge_verdict is not None:
            print(f"Judge: verdict={result.judge_verdict}, score={result.judge_score}")
        print(f"Output: {result.response}")


def _print_header(start_time: datetime, end_time: datetime):
    """Print test header information.

    Args:
        start_time (datetime): The start time of the tests.
        end_time (datetime): The end time of the tests.
    """
    duration = end_time - start_time
    print("\n" + "=" * 80)
    print("🧠 MEMORY RECALL TEST SUMMARY")
    print("=" * 80)
    print("Tested User ID: demo@glair")
    print("Expected Data Range: September 17-24, 2025")
    print(f"Test Duration: {duration.total_seconds():.2f} seconds")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


def _print_statistics(results: list[MemoryTestResult]):
    """Print test statistics.

    Args:
        results (list[MemoryTestResult]): List of test results to analyze.
    """
    print("\n" + "=" * 80)
    print("📊 TEST STATISTICS")
    print("=" * 80)
    successful = sum(1 for r in results if r.success)
    total = len(results)
    print(f"Total Scenarios: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success Rate: {(successful / total) * 100:.1f}%")

    if successful == total:
        print("\n🎉 All memory recall scenarios completed successfully!")
    else:
        print(f"\n⚠️  {total - successful} scenario(s) failed. Check details above.")
    print("=" * 80)


def print_test_summary(results: list[MemoryTestResult], start_time: datetime):
    """Print a clean summary of all test results.

    Args:
        results (list[MemoryTestResult]): List of test results to summarize.
        start_time (datetime): The start time of the tests.
    """
    end_time = datetime.now()
    _print_header(start_time, end_time)

    for i, result in enumerate(results, 1):
        print(f"\n📋 SCENARIO {i}: {result.scenario_name}")
        print("-" * 60)
        print(f"Input:  {result.query}")

        if result.success:
            _print_success_result(result)
        else:
            _print_failure_result(result)

    _print_statistics(results)


async def evaluate_with_judge(
    judge_agent: LangGraphAgent, query: str, response: str, memory_fetched: str = None
) -> tuple[str | None, float | None]:
    """Evaluate if the response is grounded in memory using the judge agent.

    Args:
        judge_agent (LangGraphAgent): The judge agent to use for evaluation.
        query (str): The original user query.
        response (str): The agent's response to evaluate.
        memory_fetched (str, optional): The memory that was retrieved. Defaults to None.

    Returns:
        tuple[str | None, float | None]: Tuple of (verdict, score) where verdict is "grounded", "hallucination", or "general_knowledge", and score is a confidence score (0.0-1.0).
    """
    memory_section = ""
    if memory_fetched:
        memory_section = f"\n\nActual Memory Retrieved from Tool:\n{memory_fetched}\n"

    judge_prompt = (
        "Evaluate the following assistant answer for whether it is grounded in the fetched personal memory, "
        "is general knowledge, or is hallucination.\n\n"
        f"User Query:\n{query}\n\n"
        f"Assistant Answer:\n{response}{memory_section}\n"
        "Your task is to determine if the assistant's answer is directly supported by the retrieved memory data, "
        "is accurate general knowledge, or is incorrect/hallucinated. "
        "Consider: Does the answer contain specific details that match the memory? "
        "Are the facts, dates, names consistent with what was actually retrieved? "
        "If no memory was retrieved and the query is general knowledge, classify as 'general_knowledge' "
        "if the answer is correct.\n\n"
        'Respond ONLY with JSON: {"verdict": "grounded|hallucination|general_knowledge", "score": <0..1>}'
    )
    judge_raw = await judge_agent.arun(judge_prompt)
    judge_text = judge_raw.get("output") if isinstance(judge_raw, dict) else str(judge_raw)
    verdict = None
    score = None
    try:
        judge_obj = json.loads(judge_text)
        verdict = judge_obj.get("verdict")
        score = judge_obj.get("score")
    except Exception:
        # Fallback: attempt to parse simple keywords if JSON parse fails
        lower = judge_text.lower()
        if "general_knowledge" in lower:
            verdict = "general_knowledge"
        elif "grounded" in lower and "hallucination" not in lower:
            verdict = "grounded"
        else:
            verdict = "hallucination"
        score = 0.5

    return verdict, score


def _check_environment_variables() -> bool:
    """Check required environment variables."""
    if not os.getenv("MEM0_API_KEY"):
        print("❌ Error: MEM0_API_KEY not found in environment variables.")
        print("Please set MEM0_API_KEY in your .env file or environment.")
        return False

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set OPENAI_API_KEY in your .env file or environment.")
        return False

    return True


def _create_agents() -> tuple[LangGraphAgent, LangGraphAgent]:
    """Create memory recall and judge agents."""
    # Create memory recall agent - simplified instruction since built-in functionality handles complexity
    agent = LangGraphAgent(
        name="LangGraphMemoryEnhancerAgent",
        instruction="You are a helpful assistant that try your best to answer the user's query.",
        memory_backend="mem0",
        agent_id="demo-user-test",
        model="openai/gpt-4.1",
        save_interaction_to_memory=False,
    )

    # Create judge agent with NO memory backend
    judge_agent = LangGraphAgent(
        name="Judge",
        instruction=(
            "You are an impartial evaluator (no tools, no memory). Given a user's query and an assistant's answer, "
            "decide if the answer is grounded in fetched personal memory, is general knowledge, or is hallucination. "
            "Output STRICT JSON with keys: verdict ('grounded'|'hallucination'|'general_knowledge'), "
            "score (0..1), reason (short string). "
            "- 'grounded' means the answer most likely came from specific recalled personal memory items. "
            "- 'general_knowledge' means the answer is accurate general knowledge that doesn't require "
            "personal memory. "
            "- 'hallucination' means the answer is incorrect, guesses, or contradicts known facts. "
            "Consider concreteness, specificity (dates, names), and whether the query requires personal memory "
            "to answer."
        ),
        memory_backend=None,
        agent_id="judge-evaluator",
        model="openai/gpt-4.1",
        save_interaction_to_memory=False,
    )

    return agent, judge_agent


async def _run_single_scenario(
    agent: LangGraphAgent,
    judge_agent: LangGraphAgent,
    scenario_name: str,
    query: str,
    output_file: str,
) -> MemoryTestResult:
    """Run a single memory recall scenario.

    Args:
        agent (LangGraphAgent): The agent to run the scenario with.
        judge_agent (LangGraphAgent): The judge agent to evaluate the response.
        scenario_name (str): Name of the test scenario.
        query (str): The query to run.
        output_file (str): Path to the output file for logging.

    Returns:
        MemoryTestResult: The test result containing response, memory, and evaluation.
    """
    print(f"\n🔄 Running scenario: {scenario_name}")
    print(f"Query: {query}")

    memory_fetched = ""
    final_response = ""

    # Write stream_start header for this scenario
    try:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"--- Scenario: {scenario_name} | Query: {query} | Time: {datetime.now().isoformat()} ---\n")
            json.dump({"type": "stream_start", "query": query, "scenario": scenario_name}, f)
            f.write("\n")
    except Exception as e:
        print(f"  ⚠️ Could not write stream_start to {output_file}: {e}")

    # Stream the agent execution and capture memory tool results + final response
    final_response = await agent.arun(query=query, memory_user_id="demo@glair")
    final_response_output = final_response["output"]
    final_state = final_response["full_final_state"]
    memory_fetched: HumanMessage = final_state["messages"][1].content.strip()

    # Create test result with both memory and response
    test_result = MemoryTestResult(scenario_name, query, final_response_output, memory_fetched)

    # Evaluate with judge using both memory and response
    verdict, score = await evaluate_with_judge(judge_agent, query, final_response_output, memory_fetched.strip())
    test_result.judge_verdict = verdict
    test_result.judge_score = score
    test_result.set_success_from_judge(verdict, score)

    return test_result


async def run_all_scenarios():
    """Run all memory recall test scenarios with a single reused agent and show clean summary."""
    start_time = datetime.now()

    print("🧠 Starting Memory Recall Testing with demo@glair data...")
    print(f"Current time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("User ID: demo@glair")
    print("Expected data range: September 17-24, 2025")
    print("Running tests... (this may take a few moments)")

    # Check environment variables
    if not _check_environment_variables():
        return

    # Create agents
    agent, judge_agent = _create_agents()

    scenarios = [
        ("Semantic Search Without Time Period", "What is my name and birthday? How old am I now?"),
        ("Semantic Search With Time Period", "I mention my hobby on September 17, 2025, can you recall it?"),
        ("Date-Based Recall Without Semantic Query", "What did we talk about in 25 September 2025?"),
        ("Last Week Recall (Calendar Week)", "What did we discuss last week?"),
        ("General Knowledge - Capital of Indonesia", "What is the capital of Indonesia?"),
        ("General Knowledge - US President Inauguration", "Who was inaugurated as US president on January 20, 2009?"),
    ]

    results = []
    try:
        # Tool stream capture output file (JSONL)
        output_file = "memory_recall_tool_events.jsonl"

        for scenario_name, query in scenarios:
            try:
                result = await _run_single_scenario(agent, judge_agent, scenario_name, query, output_file)
                results.append(result)
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                test_result = MemoryTestResult(scenario_name, query, error=str(e))
                results.append(test_result)

        # Print clean summary
        print_test_summary(results, start_time)

    except Exception as e:
        print(f"❌ Error running scenarios: {e}")


if __name__ == "__main__":
    asyncio.run(run_all_scenarios())
