import logging
import asyncio
from typing import Optional, List, Any

import instructor
from llama_cpp import Llama

from .schema import GraphData
from .renderer import to_mermaid, run_mmdc

logger = logging.getLogger("slm_graph.core")

class DictToObject:
    """
    Helper class to wrap llama-cpp-python dictionary responses 
    into an object format that instructor expects.
    """
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [DictToObject(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, DictToObject(b) if isinstance(b, dict) else b)

class EasyGraph:
    """The high-level API for slm-graph using local Llama-cpp inference."""

    def __init__(self, model_path: str, n_ctx: int = 2048):
        """
        Initializes the local inference engine.
        """
        logger.info(f"Loading local model from {model_path}...")
        # verbose=False reduces terminal clutter during inference
        self.llm = Llama(model_path=model_path, n_ctx=n_ctx, verbose=False)
        
        # We define a custom 'create' function that wraps the dict response in an object
        def llama_cpp_create_wrapper(*args, **kwargs):
            response_dict = self.llm.create_chat_completion(*args, **kwargs)
            return DictToObject(response_dict)

        # Patch the wrapper instead of the raw llm.create_chat_completion
        self.client = instructor.patch(
            create=llama_cpp_create_wrapper,
            mode=instructor.Mode.JSON_SCHEMA
        )

    async def generate(
        self, 
        prompt: str, 
        output_name: str = "graph", 
        formats: Optional[List[str]] = None
    ) -> str:
        """Processes prompt, validates JSON, and renders graph files."""
        formats = formats or ["svg"]
        
        logger.info("Extracting graph structure using local SLM...")
        
        # System prompt is critical for getting clean results from 1B models
        system_msg = (
            "You are a graph generator. Extract nodes and edges from the text. "
            "Respond ONLY with the structured JSON format provided in the schema."
        )

        structured_data: GraphData = self.client(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            response_model=GraphData,
        )

        mermaid_code = to_mermaid(structured_data)
        
        # Parallel file rendering
        tasks = [run_mmdc(mermaid_code, f"{output_name}.{fmt}") for fmt in formats]
        await asyncio.gather(*tasks)
        
        return mermaid_code

    def generate_sync(self, *args, **kwargs):
        """Synchronous entry point for the generate method."""
        return asyncio.run(self.generate(*args, **kwargs))