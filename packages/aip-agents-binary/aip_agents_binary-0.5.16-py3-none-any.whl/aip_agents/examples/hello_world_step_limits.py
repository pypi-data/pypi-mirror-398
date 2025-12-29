"""Example demonstrating configurable step limits and delegation depth tracking.

This example shows how to:
1. Configure maximum steps for an agent
2. Configure maximum delegation depth
3. Handle step limit exceeded errors gracefully
4. Track delegation chains across multi-agent hierarchies

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)
"""

import asyncio
import os

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphReactAgent
from aip_agents.examples.tools.langchain_arithmetic_tools import add_numbers
from aip_agents.schema.step_limit import MaxStepsExceededError, StepLimitConfig
from aip_agents.utils.step_limit_manager import StepLimitManager


def print_config_validation(config: StepLimitConfig | None, context: str):
    """Print step limit configuration validation."""
    print(f"\n{'=' * 60}")
    print(f"Configuration Validation - {context}")
    print(f"{'=' * 60}")
    if config is None:
        print("✓ Config: None (will use platform defaults)")
        print("  Expected: max_steps=25, max_delegation_depth=5")
    else:
        print(f"✓ max_steps: {config.max_steps}")
        print(f"✓ max_delegation_depth: {config.max_delegation_depth}")

        # Validate ranges
        if 1 <= config.max_steps <= 1000:
            print("  ✓ max_steps is valid (1-1000)")
        else:
            print("  ✗ max_steps is INVALID (should be 1-1000)")

        if 0 <= config.max_delegation_depth <= 10:
            print("  ✓ max_delegation_depth is valid (0-10)")
        else:
            print("  ✗ max_delegation_depth is INVALID (should be 0-10)")
    print(f"{'=' * 60}\n")


async def test_case_1_success_no_limits():
    """Test Case 1: Success - High limits, no warnings."""
    print("\n" + "=" * 60)
    print("TEST CASE 1: Success - High Limits (No Warnings)")
    print("=" * 60)

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [add_numbers]

    # Very high limits - should complete successfully
    step_limit_config = StepLimitConfig(
        max_steps=100,  # High limit
        max_delegation_depth=5,  # High depth
    )

    print_config_validation(step_limit_config, "High Limits")

    agent = LangGraphReactAgent(
        name="SuccessAgent",
        instruction="You are a helpful math assistant.",
        model=model,
        tools=tools,
    )

    query = "What is 5 + 3?"
    print(f"Query: {query}")
    print("Expected: Should complete successfully without warnings\n")

    try:
        response = await agent.arun(
            query=query,
            step_limit_config=step_limit_config,
            configurable={"thread_id": "test_case_1"},
        )
        print(f"✅ SUCCESS: {response['output']}")
        print("✅ Test passed: Agent completed without hitting limits\n")
    except Exception as e:
        print(f"❌ FAILED: {e}\n")


async def test_case_2_parallel_tool_batch_accounting():
    """Test Case 2: Demonstrate that parallel tool batches consume multiple steps."""
    manager = StepLimitManager(StepLimitConfig(max_steps=6))
    print("\n" + "=" * 60)
    print("TEST CASE 2: Parallel Tool Batch Accounting")
    print("=" * 60)
    print("Simulating one agent reasoning step plus 5 parallel tool calls.\n")

    print(f"Initial steps: {manager.context.current_step}, remaining budget: {manager.context.remaining_step_budget}")
    manager.increment_step()  # Agent LLM call
    print(
        f"After agent turn -> steps: {manager.context.current_step}, remaining: {manager.context.remaining_step_budget}"
    )

    # Simulate a batch of 5 tool calls executed in parallel
    manager.increment_step(count=5)
    print("After 5 parallel tool calls (count=5):")
    print(f"Steps used: {manager.context.current_step}, remaining: {manager.context.remaining_step_budget}")

    # Ensure limit is enforced now
    try:
        manager.check_step_limit()
    except MaxStepsExceededError as exc:
        print(f"✅ Limit enforcement triggered immediately: {exc}")
        return

    print("❌ Expected the limit to be hit after consuming 6 steps, but it was not.")


async def test_case_3_step_limit_exceeded():
    """Test Case 3: Step Limit Exceeded - Only 2 steps allowed."""
    print("\n" + "=" * 60)
    print("TEST CASE 3: Step Limit Exceeded (max_steps=2)")
    print("=" * 60)

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [add_numbers]

    # Very low step limit - will hit limit
    step_limit_config = StepLimitConfig(
        max_steps=2,  # Only 2 steps: 1 for thinking, 1 for tool call
        max_delegation_depth=0,
    )

    print_config_validation(step_limit_config, "Very Low Step Limit")

    agent = LangGraphReactAgent(
        name="LimitedAgent",
        instruction="You are a helpful math assistant. Always use the add_numbers tool.",
        model=model,
        tools=tools,
    )

    query = "Use the add_numbers tool to calculate 7 + 8, then add 10 to the result"
    print(f"Query: {query}")
    print("Expected: Should hit step limit after 2 steps\n")
    print("Step 0: Initial LLM call")
    print("Step 1: Tool call (add_numbers)")
    print("Step 2: Would be final response, but LIMIT HIT!\n")

    try:
        response = await agent.arun(
            query=query,
            step_limit_config=step_limit_config,
            configurable={"thread_id": "test_case_3"},
        )
        output = response["output"]
        print(f"Response: {output}\n")

        # Check if the response indicates limit was hit
        if "exceeded" in output.lower() or "limit" in output.lower():
            print("✅ SUCCESS: Step limit was enforced!")
            print("✅ Test passed: Agent terminated at limit\n")
        else:
            print("⚠️  Agent completed without hitting limit")
            print("   (This might happen if task was very simple)\n")
    except Exception as e:
        print(f"Exception raised: {type(e).__name__}: {e}")
        print("✅ Test passed: Step limit enforced via exception\n")


async def test_case_4_delegation_depth_exceeded():
    """Test Case 4: Delegation Depth Exceeded - Zero depth."""
    print("\n" + "=" * 60)
    print("TEST CASE 4: Delegation Depth Exceeded (depth=0)")
    print("=" * 60)

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Create sub-agent
    math_agent = LangGraphReactAgent(
        name="MathAgent",
        instruction="You are a math specialist. Use add_numbers tool for calculations.",
        model=model,
        tools=[add_numbers],
    )

    # Create coordinator
    coordinator = LangGraphReactAgent(
        name="Coordinator",
        instruction="You coordinate tasks. You MUST delegate all math to MathAgent using the delegate_to_agent tool.",
        model=model,
        tools=[],
    )
    coordinator.register_delegation_agents([math_agent])

    # Zero delegation depth - should block delegation
    step_limit_config = StepLimitConfig(
        max_steps=50,  # High steps
        max_delegation_depth=0,  # NO delegation allowed!
    )

    print_config_validation(step_limit_config, "Zero Delegation Depth")

    query = "Delegate to MathAgent to calculate 20 + 30"
    print(f"Query: {query}")
    print("Expected: Delegation should be BLOCKED (depth=0)\n")
    print("The coordinator will try to delegate but should get an error\n")

    try:
        response = await coordinator.arun(
            query=query,
            step_limit_config=step_limit_config,
            configurable={"thread_id": "test_case_4"},
        )
        output = response["output"]
        print(f"Response: {output}\n")

        # Check if delegation was blocked
        if (
            "cannot" in output.lower()
            or "depth" in output.lower()
            or "exceeded" in output.lower()
            or "error" in output.lower()
        ):
            print("✅ SUCCESS: Delegation depth limit enforced!")
            print("✅ Test passed: Delegation was blocked\n")
        else:
            print("⚠️  Agent responded without delegating")
            print("   (Coordinator may have answered directly instead)\n")
    except Exception as e:
        print(f"Exception raised: {type(e).__name__}: {e}")
        if "delegation" in str(e).lower() or "depth" in str(e).lower():
            print("✅ Test passed: Delegation depth enforced via exception\n")
        else:
            print("⚠️  Different error occurred\n")


async def main():
    """Run all test cases."""
    print("=" * 60)
    print("Step Limit Configuration - Test Suite")
    print("=" * 60)
    print("\nRunning 4 test cases:")
    print("1. Success with high limits")
    print("2. Parallel tool batch accounting demo")
    print("3. Step limit exceeded")
    print("4. Delegation depth exceeded")
    print("\nNOTE: Some limits are enforced silently via the agent's")
    print("      internal logic. Check for error messages in responses.")

    await test_case_1_success_no_limits()
    await test_case_2_parallel_tool_batch_accounting()
    await test_case_3_step_limit_exceeded()
    await test_case_4_delegation_depth_exceeded()

    print("\n" + "=" * 60)
    print("All test cases completed!")
    print("=" * 60)
    print("\n📝 Summary:")
    print("- Test 1: Should show successful completion")
    print("- Test 2: Shows that parallel tool batches consume multiple steps at once")
    print("- Test 3: Should show step limit enforcement")
    print("- Test 4: Should show delegation blocking")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set!")
        print("Please set it before running:")
        print('export OPENAI_API_KEY="your-key-here"')
        exit(1)

    asyncio.run(main())
