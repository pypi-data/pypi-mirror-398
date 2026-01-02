---
name: troubleshooting
description: Systematic IT troubleshooting methodology
---

# IT Troubleshooting Methodology

## Objective

Systematically diagnose and resolve IT issues using proven troubleshooting frameworks.

## Troubleshooting Framework

### 1. Problem Identification

**Information Gathering**:
- What is the exact symptom?
- When did it start?
- What changed recently?
- Who is affected?
- Is it intermittent or constant?

**Scope Definition**:
- Single user vs multiple users
- Single system vs multiple systems
- Single application vs platform-wide

### 2. Hypothesis Generation

**Common Categories**:
- Configuration change
- Resource exhaustion
- Network connectivity
- Authentication/authorization
- Software bug
- Hardware failure
- External dependency

**Prioritization**:
- Recent changes (most likely)
- Known issues (check KB)
- Common failure modes
- Environmental factors

### 3. Testing and Validation

**Isolation Testing**:
- Can you reproduce the issue?
- Does it happen in isolation?
- What conditions trigger it?

**Comparison Testing**:
- Working vs non-working system
- Before vs after
- Different users/permissions

### 4. Resolution Implementation

**Change Control**:
- Document current state
- Make one change at a time
- Verify after each change
- Have rollback plan

**Verification**:
- Confirm issue resolved
- Check for side effects
- Test edge cases
- Get user confirmation

### 5. Documentation

**Required Documentation**:
- Root cause
- Resolution steps
- Time to resolution
- Prevention measures

## Domain-Specific Checklists

### Network Issues
- [ ] Check physical connectivity
- [ ] Verify IP configuration
- [ ] Test DNS resolution
- [ ] Check firewall rules
- [ ] Trace network path
- [ ] Review recent changes

### Database Issues
- [ ] Check connection count
- [ ] Review slow query log
- [ ] Check disk space
- [ ] Verify replication status
- [ ] Review recent schema changes
- [ ] Check backup status

### Security Issues
- [ ] Review access logs
- [ ] Check authentication systems
- [ ] Verify permissions
- [ ] Scan for vulnerabilities
- [ ] Review recent access changes
- [ ] Check compliance status

### Cloud Issues
- [ ] Check service health
- [ ] Review resource limits
- [ ] Verify IAM permissions
- [ ] Check network configuration
- [ ] Review recent deployments
- [ ] Check billing/quotas
