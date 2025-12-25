"""
Batch processing functionality for running multiple agent queries in parallel.
"""

import asyncio
from typing import Any

from pydantic import BaseModel, ConfigDict

from aixtools.agents.agent import get_agent, run_agent


class AgentQueryParams(BaseModel):
    """Parameters for configuring agent queries in batch processing."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = ""  # Unique identifier for the query
    prompt: str | list[str]
    agent: Any = None
    model: Any = None
    debug: bool = False
    output_type: Any = str
    tools: list | None = []

    async def run(self):
        """Query the LLM"""
        agent = self.agent
        if agent is None:
            agent = get_agent(
                system_prompt=self.prompt, model=self.model, tools=self.tools, output_type=self.output_type
            )
        return await run_agent(agent=agent, prompt=self.prompt, debug=self.debug)


async def run_agent_batch(query_parameters: list[AgentQueryParams], batch_size=10):
    """
    Run multiple queries simultanously in batches of at most batch_size
    and yield the results as they come in.

        Usage example:
        query_parameters = [
            AgentQueryParams(prompt="What is the meaning of life")
            AgentQueryParams(prompt="Who is the prime minister of Canada")
        ]

        async for result in agent_batch(query_parameters):
            print(result)
    """
    tasks = []
    batch_num, total = 1, len(query_parameters)
    for i, qp in enumerate(query_parameters):
        tasks.append(qp.run())
        if len(tasks) >= batch_size:
            # Run a batch of tasks
            print(f"Running batch {batch_num}, {i + 1} / {total}")
            tasks_results = await asyncio.gather(
                *tasks
            )  # Returns a list of results, each one is a tuple (result, nodes)
            # Yield the results
            for r, _ in tasks_results:
                yield r
            tasks = []
            batch_num += 1
    # Run the last batch of tasks
    if tasks:
        print(f"Running final batch {batch_num}")
        tasks_results = await asyncio.gather(*tasks)
        for r, _ in tasks_results:
            yield r
    print("Done")
