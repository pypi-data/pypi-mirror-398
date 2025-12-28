# AWS Security Lake Integration

## Overview

AWS Security Lake uses OCSF natively. Lokryn logs can be exported directly to Security Lake using the OCSF mapping.

**Standard Used:** OCSF v1.3.0
**Reference:** https://docs.aws.amazon.com/security-lake/

## Integration

### Prerequisites

1. AWS Security Lake enabled in your AWS account
2. S3 bucket configured for Security Lake ingestion
3. IAM role with write permissions to the Security Lake bucket

### Export Process

1. Transform Lokryn logs to OCSF format using `../standards/ocsf/` mappings
2. Write to S3 in Parquet format (Security Lake native format)
3. Security Lake automatically ingests from configured sources

### Schema Considerations

- Use `ocsf_class_uid` and `ocsf_activity_id` fields directly (pre-translated)
- Ensure timestamps are in ISO 8601 format
- Wrap single enum values in arrays where OCSF expects arrays

## Example Export

See `export_example.py` for a Python implementation.

## Custom Source Registration

For AI/Agent events (EVENT_TOOL_INVOCATION, EVENT_MODEL_INFERENCE, etc.), you may need to register a custom source in Security Lake since these map to OCSF API Activity (class_uid 6003).

```bash
aws securitylake create-custom-log-source \
    --source-name "lokryn-compliance-log" \
    --source-version "1.0" \
    --event-classes "6003" \
    --configuration ...
```
