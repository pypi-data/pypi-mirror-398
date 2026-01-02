---
name: risk-assessment
description: Risk identification and analysis frameworks for technology decisions
---

# Risk Assessment Skill

## Objectives

Provide structured methodology for identifying and analyzing risks:
- Systematic risk identification
- Impact and probability assessment
- Mitigation strategy development

## Risk Categories

### Technical Risks
| Risk Type | Examples | Indicators |
|-----------|----------|------------|
| Performance | Latency, throughput issues | Benchmark gaps, load test failures |
| Scalability | Growth limitations | Architecture constraints, bottlenecks |
| Reliability | System failures, data loss | SPOF, recovery gaps |
| Security | Vulnerabilities, breaches | CVEs, compliance gaps |
| Integration | API incompatibilities | Version conflicts, protocol mismatches |

### Implementation Risks
| Risk Type | Examples | Indicators |
|-----------|----------|------------|
| Timeline | Delays, scope creep | Complexity underestimation |
| Resource | Skill gaps, turnover | Training needs, market scarcity |
| Quality | Technical debt, bugs | Code coverage gaps, review failures |
| Dependency | Third-party failures | Vendor instability, EOL products |

### Business Risks
| Risk Type | Examples | Indicators |
|-----------|----------|------------|
| Financial | Budget overrun, hidden costs | Incomplete TCO analysis |
| Strategic | Lock-in, obsolescence | Single vendor dependency |
| Operational | Downtime, productivity loss | Change management gaps |
| Compliance | Regulatory violations | Certification requirements |

## Risk Assessment Matrix

### Probability Scale
| Level | Description | Likelihood |
|-------|-------------|------------|
| 5 | Almost Certain | >90% |
| 4 | Likely | 60-90% |
| 3 | Possible | 30-60% |
| 2 | Unlikely | 10-30% |
| 1 | Rare | <10% |

### Impact Scale
| Level | Description | Effect |
|-------|-------------|--------|
| 5 | Critical | Project failure, major loss |
| 4 | Major | Significant delay, budget overrun |
| 3 | Moderate | Notable impact, recoverable |
| 2 | Minor | Limited impact, easily managed |
| 1 | Negligible | Minimal impact |

### Risk Score = Probability × Impact

| Score | Priority | Action |
|-------|----------|--------|
| 15-25 | Critical | Immediate mitigation required |
| 8-14 | High | Mitigation plan essential |
| 4-7 | Medium | Monitor and plan contingency |
| 1-3 | Low | Accept and monitor |

## Mitigation Strategies

### Strategy Types
1. **Avoid**: Eliminate the risk source
2. **Transfer**: Shift risk to third party (insurance, contracts)
3. **Mitigate**: Reduce probability or impact
4. **Accept**: Acknowledge and prepare contingency

### Mitigation Plan Template
```markdown
## Risk: [Risk Name]

**Category**: [Technical/Implementation/Business]
**Probability**: [1-5]
**Impact**: [1-5]
**Risk Score**: [P × I]

### Description
[Detailed risk description]

### Root Cause
[What causes this risk]

### Impact Analysis
- Best case: [Outcome]
- Most likely: [Outcome]
- Worst case: [Outcome]

### Mitigation Strategy
- Strategy type: [Avoid/Transfer/Mitigate/Accept]
- Actions:
  1. [Action 1]
  2. [Action 2]
- Cost: [Mitigation cost]

### Contingency Plan
[What to do if risk occurs]

### Monitoring
- Trigger indicators: [Warning signs]
- Review frequency: [Weekly/Monthly]
```

## Output Specification

Risk assessments should include:
- Risk register with all identified risks
- Heat map visualization (probability vs impact)
- Top risks with mitigation plans
- Residual risk summary
- Monitoring recommendations
