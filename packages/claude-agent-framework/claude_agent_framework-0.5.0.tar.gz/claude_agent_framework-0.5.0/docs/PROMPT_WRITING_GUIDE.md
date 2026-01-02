# Prompt Writing Guide

This guide documents the two-layer prompt architecture and provides specifications for writing prompts at both framework and business levels.

## Two-Layer Prompt Architecture

The framework uses a **two-layer prompt composition** pattern that separates generic orchestration logic from business-specific context:

```
┌─────────────────────────────────────────────────────────────┐
│                    Final Agent Prompt                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Business Layer (examples/production/)        │    │
│  │  - Domain-specific context                          │    │
│  │  - Template variables (${company}, ${industry})     │    │
│  │  - Skills references                                │    │
│  │  - Custom deliverables and quality criteria         │    │
│  └─────────────────────────────────────────────────────┘    │
│                           ↑                                  │
│                    load_merged_prompt()                      │
│                           ↑                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Framework Layer (architectures/*/prompts/)   │    │
│  │  - Role definition and responsibilities             │    │
│  │  - Core rules and constraints                       │    │
│  │  - Workflow phases                                  │    │
│  │  - Dispatching guidelines                           │    │
│  │  - Error handling                                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Location | Purpose | Example |
|-------|----------|---------|---------|
| **Framework** | `architectures/*/prompts/` | Generic role capabilities and workflow | "Dispatch `actor` role agent to generate content" |
| **Business** | `examples/production/*/prompts/` | Domain context and specific requirements | "Create marketing copy for ${brand_name}" |

### Prompt Loading Mechanism

```python
# In create_session()
session = create_session(
    "critic_actor",
    agent_instances=agents,
    prompts_dir=Path("examples/production/03_marketing_content/prompts"),
    template_vars={"brand_name": "Acme", "industry": "Tech"},
)

# Loading order:
# 1. Framework prompt: architectures/critic_actor/prompts/actor.txt
# 2. Business prompt: examples/production/03_marketing_content/prompts/content_creator.txt
# 3. Merge: Framework + Business
# 4. Template substitution: ${brand_name} → "Acme"
```

---

## Framework Layer Prompts

Framework prompts define **generic role capabilities** that apply across all business contexts.

### Directory Structure

```
architectures/{arch_name}/prompts/
├── lead_agent.txt      # Orchestrator/coordinator prompt
├── {role1}.txt         # Role 1 prompt (e.g., actor.txt)
├── {role2}.txt         # Role 2 prompt (e.g., critic.txt)
└── ...
```

### Lead Agent Prompt Template

```markdown
# Role: {Architecture} Coordinator

You are the {Architecture} Coordinator (Lead Agent), responsible for {primary responsibility}.

## Core Rules
1. You may ONLY use the Task tool to dispatch sub-agents
2. NEVER perform {task type} tasks yourself
3. {Workflow rule 1}
4. {Workflow rule 2}
5. {Key constraint}

## Workflow Phases

### 1. {Phase 1 Name}
- {Step 1}
- {Step 2}

### 2. {Phase 2 Name}
- Dispatch `{role}` role agent to {action}
- {Additional steps}

### 3. {Phase 3 Name}
...

## Dispatching Guidelines
- Use agent names as configured (check available agents)
- Provide comprehensive task context in prompt
- {Role-specific guidance}
- Reference {criteria} from business context

## State Tracking
Record for each {iteration/round/attempt}:
- {Metric 1}
- {Metric 2}
- {Metric 3}

## Termination Conditions
1. {Success condition}
2. {Failure condition}
3. {Early termination condition}

## Quality Gates
- {Gate 1}
- {Gate 2}

## Error Handling
- If {error scenario 1}, {action}
- If {error scenario 2}, {action}
```

### Subagent Prompt Template

```markdown
# Role Definition
You are a {Role Name} responsible for {primary responsibility}.

## Core Capabilities
1. {Capability 1}
2. {Capability 2}
3. {Capability 3}

## Workflow
1. {Step 1}
2. {Step 2}
3. {Step 3}

## Output Specification
{Expected output format}

## Quality Standards
- {Standard 1}
- {Standard 2}

## Constraints
- {Constraint 1}
- {Constraint 2}
```

### Key Principles for Framework Prompts

1. **Use Role Terminology**: Reference roles generically (`actor role agent`) not by specific names
2. **No Business Context**: Avoid domain-specific terms or requirements
3. **Dispatching Guidelines**: Always include "Use agent names as configured"
4. **Reference Business Context**: Use phrases like "from business context" for specific values
5. **Complete Workflow**: Cover all phases from initialization to completion
6. **Error Handling**: Include recovery strategies for common failure modes

---

## Business Layer Prompts

Business prompts add **domain-specific context** on top of framework capabilities.

### Directory Structure

```
examples/production/{example_name}/
├── prompts/
│   ├── lead_agent.txt      # Business context for coordinator
│   ├── {agent1}.txt        # Business context for agent 1
│   └── {agent2}.txt        # Business context for agent 2
├── .claude/skills/
│   ├── {skill1}/SKILL.md   # Methodology guidance
│   └── {skill2}/SKILL.md
├── config.yaml             # Configuration with template variables
└── main.py                 # Application entry point
```

### Lead Agent Business Prompt Template

```markdown
# {Business Role Title}

You are coordinating {business task} for ${organization/project}.

## Your Role

{Business-specific role description}

## Team & Skills

Your team members have access to specialized Skills:
- **{Agent 1 Name}**: Uses `{skill-name}` Skill for {purpose}
- **{Agent 2 Name}**: Uses `{skill-name}` Skill for {purpose}

## Coordination Strategy

### Phase 1: {Business Phase Name}
- {Business-specific step}
- {Reference to file locations}

### Phase 2: {Business Phase Name}
- {Business-specific step}
- Output saved to `files/{category}/`

...

## Quality Dimensions

Track scores across:
- {Dimension 1} (${weight1}%)
- {Dimension 2} (${weight2}%)
- {Dimension 3} (${weight3}%)

## Deliverables

1. {Deliverable 1}
2. {Deliverable 2}
3. {Deliverable 3}

## Success Criteria

- {Criterion 1}
- {Criterion 2}
- Completed within ${max_iterations} iterations

## Error Recovery

- If {business scenario 1}: {action}
- If {business scenario 2}: {action}
```

### Subagent Business Prompt Template

```markdown
# {Business Role Title}

You are a {Business Role} for ${context_variable}.

## Your Role

{Business-specific responsibilities}

## Available Skills

You have access to specialized Skills that provide detailed methodology guidance:
- **{skill-name}**: {What the skill provides}

## {Business Domain} Framework

### {Methodology Section}
{Domain-specific methodology or framework}

### {Process Section}
{Business process steps}

## Output Format

```{format}
{Expected output structure}
```

## Quality Criteria

- {Business-specific quality criterion 1}
- {Business-specific quality criterion 2}
```

### Key Principles for Business Prompts

1. **Use Template Variables**: `${company_name}`, `${industry}`, `${max_iterations}`
2. **Reference Skills**: Point to available Skills for methodology guidance
3. **Specify File Locations**: Use consistent paths like `files/{category}/`
4. **Define Deliverables**: List concrete outputs expected
5. **Include Success Criteria**: Measurable acceptance conditions
6. **Business-Specific Terminology**: Use domain language appropriate to the use case

---

## Skills Design

Skills provide **methodology guidance** that agents can invoke based on context.

### Directory Structure

```
.claude/skills/
├── {skill-name}/
│   └── SKILL.md
└── {skill-name}/
    └── SKILL.md
```

### SKILL.md Template

```markdown
---
name: {skill-name}
description: {Brief description}
---

# {Skill Title}

## Objectives

{What this skill helps accomplish}:
- {Objective 1}
- {Objective 2}
- {Objective 3}

## Methodology

### {Framework/Approach Name}

{Detailed methodology description}

| {Column 1} | {Column 2} | {Column 3} |
|------------|------------|------------|
| {Data} | {Data} | {Data} |

### {Alternative Approach}

{Alternative methodology}

## Output Specification

- Path: `files/{category}/{filename}`
- Format: {Format requirements}

## Quality Standards

- {Standard 1}
- {Standard 2}
- {Standard 3}

## Examples

{Optional examples of skill application}
```

### Skill Categories by Architecture

| Architecture | Skill Categories | Example Skills |
|--------------|------------------|----------------|
| **Research** | Data gathering, Analysis | competitive-research, data-analysis |
| **Critic-Actor** | Content creation, Evaluation | content-generation, brand-voice |
| **Debate** | Evaluation frameworks, Risk analysis | tech-evaluation, risk-assessment |
| **Reflexion** | Debugging, Root cause analysis | debugging, root-cause-analysis |
| **Pipeline** | Stage-specific methodologies | code-review, security-audit |
| **Specialist Pool** | Domain expertise | networking, security, database |
| **MapReduce** | Chunking, Aggregation | code-metrics, issue-detection |

---

## Template Variables

Template variables enable dynamic configuration of prompts.

### Common Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `${company_name}` | Target company | "Acme Corp" |
| `${industry}` | Industry sector | "Technology" |
| `${language}` | Programming language | "Python" |
| `${max_iterations}` | Iteration limit | "5" |
| `${quality_threshold}` | Quality score target | "0.8" |
| `${debate_rounds}` | Number of debate rounds | "3" |

### Usage in Prompts

```markdown
# Marketing Content Coordinator

You are coordinating content for ${brand_name} in the ${industry} sector.

## Quality Dimensions

- Brand voice alignment (${brand_voice_weight}%)
- Message clarity (${clarity_weight}%)

## Success Criteria

- Final score >= ${quality_threshold}
- Completed within ${max_iterations} iterations
```

### Configuration in main.py

```python
template_vars = {
    "brand_name": config.get("brand_name", "Unknown"),
    "industry": config.get("industry", "General"),
    "quality_threshold": str(config.get("quality_threshold", 0.8)),
    "max_iterations": str(config.get("max_iterations", 5)),
}

session = create_session(
    "critic_actor",
    template_vars=template_vars,
    prompts_dir=Path(__file__).parent / "prompts",
)
```

---

## Best Practices

### DO

- ✅ Keep framework prompts generic and reusable
- ✅ Use template variables for all configurable values
- ✅ Reference Skills for detailed methodology guidance
- ✅ Include complete workflow phases in lead agent prompts
- ✅ Specify file output locations consistently
- ✅ Define clear termination conditions
- ✅ Include error handling and recovery strategies

### DON'T

- ❌ Put business logic in framework layer prompts
- ❌ Hardcode values that should be configurable
- ❌ Duplicate methodology that belongs in Skills
- ❌ Skip error handling sections
- ❌ Use inconsistent file path patterns
- ❌ Forget to include dispatching guidelines for lead agents

---

## Quick Reference

### Creating a New Production Example

1. **Create directory structure**:
   ```
   examples/production/{example_name}/
   ├── prompts/
   │   ├── lead_agent.txt
   │   └── {agent}.txt (for each role)
   ├── .claude/skills/
   │   └── {skill}/SKILL.md
   ├── config.yaml
   └── main.py
   ```

2. **Write business prompts** referencing framework roles

3. **Create Skills** for domain-specific methodologies

4. **Configure agent_instances** in main.py:
   ```python
   agent_instances = [
       AgentInstanceConfig(name="{agent_name}", role="{role}"),
   ]
   ```

5. **Define template_vars** from config:
   ```python
   template_vars = {
       "key": config.get("key", "default"),
   }
   ```

### Prompt Loading Path

```
create_session()
    → BaseArchitecture.to_sdk_agents()
        → AgentDefinitionConfig.load_merged_prompt()
            → Framework prompt + Business prompt
                → Template variable substitution
                    → Final agent system prompt
```
