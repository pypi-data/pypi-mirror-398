from aifoundary.rag.rewrite import suggest_prompt
from aifoundary.rag.secure_rag import validate_rag


def validate_with_retry(
    prompt: str,
    contexts: list[str],
    *,
    policy_path: str,
    mode: str = "strict",
):
    first = validate_rag(
        prompt,
        contexts,
        policy_path=policy_path,
        mode=mode,
    )

    if first["allowed"]:
        return first

    if first["reason"] != "Insufficient context coverage":
        return first

    rewritten = suggest_prompt(prompt, contexts)

    second = validate_rag(
        rewritten,
        contexts,
        policy_path=policy_path,
        mode=mode,
    )

    return {
        "allowed": second["allowed"],
        "reason": second["reason"],
        "original_prompt": prompt,
        "rewritten_prompt": rewritten,
        "retry_used": True,
    }
