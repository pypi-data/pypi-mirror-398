# OTel GenAI Semantic Conventions Mapping

## Overview

Maps Lokryn compliance log schema to OpenTelemetry GenAI Semantic Conventions v1.37.0.

**Target Version:** 1.37.0
**Reference:** https://opentelemetry.io/docs/specs/semconv/gen-ai/

## Design Principles

- Lokryn fields are canonical
- OTel operation name is pre-translated and stored at write time (`otel_operation_name`)
- Export is field rename only - no runtime transformation required

## Key Mappings

### Operation Names

OTel GenAI defines specific operation names for different AI/ML activities:

| Lokryn EventType | OTel operation_name |
|------------------|---------------------|
| EVENT_TOOL_INVOCATION | `execute_tool` |
| EVENT_MODEL_INFERENCE | `chat` |
| EVENT_AGENT_DECISION | `invoke_agent` |
| EVENT_DELEGATION | `invoke_agent` |
| EVENT_CONTEXT_ACCESS | `embeddings` |
| EVENT_PROMPT_EXECUTION | `chat` |
| EVENT_MCP_INITIALIZE | `create_agent` |
| EVENT_MCP_INITIALIZED | `create_agent` |
| EVENT_SAMPLING_REQUEST | `chat` |
| EVENT_SAMPLING_RESPONSE | `chat` |

### GenAI Payload → OTel Attributes

| Lokryn Field | OTel Attribute |
|--------------|----------------|
| genai.model | gen_ai.request.model |
| genai.provider | gen_ai.system |
| genai.input_tokens | gen_ai.usage.input_tokens |
| genai.output_tokens | gen_ai.usage.output_tokens |
| genai.temperature | gen_ai.request.temperature |
| genai.max_tokens | gen_ai.request.max_tokens |
| genai.top_p | gen_ai.request.top_p |
| genai.finish_reason | gen_ai.response.finish_reasons |

## Files

- `field_mapping.json` - Lokryn field → OTel attribute mappings
- `event_type_mapping.json` - EventType → operation_name mappings
- `examples/` - Side-by-side JSON examples

## Usage with Datadog

Datadog LLM Observability supports OTel GenAI SemConv natively. See `../platforms/datadog/` for specific integration details.
