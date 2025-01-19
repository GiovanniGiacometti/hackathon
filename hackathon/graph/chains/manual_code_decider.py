from langchain_core.prompts import ChatPromptTemplate
from hackathon.session import SessionManager
from hackathon.graph.models import DecideManualCode
from hackathon.graph.prompts import DECIDE_MANUAL_CODE_PROMPT

llm = SessionManager().model_manager.model
structured_llm_router = llm.with_structured_output(DecideManualCode)


decide_manual_code_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", DECIDE_MANUAL_CODE_PROMPT),
        ("human", "{question}"),
    ]
)

manual_code_decider = decide_manual_code_prompt | structured_llm_router
