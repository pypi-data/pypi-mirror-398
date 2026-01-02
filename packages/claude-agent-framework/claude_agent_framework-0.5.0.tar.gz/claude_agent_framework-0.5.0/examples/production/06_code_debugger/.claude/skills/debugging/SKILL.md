---
name: debugging
description: Systematic debugging strategies and techniques
---

# Debugging Skill

## Objectives

Provide systematic methodology for debugging code:
- Identify bugs efficiently
- Find root causes
- Fix without side effects
- Prevent regression

## Debugging Strategies

### 1. Binary Search Debugging
When bug location is unknown:
1. Identify range where bug exists
2. Test midpoint
3. Narrow range based on result
4. Repeat until isolated

### 2. Trace-Based Debugging
For flow-related bugs:
1. Add logging at key points
2. Trace execution path
3. Compare expected vs actual flow
4. Identify divergence point

### 3. State Inspection
For data-related bugs:
1. Capture state at key points
2. Compare with expected state
3. Identify corruption point
4. Trace data source

### 4. Regression Testing
When something "used to work":
1. Identify when it broke (git bisect)
2. Compare working vs broken code
3. Isolate the change
4. Understand why change broke it

## Bug Categories

### Logic Errors
- Off-by-one errors
- Incorrect conditionals
- Wrong operator precedence
- Missing edge cases

### Data Errors
- Null/undefined references
- Type mismatches
- Invalid state transitions
- Race conditions

### Integration Errors
- API contract violations
- Protocol mismatches
- Version incompatibilities
- Configuration issues

### Performance Bugs
- Memory leaks
- Inefficient algorithms
- Blocking operations
- Resource exhaustion

## Debugging Tools Usage

### Logging
```python
# Strategic logging
logger.debug(f"Function entry: {func.__name__}, args={args}")
logger.debug(f"State: {vars(self)}")
logger.debug(f"Exit with result: {result}")
```

### Assertions
```python
# Catch invalid states early
assert data is not None, "Data should not be None at this point"
assert len(items) > 0, "Items list should not be empty"
```

### Breakpoints
- Set at suspected locations
- Conditional breakpoints for specific cases
- Watch expressions for key variables

## Common Patterns

### The Scientific Method
1. **Observe**: Gather data about the bug
2. **Hypothesize**: Form theory about cause
3. **Predict**: What would prove/disprove hypothesis
4. **Test**: Execute debugging action
5. **Analyze**: Evaluate results
6. **Iterate**: Refine hypothesis

### Rubber Duck Debugging
1. Explain the code line by line
2. Describe expected behavior
3. Describe actual behavior
4. Identify discrepancy

## Output Specification

Debugging reports should include:
- Clear problem statement
- Steps taken to investigate
- Findings and evidence
- Root cause identification
- Proposed fix
- Verification approach
