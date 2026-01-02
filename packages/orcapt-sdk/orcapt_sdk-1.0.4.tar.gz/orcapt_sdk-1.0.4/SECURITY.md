# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### Where to Report

**Do NOT open a public issue.** Instead:

1. Email: security@orcapt.com
2. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Status Updates**: Every 7 days until resolved
- **Disclosure Timeline**: 90 days after fix is available

### Bug Bounty

We do not currently offer a bug bounty program, but we greatly appreciate responsible disclosure.

## Security Best Practices

### For Users

#### 1. Environment Variables

Never commit sensitive data:

```python
# ❌ BAD - Hardcoded secrets
OPENAI_API_KEY = "sk-..."

# ✅ GOOD - Use environment variables
import os
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
```

#### 2. Input Validation

Always validate user input:

```python
from orca.common.exceptions import ValidationError

def process_user_input(data):
    if not data or not isinstance(data, dict):
        raise ValidationError("Invalid input data")

    # Validate required fields
    required = ["message", "user_id"]
    for field in required:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

    return data
```

#### 3. Error Handling

Don't expose sensitive information in errors:

```python
try:
    # Your code
    pass
except Exception as e:
    # ❌ BAD - Exposes internal details
    session.error(f"Database error: {str(e)}")

    # ✅ GOOD - Generic message
    session.error("An error occurred. Please try again.")
    logger.error(f"Internal error: {e}", exc_info=True)
```

#### 4. Rate Limiting

Implement rate limiting for production:

```python
from functools import wraps
import time

def rate_limit(max_calls=10, period=60):
    """Simple rate limiter decorator."""
    calls = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [c for c in calls if c > now - period]

            if len(calls) >= max_calls:
                raise Exception("Rate limit exceeded")

            calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(max_calls=100, period=60)
def process_request(data):
    pass
```

#### 5. Lambda Security

For Lambda deployments:

```python
# Enable CORS only for specific origins
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",")

def validate_origin(origin):
    return origin in ALLOWED_ORIGINS

# Validate JWT tokens
import jwt

def validate_token(token):
    try:
        payload = jwt.decode(
            token,
            os.environ["JWT_SECRET"],
            algorithms=["HS256"]
        )
        return payload
    except jwt.InvalidTokenError:
        return None
```

#### 6. Dependency Security

Keep dependencies updated:

```bash
# Check for security vulnerabilities
pip install safety
safety check

# Update dependencies
pip install --upgrade orca
```

### For Contributors

#### 1. Code Review

All code must be reviewed before merging:

- Check for SQL injection vulnerabilities
- Verify input validation
- Ensure no secrets in code
- Review error messages

#### 2. Testing

Include security tests:

```python
def test_sql_injection_prevention():
    """Test that SQL injection is prevented."""
    malicious_input = "'; DROP TABLE users; --"
    result = process_input(malicious_input)
    # Assert safe handling
    pass

def test_xss_prevention():
    """Test that XSS is prevented."""
    malicious_input = "<script>alert('XSS')</script>"
    result = sanitize_html(malicious_input)
    assert "<script>" not in result
```

#### 3. Secrets Management

Never commit secrets:

```bash
# Add to .gitignore
.env
.env.local
.env.*.local
*.key
*.pem
secrets.json
```

Use environment variables or secret managers:

```python
# ✅ GOOD - Environment variables
API_KEY = os.environ.get("API_KEY")

# ✅ GOOD - AWS Secrets Manager
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='my-secret')
```

## Security Features

### 1. Type Safety

Orca SDK uses Pydantic for type validation:

```python
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    message: str
    user_id: int

    @validator('message')
    def validate_message(cls, v):
        if len(v) > 10000:
            raise ValueError('Message too long')
        return v
```

### 2. Error Handling

Custom exception hierarchy prevents information leakage:

```python
from orca.common.exceptions import OrcaException

try:
    # Your code
    pass
except OrcaException as e:
    # Safe error handling
    logger.error(f"Error: {e.to_dict()}")
    raise
```

### 3. Logging

Secure logging configuration:

```python
from orca.common.logging_config import setup_logging

# Sensitive data is automatically masked
setup_logging(
    level="INFO",
    mask_sensitive=True  # Masks API keys, tokens, etc.
)
```

## Compliance

### GDPR

For GDPR compliance:

- Don't log personally identifiable information (PII)
- Implement data retention policies
- Allow users to request data deletion

```python
def anonymize_user_data(data):
    """Remove PII from logs."""
    sensitive_fields = ['email', 'phone', 'ssn', 'address']
    for field in sensitive_fields:
        if field in data:
            data[field] = "***REDACTED***"
    return data
```

### SOC 2

For SOC 2 compliance:

- Enable audit logging
- Implement access controls
- Monitor for suspicious activity

## Security Checklist

Before deploying to production:

- [ ] All secrets in environment variables
- [ ] Input validation implemented
- [ ] Error messages don't expose internal details
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Dependencies updated
- [ ] Security tests passing
- [ ] Logging configured (no PII)
- [ ] Access controls in place
- [ ] Monitoring and alerts configured

## Incident Response

If you suspect a security breach:

1. **Contain**: Isolate affected systems
2. **Assess**: Determine scope and impact
3. **Notify**: Contact security@orcapt.com
4. **Remediate**: Apply fixes
5. **Review**: Conduct post-incident review

## Updates

This security policy is updated regularly. Last update: December 2025

For questions: security@orcapt.com
