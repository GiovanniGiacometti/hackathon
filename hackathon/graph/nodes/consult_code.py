from typing import Any, Dict

from hackathon.graph.state import GraphState
from hackathon.session import SessionManager


def consult_code(state: GraphState) -> Dict[str, Any]:
    """
    Consults the galactic code documents and extracts relevant documents.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Filtered out irrelevant documents and updated web_search state
    """
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state.question
    retriever = SessionManager().vectorstore_manager.vectorstore.as_retriever(search_kwargs={"k": 2})

    documents = retriever.invoke(question, filter={"is_code": True})

    return {
        "code_documents": documents,
        "requires_code": False,
        }
