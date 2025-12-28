import os
import json
from datetime import datetime

def get_env_bool(var_name: str) -> bool:
    """
    Returns True if the environment variable doesn't exist,
    otherwise converts its value to a boolean.
    """
    value = os.getenv(var_name)

    if value is None:
        return True  # Default to True if variable not set

    # Normalize and convert string to boolean
    value_str = value.strip().lower()
    if value_str in ('1', 'true', 'yes', 'on'):
        return True
    elif value_str in ('0', 'false', 'no', 'off'):
        return False
    else:
        # If it's an unexpected string, still try bool() fallback
        return bool(value_str)

def _to_timestamp(dt_str):
    if not dt_str:
        return None
    try:
        return int(datetime.fromisoformat(dt_str).timestamp() * 1000)
    except ValueError:
        return None

def safe_serialize(obj):
    try:
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        elif isinstance(obj, list):
            return [safe_serialize(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: safe_serialize(v) for k, v in obj.items()}
        elif hasattr(obj, "dict"):
            return safe_serialize(obj.dict())
        elif hasattr(obj, "export"):
            return safe_serialize(obj.export())
        elif hasattr(obj, "__dict__"):
            return safe_serialize(vars(obj))
        return str(obj)
    except Exception as e:
        return f"[Unserializable: {e}]"

def to_json_fallback(resp):
    """Safely converts object/response into JSON-serializable object or string."""
    try:
        if isinstance(resp, (str, int, float, bool, type(None))):
            return resp
        if hasattr(resp, "model_dump"):
            return resp.model_dump()
        if hasattr(resp, "dict"):
            return resp.dict()
        if isinstance(resp, (dict, list)):
            return resp
        
        # Fallback for other objects
        return str(resp)
    except Exception as e:
        return {"error": str(e), "output": str(resp)}

def _get_prefix_and_index(value_type: str):
    """Return the appropriate prefix and index counter name for a type."""
    if value_type == "string":
        return "cvs", "string"
    elif value_type in ("int", "float"):
        return "cvn", "number"
    elif value_type == "bool":
        return "cvb", "bool"
    else:
        return "cvs", "string"

def _get_type_key(value):
    """Map Python types to category keys."""
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int) and not isinstance(value, bool):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "string"
    else:
        return "string"

def to_str_or_none(val):
    """Convert value into string or JSON string if list/dict."""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    return str(val)

def assign(variables, variable, var_value):
    """Safely assign variable values with JSON handling."""
    if var_value is None:
        variables[variable] = None
        return

    # If the value is already an int or float
    if isinstance(var_value, (int, float)):
        variables[variable] = var_value
        return

    # If the value is a dict or list, store as JSON
    if isinstance(var_value, (dict, list)):
        variables[variable] = json.dumps(var_value)
        return

    # If it's a string, handle possible JSON or numeric content
    if isinstance(var_value, str):
        var_value = var_value.strip()

        # Try to parse as JSON if it looks like JSON
        if var_value.startswith(('{', '[')):
            try:
                parsed = json.loads(var_value)
                variables[variable] = json.dumps(parsed)
                return
            except json.JSONDecodeError:
                pass

        # Try to interpret numeric strings (integers or floats)
        try:
            if '.' in var_value:
                variables[variable] = float(var_value)
            else:
                variables[variable] = int(var_value)
            return
        except ValueError:
            pass

        # Default: store as plain string
        variables[variable] = var_value
        return

    # Fallback: store raw value
    variables[variable] = var_value

def reassign(data, key_to_cvs, global_starting_indices, starting_index=None):
    """
    Maps dictionary keys to unique 'cvs' variable names and returns a new dict.
    Lists and dicts are STRINGIFIED before sending.
    """
    cvs_vars = {}

    if isinstance(data, str):
        data = json.loads(data)

    if not isinstance(data, dict):
        raise ValueError("Input must be a dict or JSON string representing a dict")

    indices = starting_index if starting_index is not None else global_starting_indices.copy()

    for key, value in data.items():
        value_type = _get_type_key(value)
        prefix, index_key = _get_prefix_and_index(value_type)

        if key not in key_to_cvs:
            key_to_cvs[key] = f"{prefix}{indices[index_key]}"
            indices[index_key] += 1

        cvs_var = key_to_cvs[key]

        # ✅ Stringify lists/dicts to ensure they are JSON strings in body
        if isinstance(value, (dict, list)):
            cvs_vars[cvs_var] = json.dumps(value)
        elif isinstance(value, (bool, int, float)) or value is None:
            cvs_vars[cvs_var] = value
        else:
            cvs_vars[cvs_var] = str(value)

    return cvs_vars
