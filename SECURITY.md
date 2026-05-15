# Security Policy — Vallum

## Reporting Security Issues

If you discover a security vulnerability, please open a private security advisory
on GitHub instead of a public issue.

## Security Measures

### 1. Secret Management

| Environment | Method |
|-------------|--------|
| Development | `.env` file (gitignored) |
| Production | GCP Secret Manager |
| CI/CD | GitHub Encrypted Secrets |

### 2. Pre-commit Protection

All commits are scanned for:
- Private keys (RSA, ECDSA, Ed25519)
- API keys (Google, OpenAI, AWS, GitHub)
- Passwords and tokens
- `.env` files

### 3. Code Security

- Input validation on all agent prompts
- Rate limiting on API endpoints
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (Streamlit handles escaping)

## Responsible Disclosure

Vallum is designed for **authorized security testing** only.
Always obtain written permission before testing systems you do not own.

## Compliance

- MITRE ATLAS 2026 technique mapping
- SOC2 audit trail structure
- HIPAA-safe logging (no PHI in logs)
- GDPR data minimization
