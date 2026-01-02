# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow responsible disclosure practices:

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please email: support@agentbill.io

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to Expect

1. **Acknowledgment**: We'll acknowledge your report within 48 hours
2. **Investigation**: We'll investigate and keep you updated on progress
3. **Fix**: We'll develop and test a fix
4. **Release**: We'll release a security patch
5. **Credit**: We'll credit you in the security advisory (unless you prefer to remain anonymous)

### Security Best Practices

When using the AgentBill CrewAI integration:

1. **API Keys**
   - Never commit API keys to version control
   - Use environment variables: `os.getenv("AGENTBILL_API_KEY")`
   - Rotate keys regularly
   - Use different keys for development/production

2. **Dependencies**
   - Keep the package updated to the latest version
   - Run `pip install --upgrade agentbill-crewai` regularly
   - Monitor security advisories
   - Use `pip-audit` to check for vulnerabilities

3. **Data Privacy**
   - Review what data is being tracked
   - Implement proper data retention policies
   - Follow GDPR/CCPA guidelines if applicable
   - Be careful with sensitive data in agent prompts

4. **Network Security**
   - Use HTTPS endpoints only
   - Verify SSL certificates
   - Use secure base URLs
   - Implement proper timeouts

## Security Features

The AgentBill CrewAI integration includes:

- ✅ HTTPS-only communication
- ✅ API key authentication
- ✅ No sensitive data logged by default
- ✅ Configurable debug mode for development
- ✅ Thread-safe operations
- ✅ Proper error handling
- ✅ Non-invasive wrapping

## CrewAI-Specific Security

### Agent Prompt Security
Be aware that CrewAI agents may process sensitive information. The AgentBill integration tracks execution but does not validate or sanitize agent inputs.

### Data Capture
The integration captures:
- Agent roles and goals
- Task descriptions
- Execution metrics
- Token usage
- Error information

**Do not include sensitive data in agent configurations if you don't want it tracked.**

### Crew Execution
Ensure your crew executions:
- Don't expose credentials
- Handle errors gracefully
- Validate inputs appropriately
- Log securely

## Questions?

For general security questions, email: support@agentbill.io

Thank you for helping keep AgentBill secure! 🔒
