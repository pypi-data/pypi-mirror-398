---
name: incident-response
description: IT incident response and management procedures
---

# Incident Response Procedures

## Objective

Guide structured incident response for IT support issues with proper escalation and communication.

## Incident Severity Levels

### Critical (P1)
- Production system down
- Security breach in progress
- Data loss occurring
- Multiple customers affected

**Response**: Immediate, all-hands
**SLA**: 1 hour resolution or escalation

### High (P2)
- Major feature broken
- Significant performance degradation
- Customer-facing issues
- Workaround not available

**Response**: Priority handling
**SLA**: 4 hours resolution

### Medium (P3)
- Non-critical feature broken
- Performance issues with workaround
- Internal tools affected

**Response**: Normal queue
**SLA**: 24 hours resolution

### Low (P4)
- Minor issues
- Enhancement requests
- Questions

**Response**: Best effort
**SLA**: 72 hours response

## Response Workflow

### 1. Triage (First 5 minutes)
- Acknowledge receipt
- Classify severity
- Assign to appropriate specialist
- Notify stakeholders if P1/P2

### 2. Investigation (Severity-dependent)
- Gather initial information
- Reproduce if possible
- Identify impacted systems
- Document timeline

### 3. Resolution
- Implement fix or workaround
- Test in safe environment
- Deploy with change control
- Verify resolution

### 4. Post-Incident
- Document root cause
- Update knowledge base
- Schedule post-mortem (P1/P2)
- Implement prevention measures

## Communication Templates

### Initial Response
```
Incident #{ID} acknowledged.
Severity: {LEVEL}
Assigned to: {SPECIALIST}
ETA for update: {TIME}
```

### Status Update
```
Incident #{ID} Update
Status: {Investigating/In Progress/Resolved}
Current action: {DESCRIPTION}
Next update: {TIME}
```

### Resolution
```
Incident #{ID} Resolved
Root cause: {DESCRIPTION}
Resolution: {DESCRIPTION}
Prevention: {RECOMMENDATIONS}
```

## Escalation Matrix

| Severity | First Response | Escalate After | Escalate To |
|----------|---------------|----------------|-------------|
| P1 | Immediate | 15 minutes | On-call manager |
| P2 | 15 minutes | 1 hour | Team lead |
| P3 | 1 hour | 4 hours | Senior engineer |
| P4 | 4 hours | 24 hours | Team lead |

## Knowledge Base Integration

After resolution:
1. Search for existing KB article
2. Update if found, create if not
3. Tag with relevant keywords
4. Link to incident ticket
