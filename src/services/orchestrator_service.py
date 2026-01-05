from typing import Dict, List, Optional, Tuple

from common.auth import AuthContext
from common.logging import get_logger
from services.agent_service import get_agent
from services.kb_service import retrieve
from services.llm_provider import call_llm
from services.session_service import add_message, create_session, get_session, list_messages
from services.usage_service import record_usage_event

logger = get_logger("services.orchestrator")


def execute_turn(
    company_id: str,
    agent_id: str,
    session_id: Optional[str],
    message: str,
    metadata: Optional[Dict],
    actor: AuthContext,
) -> Tuple[str, str, Dict, List[Dict[str, str]]]:
    agent = get_agent(company_id, agent_id)
    metadata = metadata or {}
    if session_id:
        session = get_session(company_id, session_id, agent_id=agent_id)
    else:
        session = create_session(company_id, agent_id, metadata.get("user_external_id"), "api")
        session_id = session.id
    add_message(company_id, session_id, "user", message)
    history = list_messages(company_id, session_id, limit=20)
    llm_input = [{"role": msg.role, "content": msg.content} for msg in history]
    citations: List[Dict[str, str]] = []
    did_kb_query = False
    if agent.rag_config and agent.rag_config.get("enabled"):
        top_k = int(agent.rag_config.get("top_k", 3))
        citations = retrieve(company_id, agent_id, message, top_k=top_k)
        if citations:
            llm_input.append({"role": "system", "content": "Retrieved context (untrusted):"})
            for citation in citations:
                llm_input.append({"role": "system", "content": citation["snippet"]})
        record_usage_event(company_id, agent_id, session_id, "kb_query", 1, "calls")
        did_kb_query = True
    response = call_llm(llm_input, agent.model_config)
    add_message(company_id, session_id, "assistant", response.content)
    record_usage_event(company_id, agent_id, session_id, "llm_tokens_in", response.usage.tokens_in, "tokens")
    record_usage_event(company_id, agent_id, session_id, "llm_tokens_out", response.usage.tokens_out, "tokens")
    logger.info("turn_complete %s", session_id)
    usage_summary = {
        "tokens_in": response.usage.tokens_in,
        "tokens_out": response.usage.tokens_out,
        "tool_calls": 0,
        "kb_queries": 1 if did_kb_query else 0,
    }
    return session_id, response.content, usage_summary, citations
