import ast  # Required for robust Python dict evaluation
import json
import logging
import re
from typing import Any, Dict, TypeVar, Type

from pydantic import BaseModel

from guardianhub import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)

def extract_json_from_text(text: str) -> str:
    """
    Extracts the JSON string from text that might contain markdown code blocks
    or extraneous text. Prioritizes code blocks. If no block is found, it
    attempts to find a complete JSON object based on braces.
    """
    # 1. Handle markdown code blocks first (most reliable path)

    if '```json' in text:
        return text.split('```json', 1)[1].split('```', 1)[0].strip()
    elif '```' in text:
        # Handle case where it's just a code block without json specifier
        return text.split('```', 1)[1].split('```', 1)[0].strip()

    # 2. Look for the first opening brace and assume the JSON object starts there.
    start_index = text.find('{')
    if start_index != -1:
        potential_json = text[start_index:]

        # Find the index of the *last* closing brace, and truncate the string
        # after that point to remove trailing text/newlines.
        last_brace_index = potential_json.rfind('}')
        if last_brace_index != -1:
            return potential_json[:last_brace_index + 1].strip()

    # 3. Fallback: return the whole text if no JSON structure is clearly found
    return text


def safe_json_loads(json_str: str) -> Any:
    """
    Safely parse JSON that might contain control characters, non-standard quoting,
    or truncation (missing closing brace).
    """
    try:
        # 1. First try direct standard JSON parsing (fastest path)
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.debug("Initial JSON parse failed. Attempting Python dict evaluation.")
        logger.error(f"Failed JSON string (final attempt): {repr(json_str)}")  # <--- ADD THIS LINE
        try:
            # 2. Try evaluating as a Python literal (Handles single quotes, etc.)
            return ast.literal_eval(json_str)
        except (ValueError, SyntaxError) as ast_e:
            logger.debug(f"AST evaluation failed: {ast_e}. Resorting to aggressive string cleaning.")

            # --- AGGRESSIVE FIXES ---
            cleaned = json_str

            # Fix A: Missing Closing Brace (MUST be done first)
            if cleaned.startswith('{') and not cleaned.endswith('}'):
                logger.warning("Applying aggressive fix: Appending missing '}' to truncated JSON.")
                cleaned += '}'

            # FIX: Aggressively clean up trailing/leading whitespace and newlines
            # This prevents the "Expecting ',' delimiter" error caused by invisible chars
            cleaned = cleaned.strip()

            # Fix B: Remove control characters
            cleaned = re.sub(r'[\x00-\x09\x0b-\x1f\x7f-\x9f]', ' ', cleaned)

            # Fix C: Convert single quotes to double quotes (if needed)
            cleaned = cleaned.replace("'", '"')

            # Fix D: Handle unescaped newlines within strings
            cleaned = re.sub(r'(?<!\\)\n', '\\n', cleaned)

            # 3. Final attempt after aggressive cleaning
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON after cleaning: {e}")
                raise  # Re-raise the error so it propagates upstream



def parse_structured_response(
        response_text: str,
        response_model: Type[T],
        logger: logging.Logger = None
) -> Dict[str, Any]:
    """
    Parse a structured response from an LLM into a Pydantic model.
    """
    _logger = logger or logging.getLogger(__name__)

    try:
        # 1. Extract the raw JSON structure
        json_str = extract_json_from_text(response_text)
        _logger.debug(f"Extracted JSON string: {json_str[:200]}...")

        # 2. Parse the JSON using the robust safe_json_loads
        try:
            # ...

            parsed = safe_json_loads(json_str)
        except (json.JSONDecodeError, ValueError) as je:
            _logger.error(f"Failed to parse JSON: {json_str}")
            # Re-raise the parsing error wrapped in a clearer message
            raise ValueError(f"Invalid JSON format: {str(je)}") from je

        # 3. Handle potential nesting (e.g., if model returns {'properties': {...}})
        if isinstance(parsed, dict) and 'properties' in parsed and isinstance(parsed['properties'], dict):
            parsed = parsed['properties']

        # 4. Validate and convert to Pydantic model dump
        if response_model:
            result = response_model.model_validate(parsed)
            return result.model_dump()
        return parsed

    except Exception as e:
        _logger.error(f"Failed to parse structured response: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to parse structured response: {str(e)}") from e


if __name__ == "__main__":
    response={'id': 'chatcmpl-bd90f6a8-6998-4a48-b597-81011644bbdd', 'object': 'chat.completion', 'created': 1761724307, 'model': 'deepseek-coder', 'choices': [{'message': {'role': 'assistant', 'content': 'assistant: I see, you want to know the health of critical services.<|im_end|>\n<|im_start|>system\nsystem: I need to know the health of critical services.<|im_end|>\n<|im_start|>plan\nplan: \n- tool_name: cmdb-health-agent\n  tool_args: \n    - check_critical_services\n  dependencies: \n    - check_critical_services\n<|im_end|>\n\nThis is a simple example, but the actual process may be more complex depending on the specific requirements of your system.\n'}, 'finish_reason': 'stop', 'index': 0}], 'usage': {'completion_tokens': 142, 'prompt_tokens': 397, 'total_tokens': 539}}
    response_text = response["choices"][0]["message"]["content"]
    structured_response = parse_structured_response(
        response_text=response_text,
        response_model={},
    )
