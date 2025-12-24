import asyncio

from marsys.agents import Agent
from marsys.coordination import Orchestra
from marsys.models import ModelConfig


async def main():
    # Create the agent first
    poet = Agent(model_config=ModelConfig(type="api", name="anthropic/claude-haiku-4.5", provider="openrouter"), name="Poet", goal="Creative poet", instruction="You are a talented poet who writes beautiful, evocative poetry.")

    # One-line execution
    result = await Orchestra.run(task="Write a haiku about artificial intelligence", topology={"agents": ["Poet"], "flows": []})

    print(result.final_response)


asyncio.run(main())
