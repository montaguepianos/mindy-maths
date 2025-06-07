import re
from sympy import sympify

NUMBER_WORDS = {
    'zero': 0,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
    'thirteen': 13,
    'fourteen': 14,
    'fifteen': 15,
    'sixteen': 16,
    'seventeen': 17,
    'eighteen': 18,
    'nineteen': 19,
    'twenty': 20,
}

def evaluate_expression(expr: str):
    """Safely evaluate a mathematical expression using sympy."""
    try:
        return float(sympify(expr))
    except Exception:
        return None

def parse_number(text: str):
    """Extract a numeric value from a piece of text."""
    if not text:
        return None
    lowered = text.lower()
    for word, value in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\b", lowered):
            return float(value)
    # Try direct evaluation
    cleaned = re.sub(r"[^0-9\-+*/.]+", " ", lowered)
    result = evaluate_expression(cleaned)
    if result is not None:
        return result
    # Fallback to first number in the text
    m = re.search(r"-?\d+(?:\.\d+)?", lowered)
    if m:
        try:
            return float(m.group())
        except ValueError:
            pass
    return None

def check_answer(user_answer: str, expected_answer: str, tolerance: float = 1e-2) -> bool:
    """Return True if the user's answer matches the expected answer."""
    user_val = parse_number(user_answer)
    expected_val = parse_number(expected_answer)
    if user_val is not None and expected_val is not None:
        return abs(user_val - expected_val) <= tolerance
    if user_answer and expected_answer:
        return user_answer.strip().lower() == expected_answer.strip().lower()
    return False
