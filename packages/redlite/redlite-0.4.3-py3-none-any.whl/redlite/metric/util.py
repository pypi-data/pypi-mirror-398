import re
import string

_RE_PUNCT = "[" + re.escape(string.punctuation) + "]"


def normalize_string(
    input: str,
    *,
    to_lower=False,
    strip_articles=False,
    strip_punct=False,
    normalize_whitespace=False,
) -> str:
    """
    Normalizes string.

    - **input** (`str`): Input string to normalize
    - **to_lower** (`bool`): When set `True`, converts string to lower case. Default `False`.
    - **strip_articles** (`bool`): When set to `True` strips English articles "a", "an", "the". Default `False`.
    - **strip_punct** (`bool`): When set to `True` strips punctuation symbols (`string.punctuation`). Default `False`.
    - **normalize_whitespace** (`bool`): When set to `True` converts all whetespace to space, removes duplicate
            spaces, and strips leading and trailing space. Default `False`.

    Returns transformed string.
    """
    if to_lower:
        input = input.lower()

    if strip_articles:
        input = re.sub(r"\b(a|an|the)\b", " ", input, flags=re.IGNORECASE)

    if strip_punct:
        input = re.sub(_RE_PUNCT, "", input)

    if normalize_whitespace:
        input = re.sub(r"\s+", " ", input).strip()

    return input
