import dotenv

from marsys.agents import Agent
from marsys.models import ModelConfig

dotenv.load_dotenv()  # Load environment variables from .env file


async def main():
    # Create agents with same configuration
    model_config = ModelConfig(type="api", name="anthropic/claude-sonnet-4.5", provider="openrouter")

    # Define agents and their allowed interactions
    researcher = Agent(
        model_config=model_config,
        name="Researcher",
        goal="Expert at finding and analyzing information",
        instruction="You are a research specialist. Find and analyze information thoroughly.",
        allowed_peers=["Writer"],  # Can invoke the Writer agent
    )

    writer = Agent(
        model_config=model_config, name="Writer", goal="Skilled at creating clear, engaging content", instruction="You are a skilled writer. Create clear, engaging content based on research.", allowed_peers=[]  # Cannot invoke other agents
    )

    # Run with automatic topology creation
    result = await researcher.auto_run(task="Research AI trends and write a report", max_steps=20, verbosity=1)  # Show progress

    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
