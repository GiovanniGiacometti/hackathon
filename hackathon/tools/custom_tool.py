from browser_use import Agent, SystemPrompt
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field, field_validator
from langchain_openai import ChatOpenAI
from enum import Enum


class RunningCompetitionType(str, Enum):
    """Enum for the type of run competition"""

    marathon = "marathon"
    half_marathon = "half_marathon"
    ten_k = "ten_k"
    five_k = "five_k"


class VdotCalculatorToolInput(BaseModel):
    """Input schema for the VdotCalculatorTool."""

    run_competition: RunningCompetitionType = Field(
        description="Type of running competition."
    )
    time: str = Field(description="Time taken to complete the run.")

    @field_validator
    @classmethod
    def validate_time(cls, value: str) -> str:
        """Validate the time input, making sure
        it's in the correct format, HH:MM:SS."""

        time_parts = value.split(":")
        if len(time_parts) != 3:
            raise ValueError(
                f"Time must be in HH:MM:SS format, "
                f"input received has only {len(time_parts)} parts."
            )

        for i, part in enumerate(time_parts):
            match i:
                case 0:
                    part_name = "hours"
                case 1:
                    part_name = "minutes"
                case 2:
                    part_name = "seconds"

            if len(part) != 2:
                raise ValueError(
                    f"Each part of the time must be 2 digits long, received: {part} "
                    f"for {part_name} which is not 2 digits long."
                )

            if not part.isdigit():
                raise ValueError(
                    f"Time must be in HH:MM:SS format, received {part}"
                    f"for {part_name} which is not a digit."
                )

        return value


class VDotSystemPrompt(SystemPrompt):
    def important_rules(self) -> str:
        # Get existing rules from parent class
        existing_rules = super().important_rules()

        # Add your custom rules
        new_rules = """
9. MOST IMPORTANT RULE:
- ALWAYS open first a new tab and go to https://vdoto2.com/calculator/!!!
"""

        # Make sure to use this pattern otherwise the exiting rules will be lost
        return f"{existing_rules}\n{new_rules}"


class VDotCalculatorTool(BaseTool):
    name: str = "VDotCalculatorTool"
    description: str = "This tool calculates the VDOT score for a given run."
    args_schema: Type[BaseModel] = VdotCalculatorToolInput

    def get_llm(self) -> ChatOpenAI:
        return ChatOpenAI(model="gpt-4o-mini")

    def _run(self, input: VdotCalculatorToolInput) -> str:
        # Implementation goes here
        agent = Agent(
            task="",
            llm=self.get_llm(),
            use_vision=True,
            system_prompt_class=VDotSystemPrompt,
        )

        return agent.run(input.run_competition, input.time)
