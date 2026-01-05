from dataclasses import dataclass
from typing import Dict, List

from common.logging import get_logger
from common.metrics import record_llm_call

logger = get_logger("services.llm")


@dataclass
class LlmUsage:
    tokens_in: int
    tokens_out: int


@dataclass
class LlmResponse:
    content: str
    usage: LlmUsage


def call_llm(messages: List[Dict], model_config: Dict) -> LlmResponse:
    last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    reply = f"Echo: {last_user}"
    tokens_in = max(1, len(last_user.split()))
    tokens_out = max(1, len(reply.split()))
    record_llm_call()
    logger.info("llm_call")
    return LlmResponse(content=reply, usage=LlmUsage(tokens_in=tokens_in, tokens_out=tokens_out))
