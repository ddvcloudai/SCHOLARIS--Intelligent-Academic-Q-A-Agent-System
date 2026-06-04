# guardrail.py — Security layer: validates and sanitizes all incoming queries

import re 

# ── Token limits ──────────────────────────────────────────────────────────────
MIN_INPUT_TOKENS = 3     
MAX_INPUT_CHARS  = 500   

# ── Known prompt-injection patterns ──────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore (all |previous |prior |above |the )?instructions",
    r"disregard (all |previous |prior |above |the )?instructions",
    r"forget (everything|all|your instructions)",
    r"you are now",
    r"act as (a |an )?(?!math|biology|history)",  # allow subject keywords
    r"new persona",
    r"system prompt",
    r"jailbreak",
    r"do anything now",
    r"dan mode",
    r"sudo ",
    r"<\s*script",          
    r"```.*?(exec|eval|os\.|subprocess)",  
    r"reveal (your |the )?(prompt|instructions|system)",
    r"print (your |the )?(prompt|instructions|context)",
]


_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def validate_query(query: str) -> tuple[bool, str]:
    """
    Validates an incoming query for safety and basic sanity.

    Returns:
        (True, cleaned_query)  — if the query is safe to process
        (False, error_message) — if the query should be rejected
    """

    
    query = query.strip()

   
    if len(query.split()) < MIN_INPUT_TOKENS:
        return False, "Query is too short. Please provide a meaningful question."

    
    if len(query) > MAX_INPUT_CHARS:
        return False, (
            f"Query exceeds the {MAX_INPUT_CHARS}-character limit "
            f"({len(query)} chars). Please shorten your question."
        )

    
    for pattern in _COMPILED:
        if pattern.search(query):
            return False, (
                "⚠️ Query blocked: potential prompt injection detected. "
                "Please ask a straightforward academic question."
            )

    
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", query):
        return False, "Query contains invalid characters. Please use plain text."

    
    return True, query
