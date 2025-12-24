"""
Example demonstrating agent schema validation functionality.

This script shows:
1. Creating agents with different schema formats (list, dict, full JSON schema)
2. Input validation during agent invocation
3. Output validation with error handling and re-prompting
4. Multi-agent communication with schemas
5. Real-world research workflow using schemas
"""

import asyncio
import json
from marsys.agents.agents import Agent
from marsys.models.models import ModelConfig
from marsys.agents.utils import RequestContext, LogLevel
from marsys.environment.tools import AVAILABLE_TOOLS


async def example_schema_formats():
    """Demonstrate different schema input formats."""
    print("=== Schema Format Examples ===\n")
    
    # Create a simple model config for testing
    model_config = ModelConfig(
        type="api",
        provider="openai", 
        name="gpt-4o-mini",
        api_key="your-api-key-here",
        temperature=0.7,
        max_tokens=1000
    )
    
    # 1. List of strings format (simplest)
    print("1. List of strings schema:")
    researcher_agent = Agent(
        model_config=model_config,
        description="You are a research agent that answers questions about specific topics.",
        input_schema=["sub_question"],  # Simple list format
        output_schema=["answer"],       # Simple output format
        agent_name="researcher"
    )
    print(f"   Input schema: {researcher_agent.input_schema}")
    print(f"   Compiled: {researcher_agent._compiled_input_schema}")
    print()
    
    # 2. Dict of types format (more structured)
    print("2. Dict of types schema:")
    search_agent = Agent(
        model_config=model_config,
        description="You are a search agent that finds information with specific parameters.",
        input_schema={
            "query": str,
            "max_results": int,
            "include_metadata": bool
        },
        output_schema={
            "results": list,
            "total_found": int
        },
        agent_name="searcher"
    )
    print(f"   Input schema: {search_agent.input_schema}")
    print(f"   Compiled: {search_agent._compiled_input_schema}")
    print()
    
    # 3. Full JSON schema format (most flexible)
    print("3. Full JSON schema:")
    synthesizer_agent = Agent(
        model_config=model_config,
        description="You synthesize research findings into comprehensive reports.",
        input_schema={
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "minLength": 5,
                    "description": "The original user question"
                },
                "validated_data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "minItems": 1,
                    "description": "List of validated research data"
                }
            },
            "required": ["user_query", "validated_data"],
            "additionalProperties": False
        },
        output_schema={
            "type": "object",
            "properties": {
                "report": {
                    "type": "string",
                    "minLength": 100,
                    "description": "A comprehensive research report"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence score for the report"
                }
            },
            "required": ["report", "confidence"]
        },
        agent_name="synthesizer"
    )
    print(f"   Input schema: {json.dumps(synthesizer_agent.input_schema, indent=2)}")
    print()


async def example_peer_instructions():
    """Demonstrate how peer agent instructions include schema information."""
    print("=== Peer Agent Instructions with Schemas ===\n")
    
    model_config = ModelConfig(
        type="api",
        provider="openai",
        name="gpt-4o-mini", 
        api_key="your-api-key-here"
    )
    
    # Create agents with schemas
    researcher = Agent(
        model_config=model_config,
        description="Research agent",
        input_schema=["research_topic"],
        output_schema=["findings"],
        agent_name="researcher"
    )
    
    analyzer = Agent(
        model_config=model_config,
        description="Analysis agent",
        input_schema={"data": dict, "analysis_type": str},
        output_schema={"analysis": str, "confidence": float},
        agent_name="analyzer"
    )
    
    # Coordinator that can call both agents
    coordinator = Agent(
        model_config=model_config,
        description="Coordinates research and analysis workflow",
        allowed_peers=["researcher", "analyzer"],
        agent_name="coordinator"
    )
    
    # Show how peer instructions include schema information
    peer_instructions = coordinator._get_peer_agent_instructions()
    print("Coordinator's peer agent instructions:")
    print(peer_instructions)
    print()


async def example_input_validation():
    """Demonstrate input validation during agent calls."""
    print("=== Input Validation Examples ===\n")
    
    model_config = ModelConfig(
        type="api",
        provider="openai",
        name="gpt-4o-mini",
        api_key="your-api-key-here"
    )
    
    # Create agent with strict input schema
    data_processor = Agent(
        model_config=model_config,
        description="Processes structured data according to specific schema",
        input_schema={
            "dataset": list,
            "processing_type": str,
            "options": dict
        },
        agent_name="processor"
    )
    
    # Test with valid input
    print("1. Testing valid input:")
    valid_input = {
        "dataset": [{"id": 1, "value": "test"}],
        "processing_type": "analysis",
        "options": {"detailed": True}
    }
    print(f"   Input: {valid_input}")
    print("   ✓ This would pass validation")
    print()
    
    # Test with invalid input (missing required field)
    print("2. Testing invalid input (missing required field):")
    invalid_input = {
        "dataset": [{"id": 1, "value": "test"}],
        "processing_type": "analysis"
        # Missing 'options' field
    }
    print(f"   Input: {invalid_input}")
    print("   ✗ This would fail validation")
    print()
    
    # Test with wrong data type
    print("3. Testing invalid input (wrong data type):")
    wrong_type_input = {
        "dataset": "not a list",  # Should be list
        "processing_type": "analysis",
        "options": {"detailed": True}
    }
    print(f"   Input: {wrong_type_input}")
    print("   ✗ This would fail validation")
    print()


async def example_output_validation():
    """Demonstrate output validation and re-prompting."""
    print("=== Output Validation and Re-prompting ===\n")
    
    print("When an agent produces output that doesn't match its output schema:")
    print("1. The system validates the response against the schema")
    print("2. If validation fails, it provides specific feedback to the agent")
    print("3. The agent gets re-prompted to fix the output format")
    print("4. This continues until valid output is produced or max attempts reached")
    print()
    
    print("Example scenario:")
    print("- Agent has output_schema: {'report': str, 'confidence': float}")
    print("- Agent responds: {'summary': 'text', 'score': 0.8}  # Wrong field names")
    print("- System responds: 'Your output doesn't match required schema...'")
    print("- Agent corrects: {'report': 'text', 'confidence': 0.8}  # ✓ Valid")
    print()


async def example_real_world_workflow():
    """Demonstrate a complete multi-agent workflow with schemas."""
    print("=== Real-World Research Workflow with Schemas ===\n")
    
    # This is a conceptual example - would need actual API keys to run
    print("Workflow: User Query → Research → Analysis → Synthesis")
    print()
    
    workflow_description = """
    1. OrchestratorAgent (no input/output schemas - accepts any query)
       ↓
    2. ResearcherAgent 
       - Input: {"topic": str}
       - Output: {"findings": list, "sources": list}
       ↓  
    3. AnalyzerAgent
       - Input: {"data": dict, "analysis_type": str} 
       - Output: {"analysis": str, "confidence": float}
       ↓
    4. SynthesizerAgent
       - Input: {"user_query": str, "validated_data": list}
       - Output: {"report": str, "confidence": float}
    """
    
    print(workflow_description)
    print()
    
    print("Benefits of using schemas in this workflow:")
    print("✓ Type safety - ensures data flows correctly between agents")
    print("✓ Clear contracts - each agent knows what to expect")
    print("✓ Error prevention - catches format issues early")
    print("✓ Self-documenting - schemas serve as API documentation")
    print("✓ Validation feedback - agents can learn from schema violations")
    print()


async def example_backward_compatibility():
    """Show that agents without schemas continue to work normally."""
    print("=== Backward Compatibility ===\n")
    
    model_config = ModelConfig(
        type="api",
        provider="openai",
        name="gpt-4o-mini",
        api_key="your-api-key-here"
    )
    
    # Agent without any schemas (legacy behavior)
    legacy_agent = Agent(
        model_config=model_config,
        description="I work without schemas, just like before",
        agent_name="legacy"
    )
    
    print("Legacy agent without schemas:")
    print(f"- Input schema: {legacy_agent.input_schema}")
    print(f"- Output schema: {legacy_agent.output_schema}")
    print(f"- Compiled input schema: {legacy_agent._compiled_input_schema}")
    print(f"- Compiled output schema: {legacy_agent._compiled_output_schema}")
    print()
    print("✓ This agent will accept any input and produce any output")
    print("✓ No validation overhead for agents that don't need it")
    print("✓ Fully backward compatible with existing code")
    print()


async def main():
    """Run all examples."""
    await example_schema_formats()
    await example_peer_instructions()
    await example_input_validation()
    await example_output_validation()
    await example_real_world_workflow()
    await example_backward_compatibility()
    
    print("=== Summary ===")
    print("Schema validation provides:")
    print("1. Three user-friendly input formats (list, dict, full JSON schema)")
    print("2. Runtime validation of inputs and outputs")
    print("3. Clear error messages and re-prompting for fixes")
    print("4. Enhanced peer agent instructions with schema info")
    print("5. Full backward compatibility with existing agents")
    print("6. Type safety and contract clarity for multi-agent workflows")


if __name__ == "__main__":
    # Note: This example requires actual API keys to run the agents
    # For demonstration purposes, we just show the schema setup
    asyncio.run(main()) 