---
name: code-review
description: Code review methodology and best practices
---

# Code Review Methodology

## Objective

Conduct thorough, constructive code reviews that improve code quality while respecting developer time and effort.

## Review Checklist

### Correctness
- [ ] Logic is correct and handles edge cases
- [ ] Error handling is appropriate
- [ ] Boundary conditions are handled
- [ ] Concurrent access is safe (if applicable)

### Design
- [ ] Code follows existing patterns
- [ ] Abstractions are appropriate
- [ ] Dependencies are justified
- [ ] Interface is intuitive

### Maintainability
- [ ] Code is readable and self-documenting
- [ ] Names are clear and consistent
- [ ] Complexity is manageable
- [ ] Comments explain "why" not "what"

### Performance
- [ ] No obvious inefficiencies
- [ ] Resource usage is reasonable
- [ ] Scaling considerations addressed

### Security
- [ ] Input is validated
- [ ] Output is properly encoded
- [ ] Sensitive data is protected
- [ ] Authentication/authorization is correct

### Testing
- [ ] Tests cover new functionality
- [ ] Edge cases are tested
- [ ] Tests are maintainable
- [ ] Test names are descriptive

## Feedback Guidelines

### Constructive Feedback

**DO**:
- Explain the "why" behind suggestions
- Provide examples or alternatives
- Acknowledge good practices
- Use questions to prompt thinking

**DON'T**:
- Make personal comments
- Use dismissive language
- Demand changes without explanation
- Focus on minor style issues

### Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| Critical | Security vulnerability, data loss risk | Block merge |
| High | Significant bug, major design flaw | Request changes |
| Medium | Code smell, minor issue | Suggest fix |
| Low | Nitpick, optional improvement | Comment only |

### Comment Templates

**Bug Found**:
```
🐛 Bug: [description]

This could cause [impact] when [condition].

Suggested fix:
[code example]
```

**Design Suggestion**:
```
💡 Suggestion: [brief description]

Consider [alternative approach] because [reasoning].

This would [benefit].
```

**Question**:
```
❓ Question: [question]

I'm trying to understand [context]. Could you explain [specific aspect]?
```

## Review Workflow

1. **Understand Context**
   - Read PR description
   - Understand the goal
   - Check related issues/docs

2. **High-Level Review**
   - Architecture and design
   - Overall approach
   - Major concerns

3. **Detailed Review**
   - Line-by-line analysis
   - Edge cases
   - Error handling

4. **Final Assessment**
   - Summarize findings
   - Provide verdict
   - Suggest next steps
