# ADR-005: Security and Vulnerability Management

## Status
Accepted

## Context
Security vulnerabilities discovered late in the lifecycle increase:
- Deployment risk
- Incident probability
- Remediation cost

## Decision
Security checks are enforced early in CI pipelines using:
- Trivy for container vulnerability scanning
- SonarQube for static code analysis
- Policy-as-code for compliance enforcement

## Alternatives Considered
- Manual security reviews
- Runtime-only security controls

## Consequences
### Positive
- Early detection of vulnerabilities
- Automated enforcement
- Reduced production risk

### Trade-offs
- Increased pipeline execution time
- Requires vulnerability triage process
