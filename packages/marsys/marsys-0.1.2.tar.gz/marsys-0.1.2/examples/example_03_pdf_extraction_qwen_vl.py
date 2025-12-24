"""
PDF Content Extraction using Qwen3-VL (Local Vision-Language Model)

Demonstrates using MARSYS FileOperationAgent with local Qwen3-VL for PDF analysis.

Requirements:
    pip install marsys[local-models]

"""

import asyncio
import os
from pathlib import Path

from marsys.agents.file_operation_agent import FileOperationAgent
from marsys.coordination import Orchestra
from marsys.coordination.config import ExecutionConfig, StatusConfig
from marsys.models.models import ModelConfig

# Set Hugging Face cache directory (must be set before importing transformers/marsys)
HF_CACHE_DIR = Path(__file__).parent.parent / ".cache"
HF_CACHE_DIR.mkdir(exist_ok=True)
os.environ["HF_HOME"] = str(HF_CACHE_DIR)

async def analyze_pdf(pdf_path: str):
    """Analyze a PDF file using FileOperationAgent with Qwen3-VL."""

    # Local VLM model config
    vlm_config = ModelConfig(
        type="local",
        name="Qwen/Qwen3-VL-8B-Instruct",
        model_class="vlm",
        backend="huggingface",
        torch_dtype="bfloat16",
        device_map="auto",
        max_tokens=8192,
        thinking_budget=500,
        trust_remote_code=True,
    )

    # FileOperationAgent automatically handles PDF reading with image extraction
    file_agent = FileOperationAgent(
        model_config=vlm_config,
        name="PDFAnalyzer",
        goal="Extract and analyze content from PDF files including text and images.",
        instruction="""You are a PDF analysis specialist with vision capabilities.
Read the PDF using read_file tool. Analyze both text and images.
Provide: document overview, key content, image descriptions, and summary.""",
    )

    topology = {
        "agents": ["PDFAnalyzer"],
        "flows": [],
        # "entry_point": "PDFAnalyzer",
        # "exit_points": ["PDFAnalyzer"],
    }

    result = await Orchestra.run(
        task=f"Read and extract the PDF at: {pdf_path}",
        topology=topology,
        execution_config=ExecutionConfig(
            status=StatusConfig.from_verbosity(2),
        ),
        max_steps=20,
    )

    return result.final_response


if __name__ == "__main__":
    # Example usage
    pdf_file = "/home/rezaho/research_projects/Multi-agent_AI_Learning/tmp/downloads/2206.07555v1.pdf"

    print(f"Analyzing: {pdf_file}")
    response = asyncio.run(analyze_pdf(pdf_file))
    print(response)
