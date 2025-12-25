"""
Tool doctor: Analyze tools and give recommendations for improvement.
"""

from aixtools.agents import get_agent, run_agent
from aixtools.tools.doctor.tool_recommendation import ToolRecommendation

TOOL_DOCTOR_PROMPT = """
## Tool doctor
You are helping to debug common errors in tools and tool definitions.

Given the tools, for each tool you will give feedback about the tool
definition.

1. Name: Check if the tool name is descriptive and follows naming conventions.
2. Description: Ensure the tool's description is clear and provides enough
   detail
   so that users understand its purpose and functionality.
3. Return type: Check if the return type is specified and matches the tool's
   functionality.
4. Arguments: Verify that the tool arguments are well-defined and include types
   and descriptions. Ensure that argument names are descriptive and follow
   naming conventions.
5. Look for any missing or redundant information in the tool definition.

Some rules:
- Ignore a tool called 'final_result'.
- Do not suggest change if the tool is already well-defined.
- Don't be nitpicking, focus on significant improvements that can be made to
  the tool definition.
- Don't suggest trivial improvements or changes for things that are
  self-evident or already well-defined.
"""


async def tool_doctor_single(tool) -> ToolRecommendation:
    """Run the tool doctor agent to analyze a single tool"""
    agent = get_agent(tools=[tool], output_type=ToolRecommendation)
    ret = await run_agent(agent, TOOL_DOCTOR_PROMPT, log_model_requests=True, verbose=True, debug=True)
    return ret[0]  # type: ignore


async def tool_doctor_multiple(tools: list) -> list[ToolRecommendation]:
    """Run the tool doctor agent to analyze the tools"""
    agent = get_agent(tools=tools, output_type=list[ToolRecommendation])
    ret = await run_agent(agent, TOOL_DOCTOR_PROMPT)
    return ret[0]  # type: ignore


async def tool_doctor(tools: list, max_tools_per_batch=5, verbose=True) -> list[ToolRecommendation]:
    """Run the tool doctor agent to analyze tools and give recommendations."""
    # Split tools into batches if they exceed the max_tools_per_batch limit
    results = []
    for i in range(0, len(tools), max_tools_per_batch):
        batch = tools[i : i + max_tools_per_batch]
        batch_num = i // max_tools_per_batch + 1
        tool_names = [t.__name__ for t in batch]
        print(f"Processing batch {batch_num} with {len(batch)} tools: {tool_names}")
        ret = await tool_doctor_multiple(batch)
        results.extend(ret)
    # Print results if verbose
    if verbose:
        for r in results:
            print(r)
    return results
