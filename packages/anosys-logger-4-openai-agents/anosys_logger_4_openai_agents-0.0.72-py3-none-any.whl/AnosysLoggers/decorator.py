from functools import wraps
import os
import inspect
import sys, io, json, requests
import asyncio
import traceback
from .utils import to_json_fallback, reassign, to_str_or_none, assign

# --- Global config ---
log_api_url = "https://www.anosys.ai"

# Separate index tracking for each type
global_starting_indices = {
    "string": 100,
    "number": 3,
    "bool": 1
}

# Known key mappings
key_to_cvs = {
    "custom_mapping":"otel_schema_url",
    "input": "cvs1",
    "output": "cvs2",
    "caller": "cvs4",
    "source": "cvs200"
}

# --- Decorator and raw logger ---
def anosys_logger(source=None):
    """Decorator to log function input/output to Anosys API,
       including who called the function.
       Supports sync, async, and async generator (streaming) functions.
    """
    def decorator(func):
        if inspect.isasyncgenfunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async for item in _handle_logging_async_gen(func, args, kwargs, source):
                    yield item
            return wrapper
        elif asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await _handle_logging_async(func, args, kwargs, source)
            return wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return _handle_logging_sync(func, args, kwargs, source)
            return wrapper
    return decorator

def _get_caller_info():
    stack = inspect.stack()
    if len(stack) > 3:
        caller_frame = stack[3]
        return {
            "function": caller_frame.function,
            "file": caller_frame.filename,
            "line": caller_frame.lineno,
        }
    return {"function": "unknown", "file": "unknown", "line": 0}

def _log_payload(source, args, output, error_info, caller_info):
    global key_to_cvs
    variables = {}
    
    print(f"[ANOSYS] Logger (source={source}) "
          f"called from {caller_info['function']} "
          f"at {caller_info['file']}:{caller_info['line']}")

    if error_info:
        print(f"[ANOSYS] Error occurred: {error_info['message']}")
    else:
        # Truncate output for console log if too long
        out_str = str(output)
        if len(out_str) > 200:
            out_str = out_str[:200] + "..."
        print(f"[ANOSYS] Captured output: {out_str}")
            
    print(f"[ANOSYS] Captured caller: {caller_info}")

    # === prepare payload ===
    input_array = [to_str_or_none(arg) for arg in args]
    assign(variables, "source", to_str_or_none(source))
    assign(variables, 'custom_mapping', json.dumps(key_to_cvs, indent=4))
    assign(variables, "input", input_array)
    
    if error_info:
            assign(variables, "error", True)
            assign(variables, "error_type", error_info["type"])
            assign(variables, "error_message", error_info["message"])
            assign(variables, "error_stack", error_info["stack"])
            assign(variables, "output", None)
    else:
            assign(variables, "output", to_json_fallback(output))
            
    assign(variables, "caller", caller_info)  # now structured dict

    # === send log ===
    try:
        response = requests.post(log_api_url, json=reassign(variables, key_to_cvs, global_starting_indices), timeout=5)
        response.raise_for_status()
        print(f"[ANOSYS] Mapper: {key_to_cvs}")
    except Exception as e:
        print(f"[ANOSYS]❌ POST failed: {e}")
        # print(f"[ANOSYS]❌ Data: {json.dumps(variables, indent=2)}")


def _handle_logging_sync(func, args, kwargs, source):
    caller_info = _get_caller_info()
    
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    text = None
    error_info = None

    try:
        text = func(*args, **kwargs)
    except Exception as e:
        error_info = {
            "type": type(e).__name__,
            "message": str(e),
            "stack": traceback.format_exc()
        }
        raise e
    finally:
        printed_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        output = text if text else printed_output.strip()
        
        _log_payload(source, args, output, error_info, caller_info)

    return text

async def _handle_logging_async(func, args, kwargs, source):
    caller_info = _get_caller_info()
    
    text = None
    error_info = None

    try:
        text = await func(*args, **kwargs)
    except Exception as e:
        error_info = {
            "type": type(e).__name__,
            "message": str(e),
            "stack": traceback.format_exc()
        }
        raise e
    finally:
        output = text
        _log_payload(source, args, output, error_info, caller_info)

    return text

async def _handle_logging_async_gen(func, args, kwargs, source):
    caller_info = _get_caller_info()
    
    aggregated_output = []
    error_info = None

    try:
        async for item in func(*args, **kwargs):
            aggregated_output.append(item)
            yield item
    except Exception as e:
        error_info = {
            "type": type(e).__name__,
            "message": str(e),
            "stack": traceback.format_exc()
        }
        raise e
    finally:
        # Try to join if all strings, otherwise keep as list
        if all(isinstance(x, str) for x in aggregated_output):
            output = "".join(aggregated_output)
        else:
            output = aggregated_output
            
        _log_payload(source, args, output, error_info, caller_info)

def anosys_raw_logger(data=None):
    """Directly logs raw data dict/json to Anosys API (dicts/lists are stringified)."""
    global key_to_cvs
    if data is None:
        data = {}
    try:
        mapped_data = reassign(data, key_to_cvs, global_starting_indices)
        response = requests.post(log_api_url, json=mapped_data, timeout=5)
        response.raise_for_status()
        print(f"[ANOSYS] Logger: {data} Logged successfully.")
        print(f"[ANOSYS] Mapper: {key_to_cvs}")
        return response
    except Exception as err:
        print(f"[ANOSYS]❌ POST failed: {err}")
        return None


def setup_decorator(path=None, starting_indices=None):
    """
    Setup logging decorator:
    - path: override Anosys API URL
    - starting_indices: dict of starting indices per type
    """
    global log_api_url, global_starting_indices

    if starting_indices:
        global_starting_indices.update(starting_indices)

    if path:
        log_api_url = path
        return

    api_key = os.getenv("ANOSYS_API_KEY")
    if api_key:
        try:
            response = requests.get(
                f"https://api.anosys.ai/api/resolveapikeys?apikey={api_key}",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            log_api_url = data.get("url", "https://www.anosys.ai")
        except requests.RequestException as e:
            print(f"[ERROR]❌ Failed to resolve API key: {e}")
    else:
        print("[ERROR]‼️ ANOSYS_API_KEY not found. Please obtain your API key from "
              "https://console.anosys.ai/collect/integrationoptions")
