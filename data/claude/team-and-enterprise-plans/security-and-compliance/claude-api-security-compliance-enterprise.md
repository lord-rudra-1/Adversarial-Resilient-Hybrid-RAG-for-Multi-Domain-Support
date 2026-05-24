# Claude API Security and Compliance — Enterprise Reference

## Anthropic's Bug Bounty Program

Anthropic maintains a responsible disclosure program for security vulnerabilities found in Claude products:

### Scope
- claude.ai web application and APIs
- Claude mobile applications (iOS, Android)
- Claude Code and Claude Desktop
- Authentication and authorization systems
- Data handling and privacy mechanisms

### Out of Scope
- Social engineering attacks against Anthropic employees
- Denial of service attacks
- Issues in third-party integrations not maintained by Anthropic
- "Jailbreaking" or prompt injection (handled separately by the Trust & Safety team)
- Issues already known or reported

### Reporting

Report vulnerabilities to: **security@anthropic.com**

Include:
- Detailed description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Any proof-of-concept code

### Bounty Amounts

| Severity | Bounty Range |
|---|---|
| Critical (RCE, auth bypass, data breach) | $5,000 — $25,000 |
| High (XSS, CSRF, privilege escalation) | $1,000 — $5,000 |
| Medium (information disclosure, misconfigurations) | $250 — $1,000 |
| Low (minor issues, edge cases) | $50 — $250 |

### Response Timeline

- Acknowledgment: within 24 hours
- Triage and severity assessment: within 3 business days
- Resolution: varies by severity (critical: 48h, high: 7 days, medium: 30 days)
- Bounty payment: within 30 days of resolution

### Legal Safe Harbor

Anthropic will not pursue legal action against researchers who:
- Report in good faith
- Avoid accessing user data
- Do not degrade service availability
- Follow responsible disclosure timelines

## HIPAA Compliance

Anthropic does **not** currently sign Business Associate Agreements (BAAs) for Claude. Claude should not be used to process, store, or transmit Protected Health Information (PHI) as defined by HIPAA.

Enterprise customers requiring HIPAA compliance should:
1. Contact sales@anthropic.com to discuss roadmap
2. Consider using the Anthropic API with a HIPAA-compliant infrastructure wrapper
3. Ensure all PHI is stripped before sending to Claude

## SOC 2 Type II

Anthropic has completed SOC 2 Type II certification. Reports are available to enterprise customers upon request through your account manager or at trust.anthropic.com.

## Data Residency

- All data processed in US data centers by default
- EU data residency available for Enterprise plans
- No data residency options for individual or Team plans currently

## Web Crawling and Robots.txt

Claude's web features respect robots.txt directives. Website owners can opt out of Claude accessing their content:

1. Add to robots.txt:
```
User-agent: ClaudeBot
Disallow: /
```

2. Or contact Anthropic at crawler-control@anthropic.com to request domain-level blocking

3. Note: This controls Claude's web search and browsing features only — it does not prevent users from manually pasting website content into Claude conversations

## Model Training Data Opt-Out

Users can control whether their conversations are used for model training:
- Toggle: Settings > Privacy > "Improve Claude"
- When OFF: conversations are not used for training
- When ON: conversations may be used, subject to anonymization
- The setting applies to all future conversations; it is not retroactive
