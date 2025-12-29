from _typeshed import Incomplete
from aip_agents.agent import LangGraphAgent as LangGraphAgent
from datetime import datetime

class MemoryTestResult:
    """Container for test scenario results."""
    JUDGE_SUCCESS_THRESHOLD: float
    MEMORY_DISPLAY_LIMIT: int
    scenario_name: Incomplete
    query: Incomplete
    response: Incomplete
    memory_fetched: Incomplete
    error: Incomplete
    success: Incomplete
    judge_verdict: Incomplete
    judge_score: Incomplete
    def __init__(self, scenario_name: str, query: str, response: str = None, memory_fetched: str = None, error: str = None) -> None:
        """Initialize a memory test result.

        Args:
            scenario_name: Name of the test scenario.
            query: The input query for the scenario.
            response: The agent's response (optional).
            memory_fetched: The raw memory retrieved from the tool (optional).
            error: Any error message (optional).
        """
    def set_success_from_judge(self, verdict: str, score: float | None):
        '''Set success using judge verdict and confidence score.

        Success criteria: (verdict == "grounded" or verdict == "general_knowledge") and
        score >= JUDGE_SUCCESS_THRESHOLD.

        Args:
            verdict (str): The judge\'s verdict ("grounded", "hallucination", or "general_knowledge").
            score (float | None): The confidence score (0.0 to 1.0).
        '''

def print_test_summary(results: list[MemoryTestResult], start_time: datetime):
    """Print a clean summary of all test results.

    Args:
        results (list[MemoryTestResult]): List of test results to summarize.
        start_time (datetime): The start time of the tests.
    """
async def evaluate_with_judge(judge_agent: LangGraphAgent, query: str, response: str, memory_fetched: str = None) -> tuple[str | None, float | None]:
    '''Evaluate if the response is grounded in memory using the judge agent.

    Args:
        judge_agent (LangGraphAgent): The judge agent to use for evaluation.
        query (str): The original user query.
        response (str): The agent\'s response to evaluate.
        memory_fetched (str, optional): The memory that was retrieved. Defaults to None.

    Returns:
        tuple[str | None, float | None]: Tuple of (verdict, score) where verdict is "grounded", "hallucination", or "general_knowledge", and score is a confidence score (0.0-1.0).
    '''
async def run_all_scenarios() -> None:
    """Run all memory recall test scenarios with a single reused agent and show clean summary."""
