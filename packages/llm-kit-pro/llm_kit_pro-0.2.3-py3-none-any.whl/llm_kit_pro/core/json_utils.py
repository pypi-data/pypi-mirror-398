import json
import re
from typing import Any, Dict


class JSONExtractionError(ValueError):
    pass


def extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()

    # Fast path
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # ```json fenced block
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    # Any JSON object
    brace = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace:
        return json.loads(brace.group(1))

    raise JSONExtractionError("No valid JSON object found in model output")

