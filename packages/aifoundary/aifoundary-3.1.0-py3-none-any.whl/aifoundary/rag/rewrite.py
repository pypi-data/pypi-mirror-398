def suggest_prompt(prompt: str, contexts: list[str]) -> str:
    """
    Deterministic prompt rewrite suggestion
    using key terms from context.
    """

    context_text = " ".join(contexts)

    if "when" in prompt.lower() and "founded" in context_text.lower():
        return "When was the organization founded according to the provided context?"

    if len(prompt.split()) < 4:
        return f"Based on the provided context, {prompt.strip()}"

    return f"Answer the following using only the provided context: {prompt}"
