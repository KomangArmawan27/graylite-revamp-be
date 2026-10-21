import re
from typing import Any, Mapping, Tuple, List, Optional
from app.core.errors import AppError

PARAM_REGEX = re.compile(r"::(\w+)::")

def bind(sql: str, values: Mapping[str, Any], required_params: Optional[set[str]] = None) -> Tuple[str, List[Any]]:
    """Return (sql_with_question_marks, params_in_order). Names are matched case-insensitively."""
    required_params = required_params or set()
    
    lower_values = {k.lower(): v for k, v in values.items()}
    params: List[Any] = []
    
    def replacer(match: re.Match) -> str:
        param_name = match.group(1)
        param_name_lower = param_name.lower()
        
        if param_name_lower in lower_values:
            val = lower_values[param_name_lower]
            params.append(val)
        elif param_name_lower in [r.lower() for r in required_params]:
            raise AppError(status_code=422, code="validation_failed", message=f"Missing required parameter: {param_name}")
        else:
            params.append(None)
        return "?"

    bound_sql = PARAM_REGEX.sub(replacer, sql)
    return bound_sql, params
