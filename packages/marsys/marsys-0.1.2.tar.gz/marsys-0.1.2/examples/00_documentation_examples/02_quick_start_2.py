import asyncio

from marsys.agents import Agent
from marsys.models import ModelConfig


async def main():
    # Create a single model configuration
    model_config = ModelConfig(type="api", name="anthropic/claude-haiku-4.5", provider="openrouter")

    # Create specialized agents with allowed_peers
    researcher = Agent(
        model_config=model_config, name="Researcher", goal="Expert at finding and analyzing information", instruction="You are a research specialist. Find and analyze information thoroughly.", allowed_peers=["Writer"]  # Can invoke Writer
    )

    writer = Agent(
        model_config=model_config, name="Writer", goal="Skilled at creating clear, engaging content", instruction="You are a skilled writer. Create clear, engaging content based on research.", allowed_peers=[]  # Cannot invoke other agents
    )

    # Run with automatic topology creation from allowed_peers
    result = await researcher.auto_run(task="Research the latest AI breakthroughs and write a summary", max_steps=20, verbosity=1)  # Show progress

    print(result)


asyncio.run(main())
