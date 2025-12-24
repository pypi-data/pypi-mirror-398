import re

def _normalize(text: str) -> list[str]:
    """
    Lowercase, strip punctuation, split into meaningful tokens.
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    return [t for t in text.split() if len(t) > 2]


def check_coverage(prompt: str, contexts: list[str], *, min_ratio: float = 0.3):
    """
    Explainable lexical coverage check with normalization.
    """

    prompt_terms = set(_normalize(prompt))
    context_terms = set(_normalize(" ".join(contexts)))

    hits = prompt_terms & context_terms
    misses = prompt_terms - hits

    ratio = len(hits) / max(len(prompt_terms), 1)

    return {
        "ok": ratio >= min_ratio,
        "coverage_ratio": round(ratio, 2),
        "required_ratio": min_ratio,
        "matched_terms": sorted(hits),
        "missing_terms": sorted(misses),
    }
