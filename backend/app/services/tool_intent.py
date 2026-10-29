import re

ACTION_PATTERNS = re.compile(
    r"\b(open|launch|start|search for|look up|google|find|"
    r"take a note|note that|remind me|create file|write code|generate code|write a program|write python)\b",
    re.IGNORECASE,
)

CODE_PATTERNS = re.compile(
    r"\b(write code|generate code|write a program|write python|python code|build a script|code for|write a function|implement|create a script|coding|script)\b",
    re.IGNORECASE,
)


def looks_like_a_task(query: str) -> bool:
    return bool(ACTION_PATTERNS.search(query))


def is_code_request(query: str) -> bool:
    return bool(CODE_PATTERNS.search(query))

