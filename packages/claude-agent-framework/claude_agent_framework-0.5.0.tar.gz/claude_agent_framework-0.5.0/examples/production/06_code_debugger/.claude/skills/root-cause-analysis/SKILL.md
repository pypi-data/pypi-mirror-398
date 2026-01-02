---
name: root-cause-analysis
description: Root cause analysis frameworks for debugging
---

# Root Cause Analysis Skill

## Objectives

Provide structured methodology for finding root causes:
- Move beyond symptoms to causes
- Identify systemic issues
- Prevent recurrence
- Document learnings

## RCA Frameworks

### 5 Whys Analysis
Ask "Why?" iteratively until root cause found:

| Level | Question | Example |
|-------|----------|---------|
| Why 1 | Why did it fail? | Test assertion failed |
| Why 2 | Why did assertion fail? | Wrong value returned |
| Why 3 | Why was value wrong? | Calculation error |
| Why 4 | Why was calculation wrong? | Variable not initialized |
| Why 5 | Why wasn't it initialized? | Missing init in constructor |

**Root Cause**: Constructor missing variable initialization

### Fishbone (Ishikawa) Diagram

Categories for software bugs:
- **Code**: Logic errors, edge cases, algorithms
- **Data**: Invalid input, corrupt state, missing validation
- **Environment**: Config, dependencies, resources
- **Integration**: APIs, protocols, contracts
- **Process**: Testing gaps, review failures

### Fault Tree Analysis

```
                    [Bug Symptom]
                         |
           +-------------+-------------+
           |             |             |
      [Cause A]     [Cause B]     [Cause C]
           |             |
      +----+----+   +----+----+
      |         |   |         |
   [A1]      [A2] [B1]      [B2]
```

## Investigation Phases

### Phase 1: Problem Definition
- What is the symptom?
- When does it occur?
- What is the impact?
- Is it reproducible?

### Phase 2: Data Collection
- Error messages and logs
- System state at failure
- Recent changes (code, config, deps)
- Related issues

### Phase 3: Analysis
- Timeline reconstruction
- Cause-effect mapping
- Hypothesis testing
- Evidence evaluation

### Phase 4: Solution
- Root cause identification
- Fix development
- Verification
- Prevention measures

## Root Cause Categories

### Immediate Causes
Direct trigger of the bug:
- Specific code line
- Particular input value
- Configuration setting

### Contributing Causes
Factors that enabled the bug:
- Missing validation
- Insufficient testing
- Code complexity

### Systemic Causes
Organizational/process issues:
- Missing code review
- Inadequate testing strategy
- Documentation gaps

## Prevention Strategies

### Technical Prevention
- Input validation
- Defensive programming
- Error handling
- Type checking

### Process Prevention
- Code review checklists
- Testing requirements
- CI/CD gates
- Documentation standards

### Monitoring Prevention
- Health checks
- Alerting thresholds
- Anomaly detection
- Audit logging

## Output Template

```markdown
# Root Cause Analysis Report

## Problem Statement
[Clear description of the bug]

## Timeline
- [Time]: [Event]
- [Time]: [Event]

## Investigation Summary
[What was investigated and found]

## Root Cause
**Immediate**: [Direct cause]
**Contributing**: [Enabling factors]
**Systemic**: [Process/org issues]

## Evidence
- [Evidence 1]
- [Evidence 2]

## Solution
**Fix**: [Technical solution]
**Verification**: [How to verify fix]

## Prevention
- [Prevention measure 1]
- [Prevention measure 2]

## Lessons Learned
- [Learning 1]
- [Learning 2]
```
