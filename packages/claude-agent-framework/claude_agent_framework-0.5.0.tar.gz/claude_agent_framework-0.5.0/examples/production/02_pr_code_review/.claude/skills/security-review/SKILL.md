---
name: security-review
description: Security-focused code review guidelines
---

# Security Review Guidelines

## Objective

Identify security vulnerabilities in code changes before they reach production.

## OWASP Top 10 Checklist

### 1. Injection
- SQL injection in database queries
- Command injection in system calls
- LDAP injection in directory queries
- XPath injection in XML processing

**Detection**:
- String concatenation in queries
- User input in command execution
- Dynamic query construction

### 2. Broken Authentication
- Weak password policies
- Missing session management
- Insecure credential storage
- Missing MFA where required

**Detection**:
- Password handling code
- Session token management
- Remember-me functionality

### 3. Sensitive Data Exposure
- Unencrypted sensitive data
- Weak cryptographic algorithms
- Missing TLS for data in transit
- Logging sensitive information

**Detection**:
- Encryption usage patterns
- Data classification handling
- Log statements with user data

### 4. XML External Entities (XXE)
- Unsafe XML parser configuration
- External entity processing enabled

**Detection**:
- XML parsing code
- SOAP/SAML handling

### 5. Broken Access Control
- Missing authorization checks
- IDOR vulnerabilities
- Path traversal risks
- CORS misconfigurations

**Detection**:
- API endpoint handlers
- File access operations
- Resource identifiers from user input

### 6. Security Misconfiguration
- Debug mode in production
- Default credentials
- Unnecessary features enabled
- Missing security headers

**Detection**:
- Configuration files
- Framework settings
- HTTP response headers

### 7. Cross-Site Scripting (XSS)
- Reflected XSS
- Stored XSS
- DOM-based XSS

**Detection**:
- User input rendering
- Template variable usage
- JavaScript string construction

### 8. Insecure Deserialization
- Untrusted data deserialization
- Missing integrity checks

**Detection**:
- Pickle/Marshal usage
- JSON/XML deserialization
- Object serialization

### 9. Using Components with Known Vulnerabilities
- Outdated dependencies
- Unpatched libraries

**Detection**:
- Dependency changes
- Version specifications

### 10. Insufficient Logging & Monitoring
- Missing security event logging
- Sensitive data in logs
- Missing audit trails

**Detection**:
- Authentication event handling
- Error logging patterns

## Security Review Output

```markdown
### Security Findings

#### Critical
- [VULN-001] [Type]: [Description]
  - Location: [file:line]
  - Impact: [potential damage]
  - Remediation: [how to fix]

#### High
- [VULN-002] ...

### Security Score: [0-100]

### Recommendations
1. [Priority action]
2. [Secondary action]
```

## Secure Coding Patterns

### Input Validation
- Whitelist validation preferred
- Validate on server side
- Sanitize before use

### Output Encoding
- Context-aware encoding
- Use framework functions
- Avoid raw output

### Authentication
- Use established frameworks
- Implement rate limiting
- Log authentication events

### Cryptography
- Use standard algorithms
- Proper key management
- Avoid custom crypto
