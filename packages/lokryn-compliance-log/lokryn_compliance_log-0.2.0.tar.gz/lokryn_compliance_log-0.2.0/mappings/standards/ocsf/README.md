# OCSF (Open Cybersecurity Schema Framework) Mapping

## Overview

Maps Lokryn compliance log schema to OCSF v1.3.0.

**Target Version:** 1.3.0
**Reference:** https://schema.ocsf.io/

## Design Principles

- Lokryn fields are canonical
- OCSF values are pre-translated and stored at write time (`ocsf_class_uid`, `ocsf_activity_id`)
- Export is field rename only - no runtime transformation required

## Key Mappings

### Severity
Lokryn severity values 1-8 align exactly with OCSF `severity_id`.

### Outcome
Lokryn uses granular failure types. Export rule:
- `OUTCOME_SUCCESS` → OCSF `status_id: 1`
- `OUTCOME_FAILURE_*` (prefix match) → OCSF `status_id: 2`
- `OUTCOME_OTHER` → OCSF `status_id: 99`

### Sensitivity
Lokryn sensitivity values 0-4 align exactly with OCSF `confidentiality_id`.
- `SENSITIVITY_PUBLIC_INTERNAL` (10) → OCSF `confidentiality_id: 1` (via prefix rule)

## Files

- `field_mapping.json` - Lokryn field → OCSF field mappings
- `event_type_mapping.json` - EventType → class_uid/activity_id mappings
- `examples/` - Side-by-side JSON examples

## Usage with AWS Security Lake

AWS Security Lake uses OCSF natively. See `../platforms/aws-security-lake/` for specific integration details.

## Usage with Google Chronicle

Google Chronicle supports OCSF ingestion. See `../platforms/google-chronicle/` for specific integration details.
