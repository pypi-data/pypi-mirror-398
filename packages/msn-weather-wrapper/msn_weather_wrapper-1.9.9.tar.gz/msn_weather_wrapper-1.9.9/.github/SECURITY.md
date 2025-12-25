# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of MSN Weather Wrapper seriously. If you have discovered a security vulnerability, please report it to us as described below.

### Please Do NOT:

- Open a public GitHub issue for security vulnerabilities
- Post about the vulnerability in public forums or social media
- Attempt to exploit the vulnerability beyond what is necessary to demonstrate it

### Please DO:

**Report security vulnerabilities via GitHub Security Advisories:**

1. Go to the [Security tab](https://github.com/jim-wyatt/msn-weather-wrapper/security/advisories)
2. Click "Report a vulnerability"
3. Fill out the advisory form with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

**Or email directly:**
- Email: the.jim.wyatt@outlook.com
- Subject: [SECURITY] MSN Weather Wrapper Vulnerability Report

### What to Include

Please include the following information in your report:

- Type of vulnerability (e.g., XSS, SQL injection, authentication bypass)
- Full paths of affected source file(s)
- Location of the affected code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability and how it could be exploited
- Your name/handle for credit (optional)

### What to Expect

- **Acknowledgment**: Within 48 hours of your report
- **Initial Assessment**: Within 5 business days
- **Status Updates**: Every 7 days until resolution
- **Fix Timeline**: Critical vulnerabilities within 7 days, high severity within 14 days
- **Public Disclosure**: After a fix is released and users have had time to update

### Response Process

1. **Acknowledgment**: We'll confirm receipt of your report
2. **Validation**: We'll reproduce and validate the vulnerability
3. **Assessment**: We'll assess the severity using CVSS scoring
4. **Fix Development**: We'll develop and test a fix
5. **Release**: We'll release a patch version with the fix
6. **Disclosure**: We'll publish a security advisory with credit to the reporter
7. **CVE Assignment**: We'll request a CVE identifier for tracking

## Security Measures

This project implements several security measures:

### Automated Security Scanning

- **SAST**: Bandit (Python security linting), Semgrep (pattern detection)
- **Dependency Scanning**: Safety, pip-audit for known vulnerabilities
- **Container Scanning**: Trivy, Grype for image vulnerabilities
- **License Compliance**: Automated checking of dependency licenses
- **Schedule**: Weekly scans every Monday at 2 AM UTC + on all pushes to main

### Code Quality

- Pre-commit hooks with security linters
- Type checking with mypy (strict mode)
- Input validation and sanitization
- Rate limiting on API endpoints
- Comprehensive test suite (89% coverage)

### Deployment Security

- Multi-stage container builds (reduced attack surface)
- Non-root container user
- Read-only file systems where possible
- Health check endpoints for monitoring
- Gunicorn with secure worker configuration

## Known Security Considerations

### Input Validation

The API validates and sanitizes all user inputs to prevent:
- SQL injection (though we don't use a database)
- Cross-site scripting (XSS)
- Path traversal
- Command injection

### Rate Limiting

API endpoints are rate-limited:
- 30 requests per minute per IP address
- 200 requests per hour globally
- Configurable via environment variables

### CORS Configuration

CORS is configured for secure cross-origin requests:
- Dual-layer protection (Flask + Nginx)
- Configurable allowed origins
- Credentials support for authenticated requests

### Dependencies

All dependencies are:
- Scanned for known vulnerabilities
- Updated regularly via Dependabot
- License-checked for compatibility
- Pinned to specific versions in production

## Security Best Practices for Users

### API Key/Token Management

- Never commit API keys or tokens to version control
- Use environment variables for sensitive configuration
- Rotate credentials regularly
- Use different credentials for development and production

### Container Deployment

- Always use specific version tags (not `latest`)
- Run containers as non-root user
- Use read-only file systems when possible
- Regularly update base images
- Scan images before deployment

### Network Security

- Use HTTPS in production
- Configure firewalls appropriately
- Limit API access to trusted networks when possible
- Monitor access logs for suspicious activity

## Security Updates

Security updates are released as patch versions (e.g., 1.2.3 → 1.2.4) and include:

- Fix for the vulnerability
- Tests to prevent regression
- Updated documentation
- Security advisory on GitHub

Users are strongly encouraged to:
- Subscribe to release notifications
- Update to the latest version promptly
- Review security advisories
- Test updates in staging before production

## Hall of Fame

We appreciate security researchers who help keep our project safe:

<!-- Security researchers who report vulnerabilities will be listed here with their permission -->

- *Your name could be here!*

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://snyk.io/blog/python-security-best-practices/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [GitHub Security Features](https://docs.github.com/en/code-security)

## Contact

For non-security issues, please use:
- GitHub Issues: https://github.com/jim-wyatt/msn-weather-wrapper/issues
- Discussions: https://github.com/jim-wyatt/msn-weather-wrapper/discussions

For security issues, please use the reporting methods described above.

---

Last updated: December 2, 2025
