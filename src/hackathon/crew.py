from typing import Any
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai import LLM
import os
from crewai_tools import SerperDevTool


@CrewBase
class Hackathon:
    """Hackathon crew"""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore
    agents: list[Agent]
    tasks: list[Task]
    llm = LLM(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
    )

    @agent
    def news_finder(self) -> Agent:
        return Agent(
            config=self.agents_config["news_finder"],
            verbose=True,
            llm=self.llm,
            tools=[SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))],
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["reporting_analyst"], verbose=True, llm=self.llm
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],
        )

    @task
    def reporting_task(self) -> Task:
        return Task(config=self.tasks_config["reporting_task"], output_file="report.md")

    @crew
    def crew(self) -> Crew:
        """Creates the Hackathon crew"""

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
