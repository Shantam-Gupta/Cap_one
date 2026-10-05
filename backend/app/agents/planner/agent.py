"""Planner Agent Implementation."""
import logging
from typing import Any, Dict, List, Optional

from app.agents.planner.schemas import PlanOutput

logger = logging.getLogger(__name__)
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider


class PlannerAgent:
    """
    Decomposes natural language user goals into structured, actionable subtask plans.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()

    async def plan(
        self,
        task_prompt: str,
        available_files: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
    ) -> PlanOutput:
        system_prompt = (
            "You are the Lead Technical Planner in the ReRun Autonomous Architecture.\n"
            "Your objective is to decompose the user's task into a highly detailed, rigorous, step-by-step execution plan.\n"
            "DO NOT provide just a high-level overview. Break the task down into granular, atomic subtasks (e.g., file-by-file or function-by-function).\n"
            "You must return ONLY valid JSON with keys: 'goal', 'requirements', 'subtasks', "
            "'dependencies', 'expected_outputs', 'validation_requirements', 'constraints'.\n"
            "Subtasks must have: 'id', 'name', 'description' (provide full, comprehensive detail of what to do), and 'dependencies'."
        )

        files_str = ", ".join(available_files) if available_files else "None provided"
        constraints_str = ", ".join(constraints) if constraints else "Default sandbox constraints apply"

        user_content = (
            f"User Objective: {task_prompt}\n"
            f"Available Files in Workspace: {files_str}\n"
            f"Active Constraints: {constraints_str}\n\n"
            "Synthesize a comprehensive execution plan. Provide a highly detailed 'description' for every single subtask explaining exactly how to implement it, what libraries to use, and edge cases to consider."
        )

        try:
            resp = await self.llm.complete_structured(
                prompt=user_content,
                system_prompt=system_prompt,
            )
            data = resp.structured or {}
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            data = {}

        # Fallback if keys missing or invalid type
        if "goal" not in data or not isinstance(data["goal"], str):
            data["goal"] = task_prompt
        
        if "subtasks" not in data or not isinstance(data["subtasks"], list):
            data["subtasks"] = [
                {"id": 1, "name": f"Address goal: {task_prompt[:50]}...", "dependencies": []}
            ]
            
        if "expected_outputs" not in data or not isinstance(data["expected_outputs"], list):
            data["expected_outputs"] = [{"name": "output.txt", "type": "file", "required": False}]

        try:
            return PlanOutput.model_validate(data)
        except Exception as e:
            logger.error(f"Plan validation failed: {e}")
            return PlanOutput(
                goal=task_prompt,
                subtasks=[{"id": 1, "name": "Execute user request directly", "dependencies": []}]
            )
