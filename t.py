# /// script
# dependencies = [
#   "browser_use",
# ]
# ///

import asyncio
import json
from browser_use import Agent, SystemPrompt
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


load_dotenv()


class VDotSystemPrompt(SystemPrompt):
    def important_rules(self) -> str:
        # Get existing rules from parent class
        existing_rules = super().important_rules()

        # Add your custom rules
        new_rules = """
9. MOST IMPORTANT RULE:
- ALWAYS open first a new tab and go to https://vdoto2.com/calculator
"""

        # Make sure to use this pattern otherwise the exiting rules will be lost
        return f"{existing_rules}\n{new_rules}"


agent = Agent(
    task="Go to https://rundna.com/community/vdot-calculator/"
    "Select Marathon from Event Distance dropdown"
    "Enter 3:00:00 in the Time field"
    "Retrieve the Race Paces table",
    llm=ChatOpenAI(model="gpt-4o", temperature=0.0),
    use_vision=True,
    # system_prompt_class=VDotSystemPrompt,
    save_conversation_path="conversations/vdot_table.log",
)


async def main():
    history = await agent.run()

    with open("conversations/vdot_table_mine.json", "w") as file:
        json.dump(history.model_dump(), file, indent=4)

    print(history)


if __name__ == "__main__":
    asyncio.run(main())
