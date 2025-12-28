# Splunk Integration

## Overview

Splunk uses CIM (Common Information Model) for data normalization.

**Standard Used:** CIM v6.1
**Reference:** https://docs.splunk.com/Documentation/CIM

## Integration

### Source Type Configuration

Create a custom source type for Lokryn logs:

```ini
# props.conf
[lokryn:compliance:log]
SHOULD_LINEMERGE = false
TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%3NZ
TIME_PREFIX = "time":"
MAX_TIMESTAMP_LOOKAHEAD = 30
TRUNCATE = 0
KV_MODE = json
```

### Field Extractions

```ini
# transforms.conf
[lokryn_severity]
REGEX = "severity":(\d+)
FORMAT = severity::$1

[lokryn_user]
REGEX = "actor_id":"([^"]+)"
FORMAT = user::$1
```

### Tags for CIM Compliance

```ini
# tags.conf
[eventtype=lokryn_authentication]
authentication = enabled

[eventtype=lokryn_change]
change = enabled
audit = enabled
```

### Event Types

```ini
# eventtypes.conf
[lokryn_authentication]
search = sourcetype="lokryn:compliance:log" (event_type=1 OR event_type=2)

[lokryn_change]
search = sourcetype="lokryn:compliance:log" (event_type=4 OR event_type=6 OR event_type=11)
```

## Files

- `props_transforms.conf` - Combined Splunk configuration
- See `../standards/splunk-cim/` for field mappings
