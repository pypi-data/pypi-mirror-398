from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor, 
    BatchSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from traceai_openai_agents import OpenAIAgentsInstrumentor
import threading
import json
import os
import logging
from datetime import datetime
import requests
from .utils import get_env_bool, _to_timestamp, to_str_or_none, assign, reassign

# Set up logging
logger = logging.getLogger(__name__)

# Prevent re-initialization
_lock = threading.Lock()
log_api_url = "https://www.anosys.ai"

# Separate index tracking for each type
global_starting_indices = {
    "string": 100,
    "number": 3,
    "bool": 1
}

key_to_cvs = {
    # --- Core / Internal ---
    "otel_record_type": "otel_record_type",  # Internal record type identifier
    "custom_mapping": "otel_schema_url",     # Custom mapping configuration
    "otel_observed_timestamp": "otel_observed_timestamp", # Timestamp when the event was observed
    "cvn1": "cvn1",                          # Custom numeric value 1 (start timestamp)
    "cvn2": "cvn2",                          # Custom numeric value 2 (end timestamp)
    "otel_resource": "otel_resource",        # Resource attributes
    "name": "otel_name",                     # Span name
    "trace_id": "otel_trace_id",             # Trace ID
    "span_id": "otel_span_id",               # Span ID
    "trace_state": "otel_trace_flags",       # Trace state/flags
    "parent_id": "otel_parent_span_id",      # Parent span ID
    "start_time": "otel_start_time",         # Start time of the span
    "end_time": "otel_end_time",             # End time of the span
    "kind": "otel_kind",                     # Span kind (CLIENT, SERVER, etc.)
    "resp_id": "otel_status_message",        # Response ID (mapped to status message)
    "otel_duration_ms": "otel_duration_ms",  # Duration in milliseconds
    "raw": "cvs199",                         # Raw data dump (debug)
    "from_source": "cvs200",                 # Source of the telemetry (e.g., openAI_Agents_Telemetry)

    # --- Legacy / Backward Compatibility ---
    "llm_tools": "llm_tools",                # Tools available to the LLM
    "llm_system": "llm_system",              # System prompt/instructions
    "llm_token_count": "llm_token_count",    # Token usage count
    "llm_model": "llm_model",                # Model name
    "llm_input": "llm_input",                # Input text/value
    "llm_output": "llm_output",              # Output text/value
    "llm_invocation_parameters": "llm_invocation_parameters", # Parameters used for invocation
    "llm_input_messages": "cvs1",            # Input messages (mapped to cvs1)
    "llm_output_messages": "cvs2",           # Output messages (mapped to cvs2)

    # --- General & System ---
    "gen_ai.system": "gen_ai_system",               # The vendor/system name (e.g., openai, anthropic)
    "gen_ai.provider.name": "gen_ai_provider_name", # The name of the provider (e.g., openai, aws.bedrock)
    "gen_ai.operation.name": "gen_ai_operation_name", # The operation name (e.g., chat, generate_content)
    "server.address": "server_address",             # Server address (e.g., api.openai.com)
    "server.port": "server_port",                   # Server port (e.g., 443)
    "error.type": "error_type",                     # Error type/code (e.g., timeout, rate_limit_exceeded)

    # --- Request Configuration (LLM) ---
    "gen_ai.request.model": "gen_ai_request_model", # The name of the model requested (e.g., gpt-4)
    "gen_ai.request.temperature": "gen_ai_request_temperature", # Randomness setting (0.0 - 2.0)
    "gen_ai.request.top_p": "gen_ai_request_top_p", # Nucleus sampling probability
    "gen_ai.request.top_k": "gen_ai_request_top_k", # Top-k sampling count
    "gen_ai.request.max_tokens": "gen_ai_request_max_tokens", # Maximum tokens allowed
    "gen_ai.request.frequency_penalty": "gen_ai_request_frequency_penalty", # Penalty for frequent tokens
    "gen_ai.request.presence_penalty": "gen_ai_request_presence_penalty", # Penalty for existing tokens
    "gen_ai.request.stop_sequences": "gen_ai_request_stop_sequences", # List of sequences to stop generation
    "gen_ai.request.seed": "gen_ai_request_seed",   # Random seed for reproducibility
    "gen_ai.request.choice.count": "gen_ai_request_choice_count", # Number of completion choices requested
    "gen_ai.request.encoding_formats": "gen_ai_request_encoding_formats", # Requested encoding formats (e.g., base64)

    # --- Response & Usage (LLM) ---
    "gen_ai.response.model": "gen_ai_response_model", # The name of the model that actually served the response
    "gen_ai.response.id": "gen_ai_response_id",       # Unique identifier for the response
    "gen_ai.response.finish_reasons": "gen_ai_response_finish_reasons", # List of reasons why generation stopped
    "gen_ai.usage.input_tokens": "gen_ai_usage_input_tokens",   # Number of prompt tokens used
    "gen_ai.usage.output_tokens": "gen_ai_usage_output_tokens", # Number of completion tokens used
    "gen_ai.usage.total_tokens": "gen_ai_usage_total_tokens",   # Total tokens used (input + output)
    "gen_ai.output.type": "gen_ai_output_type",       # Type of output (e.g., text, json, image)

    # --- Content & Messages (Opt-In) ---
    "gen_ai.input.messages": "gen_ai_input_messages", # Full input messages (JSON)
    "gen_ai.output.messages": "gen_ai_output_messages", # Full output messages (JSON)
    "gen_ai.system_instructions": "gen_ai_system_instructions", # System instructions/prompt
    "gen_ai.tool.definitions": "gen_ai_tool_definitions", # Definitions of tools provided to the model

    # --- Agents & Frameworks ---
    "gen_ai.agent.id": "gen_ai_agent_id",             # Unique identifier of the agent
    "gen_ai.agent.name": "gen_ai_agent_name",         # Human-readable name of the agent
    "gen_ai.agent.description": "gen_ai_agent_description", # Description of the agent's purpose
    # "gen_ai.agent.version": "gen_ai_agent_version",   # Agent version
    # "gen_ai.agent.type": "gen_ai_agent_type",         # Agent type (autonomous/collaborative/reactive)
    "gen_ai.conversation.id": "gen_ai_conversation_id", # Unique identifier for the conversation thread
    "gen_ai.data_source.id": "gen_ai_data_source_id", # Identifier for a data source used by the agent

    # # --- Agentic Tasks ---
    # "gen_ai.task.id": "gen_ai_task_id",               # Unique task instance identifier
    # "gen_ai.task.name": "gen_ai_task_name",           # Human-readable task name
    # "gen_ai.task.parent.id": "gen_ai_task_parent_id", # Parent task ID for subtasks
    # "gen_ai.task.code.id": "gen_ai_task_code_id",     # Task type/template identifier
    # "gen_ai.task.code.vendor": "gen_ai_task_code_vendor", # Framework vendor (e.g., crewai, langgraph)
    # "gen_ai.task.kind": "gen_ai_task_kind",           # Task kind (standalone/subtask/parallel)
    # "gen_ai.task.tags": "gen_ai_task_tags",           # Task tags for categorization
    # "gen_ai.task.description": "gen_ai_task_description", # Task description/objective
    # "gen_ai.task.status": "gen_ai_task_status",       # Task status (pending/running/completed/failed)
    # "gen_ai.task.input": "gen_ai_task_input",         # Task input data
    # "gen_ai.task.output": "gen_ai_task_output",       # Task output data

    # # --- Agentic Actions ---
    # "gen_ai.action.id": "gen_ai_action_id",           # Unique action identifier
    # "gen_ai.action.name": "gen_ai_action_name",       # Action name
    # "gen_ai.action.type": "gen_ai_action_type",       # Action type (llm_call/tool_call/api_request/db_query)
    # "gen_ai.action.task.id": "gen_ai_action_task_id", # Associated task ID
    # "gen_ai.action.tool.name": "gen_ai_action_tool_name", # Tool name if action is tool call
    # "gen_ai.action.tool.parameters": "gen_ai_action_tool_parameters", # Tool parameters
    # "gen_ai.action.input": "gen_ai_action_input",     # Action input
    # "gen_ai.action.output": "gen_ai_action_output",   # Action output
    # "gen_ai.action.status": "gen_ai_action_status",   # Action status

    # # --- Agentic Teams ---
    # "gen_ai.team.id": "gen_ai_team_id",               # Team identifier
    # "gen_ai.team.name": "gen_ai_team_name",           # Team name
    # "gen_ai.team.description": "gen_ai_team_description", # Team description
    # "gen_ai.team.agents": "gen_ai_team_agents",       # List of agent IDs in team (JSON array)
    # "gen_ai.team.orchestration": "gen_ai_team_orchestration", # Orchestration pattern (sequential/parallel/hierarchical)

    # # --- Agentic Artifacts ---
    # "gen_ai.artifact.id": "gen_ai_artifact_id",       # Artifact identifier
    # "gen_ai.artifact.type": "gen_ai_artifact_type",   # Artifact type (prompt/embedding/document/image/code)
    # "gen_ai.artifact.format": "gen_ai_artifact_format", # Artifact format (json/text/binary)
    # "gen_ai.artifact.size": "gen_ai_artifact_size",   # Artifact size in bytes
    # "gen_ai.artifact.uri": "gen_ai_artifact_uri",     # Artifact storage URI
    # "gen_ai.artifact.metadata": "gen_ai_artifact_metadata", # Artifact metadata (JSON)

    # # --- Agentic Memory ---
    # "gen_ai.memory.id": "gen_ai_memory_id",           # Memory store identifier
    # "gen_ai.memory.scope": "gen_ai_memory_scope",     # Memory scope (session/agent/task/global)
    # "gen_ai.memory.type": "gen_ai_memory_type",       # Memory type (short_term/long_term/working)
    # "gen_ai.memory.operation": "gen_ai_memory_operation", # Memory operation (read/write/update/delete)
    # "gen_ai.memory.key": "gen_ai_memory_key",         # Memory key/identifier
    # "gen_ai.memory.value": "gen_ai_memory_value",     # Memory value (JSON)

    # --- Embeddings Specific ---
    "gen_ai.embeddings.dimension.count": "gen_ai_embeddings_dimension_count", # The vector dimension size
}

def set_nested(obj, path, value):
    parts = path.split(".")
    current = obj
    for i, part in enumerate(parts[:-1]):
        try:
            idx = int(part)
            if not isinstance(current, list):
                current_parent = current
                current = []
                if isinstance(current_parent, dict):
                    current_parent[parts[i - 1]] = current
            while len(current) <= idx:
                current.append({})
            current = current[idx]
        except ValueError:
            if part not in current or not isinstance(current[part], (dict, list)):
                current[part] = {}
            current = current[part]
    final_key = parts[-1]
    try:
        final_key = int(final_key)
        if not isinstance(current, list):
            current_parent = current
            current = []
            if isinstance(current_parent, dict):
                current_parent[parts[-2]] = current
        while len(current) <= final_key:
            current.append(None)
    except ValueError:
        pass
    if isinstance(value, str) and value.strip().startswith(("{", "[")):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
    if isinstance(final_key, int):
        current[final_key] = value
    else:
        current[final_key] = value


def deserialize_attributes(attributes):
    new_attrs = {}
    for key, value in attributes.items():
        set_nested(new_attrs, key, value)
    return new_attrs

def span_to_dict(span: ReadableSpan) -> dict:
    return {
        "name": span.name,
        "context": {
            "trace_id": format(span.context.trace_id, "032x"),
            "span_id": format(span.context.span_id, "016x"),
            "trace_flags": int(span.context.trace_flags),
        },
        "parent_id": (
            format(span.parent.span_id, "016x")
            if span.parent else None
        ),
        "kind": span.kind.name,
        "start_time_unix_nano": span.start_time,
        "end_time_unix_nano": span.end_time,
        "status": {
            "status_code": span.status.status_code.name,
            "description": span.status.description,
        },
        "attributes": dict(span.attributes),
        "attributes_json": deserialize_attributes(dict(span.attributes)),
        "events": [
            {
                "name": event.name,
                "timestamp": event.timestamp,
                "attributes": dict(event.attributes),
            }
            for event in span.events
        ],
        "links": [
            {
                "context": {
                    "trace_id": format(link.context.trace_id, "032x"),
                    "span_id": format(link.context.span_id, "016x"),
                },
                "attributes": dict(link.attributes),
            }
            for link in span.links
        ],
        "resource": dict(span.resource.attributes),
        "instrumentation_scope": {
            "name": span.instrumentation_scope.name,
            "version": span.instrumentation_scope.version,
        },
    }

def extract_span_info(span: ReadableSpan):
    variables = {}

    # OTel uses nanoseconds for start_time/end_time
    # We need milliseconds for backend
    start_ts_ms = span.start_time // 1_000_000 if span.start_time else None
    end_ts_ms = span.end_time // 1_000_000 if span.end_time else None
    
    # Top-level keys
    assign(variables, 'otel_record_type', 'AnoSys Trace')
    assign(variables, 'custom_mapping', json.dumps(key_to_cvs, indent=4))
    
    # helper for hex ids
    trace_id_hex = trace.format_trace_id(span.context.trace_id) if span.context.trace_id else None
    span_id_hex = trace.format_span_id(span.context.span_id) if span.context.span_id else None
    parent_id_hex = trace.format_span_id(span.parent.span_id) if span.parent else None

    assign(variables, 'otel_observed_timestamp', datetime.utcnow().isoformat() + "Z")
    assign(variables, 'name', span.name)
    assign(variables, 'trace_id', trace_id_hex)
    assign(variables, 'span_id', span_id_hex)
    # trace_state is an object, typically we want repr or header string. Header string is best.
    assign(variables, 'trace_state', span.context.trace_state.to_header() if span.context.trace_state else None)
    assign(variables, 'parent_id', parent_id_hex)
    
    # Existing backend expects specific timestamp format or just values?
    # Original code used `to_str_or_none(span.get('start_time'))` which was ISO string from to_json()
    # But `cvn1` used `_to_timestamp`.
    # Let's keep `start_time` as ISO based on `start_ts_ms` for backward compat if needed,
    # or just use the ints if that matches `utils.to_str_or_none`. 
    # Original `start_time` provided by `to_json` is ISO string. 
    # Let's convert ms timestamp to ISO string for 'start_time' / 'end_time' keys to match original behavior.
    
    if start_ts_ms:
        variables['start_time'] = datetime.utcfromtimestamp(start_ts_ms / 1000.0).isoformat() + "Z"
    else:
        variables['start_time'] = None

    assign(variables, 'cvn1', start_ts_ms)
    
    if end_ts_ms:
        variables['end_time'] = datetime.utcfromtimestamp(end_ts_ms / 1000.0).isoformat() + "Z"
    else:
        variables['end_time'] = None
        
    assign(variables, 'cvn2', end_ts_ms)
    
    if start_ts_ms is not None and end_ts_ms is not None:
        assign(variables, 'otel_duration_ms', end_ts_ms - start_ts_ms)
    else:
        assign(variables, 'otel_duration_ms', None)

    # Attributes - Direct Access
    # attributes is available as span.attributes (dict-like)
    attributes = span.attributes or {}
    attributes_json = deserialize_attributes(dict(span.attributes))
    print( attributes_json)

    # --- Legacy / Backward Compatibility ---
    assign(variables, 'llm_tools', to_str_or_none(attributes.get('llm.tools')))
    assign(variables, 'llm_token_count', to_str_or_none(attributes.get('llm.token_count')))
    # Nested dictionaries in attributes were flattened in OTel attributes usually, e.g., 'llm.tools'.
    # Original code: attributes.get('llm', {}).get('tools') suggests nested structure in the JSON export,
    # but in actual OTel Span object, attributes are typically flat keys like 'llm.model_name'.
    # Standard OTel format for nested structures is dot-notation keys.
    # HOWEVER, the 'agents' library might be setting them as complex dict/string values?
    # Assuming standard OTel conventions where possible, but if 'agents' library puts a dict in specific key, we handle that.
    # Looking at original code: `attributes.get('llm', {}).get('tools')`
    # This implies `attributes` dictionary had a key "llm" which was a dict.
    # This happens when `span.to_json()` is called -> it structures it? 
    # Actually, OTel `to_json()` does NOT nest attributes by dots. It keeps keys as is.
    # So if original code worked, `attributes` MUST have had a key "llm" which was a Dictionary.
    # This is non-standard for OTel (attributes values are int/float/bool/str/arrays). They shouldn't be Dicts.
    # IF the instrumentor is doing something weird, we need to be careful.
    # But usually, `llm.tools` is the key.
    # Let's check `traceai_openai_agents` instrumentor if we could... we don't have code for it.
    # BUT, if `span.to_json()` output had nested objects, it means the Exporter was serializing it that way?
    # Wait, `span.to_json()` from opentelemetry-sdk DOES NOT NEST attributes.
    # It just outputs attributes as a dictionary.
    # IF the original code `attributes.get('llm', {})...` worked, it means the key "llm" existed and value was a dict.
    # Use `.get('llm.tools')` or similar if keys are dotted.
    # Let's try both for safety or check if we can assume dotted keys. 
    # Actually, if I look at `deserialize_attributes` in original code:
    # "set_nested(new_attrs, key, value)"
    # Ah! The original code called `deserialize_attributes` which manually unflattened "llm.tools" into "llm": {"tools": ...}
    # So the RAW attributes are flat: "llm.tools".
    # So I should access them as `attributes.get('llm.tools')`. Correct.
    
    assign(variables, 'llm_tools', to_str_or_none(attributes.get('llm.tools')))
    assign(variables, 'llm_token_count', to_str_or_none(attributes.get('llm.token_count')))
    
    # Note: 'llm.output_messages.output_messages' ... strange double nesting?
    # Original: attributes.get('llm', {}).get('output_messages', {}).get('output_messages')
    # Unflattened: llm -> output_messages -> output_messages
    # Flat key: "llm.output_messages.output_messages"
    assign(variables, 'llm_output_messages', to_str_or_none(attributes.get('llm.output_messages.output_messages')))
    assign(variables, 'llm_input_messages', to_str_or_none(attributes.get('llm.input_messages.input_messages')))
    assign(variables, 'llm_model', to_str_or_none(attributes.get('llm.model_name')))
    assign(variables, 'llm_invocation_parameters', to_str_or_none(attributes.get('llm.invocation_parameters')))
    assign(variables, 'llm_system', to_str_or_none(attributes.get('llm.system')))
    assign(variables, 'llm_input', to_str_or_none(attributes.get('input.value')))
    assign(variables, 'llm_output', to_str_or_none(attributes.get('output.value')))
    
    # Kind
    # Original: attributes.get('fi', {}).get('span', {}).get('kind') - this looks like specific instrumentation artifact?
    # Or maybe it was `span.kind` transformed? 
    # Let's just use span.kind from the object.
    assign(variables, 'kind', str(span.kind).replace('SpanKind.', '').upper()) # CLIENT, SERVER, INTERNAL...
    
    # Resource
    # span.resource.attributes is a bounded attributes dict
    assign(variables, 'otel_resource', json.dumps(span.resource.attributes, default=str))
    assign(variables, 'from_source', "openAI_Agents_Telemetry")

    # --- Gen AI Semantic Conventions ---
    
    # General & System
    assign(variables, 'gen_ai.system', to_str_or_none(attributes.get('gen_ai.system') or "openai"))
    assign(variables, 'gen_ai.provider.name', to_str_or_none(attributes.get('gen_ai.provider.name')))
    assign(variables, 'gen_ai.operation.name', to_str_or_none(attributes.get('gen_ai.operation.name')))
    assign(variables, 'server.address', to_str_or_none(attributes.get('server.address')))
    assign(variables, 'server.port', attributes.get('server.port'))
    assign(variables, 'error.type', to_str_or_none(attributes.get('error.type')))

    # Request Configuration
    assign(variables, 'gen_ai.request.model', to_str_or_none(attributes.get('gen_ai.request.model') or attributes.get('llm.model_name')))
    assign(variables, 'gen_ai.request.temperature', attributes.get('gen_ai.request.temperature'))
    assign(variables, 'gen_ai.request.top_p', attributes.get('gen_ai.request.top_p'))
    assign(variables, 'gen_ai.request.top_k', attributes.get('gen_ai.request.top_k'))
    assign(variables, 'gen_ai.request.max_tokens', attributes.get('gen_ai.request.max_tokens'))
    assign(variables, 'gen_ai.request.frequency_penalty', attributes.get('gen_ai.request.frequency_penalty'))
    assign(variables, 'gen_ai.request.presence_penalty', attributes.get('gen_ai.request.presence_penalty'))
    assign(variables, 'gen_ai.request.stop_sequences', to_str_or_none(attributes.get('gen_ai.request.stop_sequences')))
    assign(variables, 'gen_ai.request.seed', attributes.get('gen_ai.request.seed'))
    assign(variables, 'gen_ai.request.choice.count', attributes.get('gen_ai.request.choice.count'))
    assign(variables, 'gen_ai.request.encoding_formats', to_str_or_none(attributes.get('gen_ai.request.encoding_formats')))

    # Response & Usage
    assign(variables, 'gen_ai.response.model', to_str_or_none(attributes.get('gen_ai.response.model')))
    assign(variables, 'gen_ai.response.id', to_str_or_none(attributes.get('gen_ai.response.id')))
    assign(variables, 'gen_ai.response.finish_reasons', to_str_or_none(attributes.get('gen_ai.response.finish_reasons')))
    assign(variables, 'gen_ai.usage.input_tokens', attributes.get('gen_ai.usage.input_tokens'))
    assign(variables, 'gen_ai.usage.output_tokens', attributes.get('gen_ai.usage.output_tokens'))
    assign(variables, 'gen_ai.usage.total_tokens', attributes.get('gen_ai.usage.total_tokens'))
    assign(variables, 'gen_ai.output.type', to_str_or_none(attributes.get('gen_ai.output.type')))

    # Content & Messages
    assign(variables, 'gen_ai.input.messages', to_str_or_none(attributes.get('gen_ai.input.messages')))
    assign(variables, 'gen_ai.output.messages', to_str_or_none(attributes.get('gen_ai.output.messages')))
    assign(variables, 'gen_ai.system_instructions', to_str_or_none(attributes.get('gen_ai.system_instructions')))
    assign(variables, 'gen_ai.tool.definitions', to_str_or_none(attributes.get('gen_ai.tool.definitions')))

    # Agents & Frameworks
    assign(variables, 'gen_ai.agent.id', to_str_or_none(attributes.get('gen_ai.agent.id')))
    assign(variables, 'gen_ai.agent.name', to_str_or_none(attributes.get('gen_ai.agent.name')))
    assign(variables, 'gen_ai.agent.description', to_str_or_none(attributes.get('gen_ai.agent.description')))
    
    assign(variables, 'gen_ai.conversation.id', to_str_or_none(attributes.get('gen_ai.conversation.id')))
    assign(variables, 'gen_ai.data_source.id', to_str_or_none(attributes.get('gen_ai.data_source.id')))

    # Embeddings
    assign(variables, 'gen_ai.embeddings.dimension.count', attributes.get('gen_ai.embeddings.dimension.count'))


    # Handling dict/list/string cases for Output -> ID 
    # Original logic examined attributes.get('output') which was presumably a dict from the JSON
    # Now it's flattened: 'output.value.id' maybe? 
    # BUT, 'output' attribute might be a JSON STRING in OTel if it's complex.
    # OTel attributes don't support dicts as values. Only primitives and arrays of primitives.
    # So if "output" contains an ID, it's either in a flat key "output.id" or the value of "output" key is a JSON string.
    # The original code `extract_span_info` logic:
    # output_attr = attributes.get('output') -> if dict...
    # This strongly suggests standard extraction relies on unflattened dicts.
    # Since I'm using flat attributes now:
    # 1. Check if 'output.value' exists (flat key).
    # 2. Check if 'output' exists and is a JSON string.
    
    response_id = None
    # Strategy: Try specific flat keys first
    
    # Original: output -> value -> id
    # Flat equivalent: output.value.id (if flattened)
    # OR: output.value is a string that is JSON?
    
    # Safe bet: look for 'gen_ai.response.id' which is standard semconv (already handled above).
    # But for custom specific ones... 
    
    # Let's try to reconstruct the `val` from original logic
    # original: output_attr = attributes.get('output')
    # If attributes are flat, 'output' key might NOT exist if it was a parent of 'output.value'.
    # In 'deserialize_attributes', 'output.value' becomes output['value'].
    # So we should look for 'output.value.id' key? OR parse 'output.value' if it's a string?
    
    # Let's check 'output' key directly.
    output_val = attributes.get('output') # might be string
    
    # Let's also check 'output.value'
    # output_value_val = attributes.get('output.value') # might be string
    output_value_val = attributes.get('raw.output') # might be string

    if output_value_val and isinstance(output_value_val, str):
         # Try parsing if it looks like JSON
         if output_value_val.startswith('{'):
             try:
                 parsed = json.loads(output_value_val)
                 if isinstance(parsed, dict):
                     response_id = parsed.get('id')
             except:
                 pass

    assign(variables, 'resp_id', to_str_or_none(response_id))  # for link with agentsAI records
    
    # if (get_env_bool('ANOSYS_DEBUG_LOGS')):
    #     # Construct a debug dict since we don't have existing json
    #     debug_span = {
    #         "name": span.name,
    #         "context": {
    #             "trace_id": trace_id_hex,
    #             "span_id": span_id_hex,
    #         },
    #         "kind": str(span.kind),
    #         "start_time": span.start_time,
    #         "end_time": span.end_time,
    #         "attributes": dict(attributes),
    #         "resource": dict(span.resource.attributes)
    #     }
    #     assign(variables, "raw", json.dumps(debug_span, default=str))

    variables['raw'] = json.dumps(span_to_dict(span), default=str)
    return reassign(variables, key_to_cvs, global_starting_indices)

# Removed legacy helper functions: set_nested, deserialize_attributes
# clean_nulls is still used for the payload cleaning.

def clean_nulls(data):
    """Recursively remove None values AND empty containers."""
    if isinstance(data, dict):
        cleaned = {k: clean_nulls(v) for k, v in data.items() if v is not None}
        # remove keys whose cleaned contents are empty
        return {k: v for k, v in cleaned.items() if v not in ({}, [], None)}
    
    elif isinstance(data, list):
        cleaned = [clean_nulls(item) for item in data if item is not None]
        # remove empty results
        return [item for item in cleaned if item not in ({}, [], None)]
    
    return data


class AnosysHttpExporter(SpanExporter):
    def export(self, spans) -> SpanExportResult:
        for span in spans:
            try:
                # Direct extraction from ReadableSpan
                data = extract_span_info(span)
                
                span_source = data.get("from_source") or "unknown_source"
                span_name = data.get("otel_name") or data.get("name") or "unknown_name"
                logger.debug(f"[ANOSYS]📡 Exporting span from: {span_source} | Name: {span_name}")
                
                # ✅ Remove null values before sending
                cleaned_data = clean_nulls(data)
                
                response = requests.post(log_api_url, json=cleaned_data, timeout=5)
                response.raise_for_status()
                logger.info(f"[ANOSYS]✅ Successfully sent to backend: {span_source} | {span_name}")

            except requests.exceptions.HTTPError as e:
                logger.error(f"[ANOSYS]❌ HTTP Export failed ({e.response.status_code}): {e}")
                try:
                    logger.error(f"[ANOSYS]❌ Response: {e.response.text[:500]}")
                except Exception:
                    pass
                try:
                    logger.error(f"[ANOSYS]❌ Data: {json.dumps(data, indent=2)}")
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"[ANOSYS]❌ Export failed (Unexpected): {e}")

        return SpanExportResult.SUCCESS


def setup_tracing(api_url, use_batch_processor=False):
    """
    Initialize tracing for OpenAI and ALL other OpenTelemetry sources.

    Args:
        api_url (str): URL to post telemetry data.
        use_batch_processor (bool): If True, use BatchSpanProcessor; otherwise, SimpleSpanProcessor.
    """
    global log_api_url
    log_api_url = api_url

    with _lock:
        exporter = AnosysHttpExporter()
        if use_batch_processor:
            span_processor = BatchSpanProcessor(
                exporter,
                schedule_delay_millis=1000,
                max_queue_size=2048,
                max_export_batch_size=512
            )
            logger.info("[ANOSYS] Using BatchSpanProcessor for spans")
        else:
            span_processor = SimpleSpanProcessor(exporter)
            logger.info("[ANOSYS] Using SimpleSpanProcessor for spans")

        # Check existing Global Provider
        active_provider = trace.get_tracer_provider()
        trace_provider = None
        set_global = False

        if isinstance(active_provider, TracerProvider):
            logger.info("[ANOSYS] Detected existing global TracerProvider. Attaching processor.")
            trace_provider = active_provider
        else:
            logger.info("[ANOSYS] Creating new global TracerProvider.")
            trace_provider = TracerProvider()
            set_global = True

        # Attach Span Processor
        trace_provider.add_span_processor(span_processor)

        if set_global:
            trace.set_tracer_provider(trace_provider)

        # ✅ Instrument OpenAI
        instrumentor = OpenAIAgentsInstrumentor()
        try:
            if getattr(instrumentor, "_is_instrumented_by_opentelemetry", False):
                instrumentor.uninstrument()
        except Exception as e:
            logger.warning(f"[ANOSYS]⚠️ Uninstrument warning: {e}")

        instrumentor.instrument(tracer_provider=trace_provider)

        logger.info("[ANOSYS]✅ AnoSys Instrumented OpenAI and all OpenTelemetry traces")

        # ✅ Optional: Print active tracer info to confirm global registration
        active_provider_check = trace.get_tracer_provider()
        logger.debug(f"[ANOSYS] Active global tracer provider: {active_provider_check.__class__.__name__}")
