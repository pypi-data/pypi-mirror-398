import hashlib
import re

from aifoundary.audit import emit_audit_event
from aifoundary.policy.loader import load_policy


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _contains_override(prompt: str) -> bool:
    return bool(re.search(r"ignore|override|disregard", prompt, re.IGNORECASE))


def _contains_pii(text: str) -> bool:
    return bool(re.search(r"\b\d{3}-\d{2}-\d{4}\b", text))


def validate_rag(prompt: str, contexts: list[str], policy_path="rag_policy.yaml"):
    policy = load_policy(policy_path)

    prompt_l = prompt.lower()
    context = " ".join(contexts)
    context_l = context.lower()

    allowed = True
    reason = "OK"

    if _contains_override(prompt_l):
        allowed = False
        reason = "Prompt override"

    elif _contains_pii(context_l):
        allowed = False
        reason = "Context contains restricted PII"

    prompt_hash = _hash(prompt)
    context_hash = _hash(context)

    emit_audit_event({
        "decision": "allowed" if allowed else "blocked",
        "reason": reason,
        "policy_version": policy["version"],
        "prompt_hash": prompt_hash,
        "context_hash": context_hash,
    })

    return {
        "allowed": allowed,
        "reason": reason,
    }
