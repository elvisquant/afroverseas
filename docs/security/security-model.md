Security is enforced at every layer — from source control to runtime — with policy-as-code and short-lived identities to minimize trust and blast radius.
# Security & Governance Model
Security governance goals:
    .Minimize trust
    .Prevent unsafe changes
    .Protect secrets and identities
    .Secure the supply chain
    .Be auditable and automated

## Principles
- Least privilege
- Defense in depth
- Shift-left security
- Automation over manual controls

## Security Architecture Overview

Security is enforced across four layers:
 
    Source Control → CI/CD → Runtime → Data

## Source Control Security
Describe branch protection and review policies.

If code enters Git unsafely, no pipeline can fix it.

Controls have to be implemented :

    .Protected branches
    .Mandatory pull request reviews
    .Signed commits (optional, advanced)
    .Restricted direct pushes to main

## CI/CD Security

Pipelines are part of the production attack surface.

Controls

    .Short-lived credentials (OIDC)
    .Separate identities per pipeline
    .No static secrets in CI
    .Dependency and image scanning

Tools 

    .Trivy (vulnerability scanning)
    .SonarQube (static analysis)
    .Policy-as-code (OPA / Conftest)

## Policy-As-Code (Prevention, Not Detection)
Rules enforced automatically scale better than reviews.

What policies enforce:

    .Approved regions only
    .Mandatory encryption
    .Required labels and naming
    .Disallowed resource types

## Secrets & Identity management

Secrets

    .Stored in managed secret storage
    .Injected at runtime
    .Rotated regularly
    .Never committed or baked into images

Identity

    .One service account per workload
    .Least privilege permissions
    .No shared identities

## Runtime Security

Assume the application can be compromised — limit blast radius.

Controls:

    .Minimal container images
    .No root containers
    .Resource limits enforced
    .Network access restricted

## Threat Model

Threats considered

    .Compromised CI pipeline
    .Leaked credentials
    .Vulnerable dependencies
    .Misconfigured infrastructure

Mitigations

    .Short-lived credentials
    .Policy enforcement
    .Automated scanning
    .Least privilege access
