
from typing import Dict, Any
from hackathon.graph.state import GraphState
from hackathon.graph.models import DecideManualCode
from hackathon.graph.chains.manual_code_decider import manual_code_decider


def decide_manual_code(state: GraphState) -> Dict[str, Any]:
    """
    Decide whether to consult the manual or not.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): The updated state
    """
    print("---DECIDE WHETHER TO CONSULT MANUAL or CODE---")
    question = state.question
    source: DecideManualCode = manual_code_decider.invoke({"question": question})  # type: ignore

    return {
        "requires_manual": source.requires_manual,
        "requires_code": source.requires_code
    }