from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from hackathon.graph.consts import (
    EXTRACT_METADATA,
    RETRIEVE,
    GENERATE,
    DECIDE_MANUAL_CODE,
    RETRIEVE,
    RETRIEVE_CODE,
    RETRIEVE_MANUAL,
    FORMAT_OUTPUT,
)

from hackathon.graph.nodes.extract_metadata import extract_metadata
from hackathon.graph.nodes.retrieve import retrieve
from hackathon.graph.nodes.generate import generate
from hackathon.graph.nodes.decide_manual_code import decide_manual_code
from hackathon.graph.nodes.consult_manual import consult_manual
from hackathon.graph.nodes.consult_code import consult_code
from hackathon.graph.nodes.format_output import format_output

from hackathon.graph.state import GraphState
from hackathon.session import SessionManager


memory = MemorySaver()
    
def decide_to_retrieve(state: GraphState):
    """Decides whether to retrieve documents from the manual and/or the guide
    based on the question.
    """
    print("---DECISION: RETRIEVE FROM MANUAL---")
    if state.requires_manual:
        return RETRIEVE_MANUAL
    elif state.requires_code:
        print("---DECISION: RETRIEVE FROM CODE---")
        return RETRIEVE_CODE
    else:
        return RETRIEVE

def grade_generation_grounded_in_documents_and_question(
    state: GraphState,
) -> str:
    """Grades the generation based on whether it is grounded in the documents and
    addresses the question.
    """
    print("---CHECK HALLUCINATIONS---")
    question = state.question
    documents = state.documents
    generation = state.generation

    hallucination_score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )

    if hallucination_score.binary_score:
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        print("---GRADE GENERATION vs QUESTION---")
        answer_grader_score = answer_grader.invoke(
            {"question": question, "generation": generation}
        )
        if answer_grader_score.binary_score:
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "hallucination"



workflow = StateGraph(GraphState)
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GENERATE, generate)
workflow.add_node(RETRIEVE_CODE, consult_code)
workflow.add_node(RETRIEVE_MANUAL, consult_manual)
workflow.add_node(DECIDE_MANUAL_CODE, decide_manual_code)

workflow.set_conditional_entry_point(
    decide_to_retrieve,
    {
        RETRIEVE_MANUAL: RETRIEVE_MANUAL,
        RETRIEVE_CODE: RETRIEVE_CODE,
        RETRIEVE: RETRIEVE,
    },
)
workflow.add_edge(DECIDE_MANUAL_CODE, decide_to_retrieve)
workflow.add_edge(RETRIEVE_MANUAL, decide_to_retrieve)
workflow.add_edge(RETRIEVE_CODE, decide_to_retrieve)
workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)
workflow.add_conditional_edges(
    GRADE_DOCUMENTS,
    decide_to_generate,
    {
        WEBSEARCH: WEBSEARCH,
        GENERATE: GENERATE,
    },
)
workflow.add_edge(WEBSEARCH, GENERATE)
workflow.add_conditional_edges(
    GENERATE,
    grade_generation_grounded_in_documents_and_question,
    {
        "hallucination": GENERATE,
        "useful": END,
        "not useful": WEBSEARCH,
    },
)


app = workflow.compile(checkpointer=memory)

# app.get_graph().draw_mermaid_png(output_file_path="graph.png")
