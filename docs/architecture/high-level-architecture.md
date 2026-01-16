# High-Level Architecture

System Overview

The Afroverseas Platform is designed as a cloud-native, Git-driven platform where infrastructure, application delivery, security controls, and observability are coordinated through automation.

Git acts as the system of record for all changes. Any modification to infrastructure, application code, or policy is introduced through version-controlled pull requests and validated through automated pipelines before reaching production.

The platform intentionally relies on managed cloud services to reduce operational overhead while maintaining scalability, reliability, and security. Responsibilities are clearly separated between provisioning, deployment, runtime execution, and monitoring to minimize blast radius and simplify ownership.

## Design Goals
- Scalability with minimal operational overhead
- Secure-by-default infrastructure
- Clear separation of responsibilities
- Fast and safe delivery cycles
- Observability-driven operations

## System Overview
┌──────────────────────────┐
│        Developers        │
│  (GitHub Pull Requests)  │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│      GitHub Repository   │
│  (App + Infra + Policies)│
└─────────────┬────────────┘
              │
              ▼
┌────────────────────────────────────────────┐
│             GitHub Actions CI/CD           │ 
│                                            │
│  ┌──────────────┐  ┌────────────────────┐  │
│  │ Infra Pipeline│  │ App Delivery Pipeline│ 
│  │ (Terraform)   │  │ (Build & Deploy)     │ 
│  └──────┬───────┘  └─────────┬──────────┘  │
│         │                    │             │
│         ▼                    ▼             │
│  Terraform Plan/Apply     Build Container  │
│  + Policy Validation      + Security Scan  │
└─────────┬───────────────────┬─────────────-┘
          │                   │
          ▼                   ▼
┌──────────────────────┐   ┌───────────────────┐
│ Google Cloud Platform│   │ Artifact Registry │
│                      │   │ (Docker Images)   │
│  - Cloud Run         │   └─────────┬───────-─┘
│  - Cloud SQL         │             │
│  - Secret Manager    │             ▼
│  - VPC / IAM         │     Deploy to Cloud Run
└─────────┬────────────┘
          │
          ▼
┌──────────────────────────┐
│        Application       │
│   FastAPI + Frontend     │
│   Served via HTTPS       │
└─────────┬───────────────-┘
          │
          ▼
┌──────────────────────────┐
│    Observability Stack   │
│                          │
│  - Prometheus (metrics)  │
│  - Grafana (dashboards)  │
│  - Alerting (SLO-based)  │
└──────────────────────────┘


## Domain &Traffic Flow (afroverseas.com)

    1.End users access the application via the custom domain afroverseas.com, which is managed externally through a DNS provider.

    2.DNS records route traffic to a cloud-managed HTTPS endpoint, where TLS termination and certificate management are handled automatically.

    3.Requests are forwarded to the Cloud Run service hosting the containerized FastAPI application.

    4.The application processes requests and interacts with the managed PostgreSQL database hosted in Cloud SQL using a private, authenticated connection.

    5.Responses are returned through the same managed path back to the user.

This flow ensures that:

    .All traffic is encrypted in transit
    .No direct public access to the database exists
    .Application scaling is handled automatically based on demand

This is how it works:

User
  │
  ▼
afroverseas.com (DNS – Hostinger)
  │
  ▼
Google Managed HTTPS Load Balancer
  │
  ▼
Cloud Run Service
  │
  ▼
Cloud SQL (PostgreSQL)


## CI/CD Flow
All changes originate from Git through pull requests.

    1.Infrastructure Changes

        .Changes under the infrastructure directory trigger the infrastructure pipeline.
        .Terraform plans are generated and validated against policy rules.
        .Approved changes are applied automatically, ensuring infrastructure consistency and preventing configuration drift.

    2.Application Changes

        .Application code changes trigger the application delivery pipeline.
        .Container images are built and scanned for vulnerabilities.
        .Images are published to a trusted container registry.
        .Deployments to Cloud Run are performed using progressive delivery strategies.

    3.Monitoring and Governance

        .Observability configurations and alerting rules are versioned and deployed through a dedicated pipeline.
        .Service health and reliability are continuously evaluated using defined service-level indicators.

Pipelines are designed to be independent but ordered, ensuring infrastructure readiness before application deployment while allowing fast iteration for application changes.

## Security Boundaries

Security is enforced through clearly defined trust zones:

1️⃣ CI/CD Trust Boundary

    .GitHub Actions has limited IAM permissions
    .Separate service accounts per pipeline
    .No long-lived credentials

2️⃣ Runtime Boundary

    .Cloud Run has least-privilege access
    .Secrets pulled from Secret Manager
    .No secrets in images or repo

3️⃣ Network Boundary

    .Cloud SQL accessed via private connection
    .No public DB access
    .Domain terminates at managed HTTPS layer

## Failure Considerations

The platform is designed to detect and respond to failures automatically:

    .Application health is monitored using metrics and service-level indicators.
    .Alerting is triggered based on user-impacting symptoms rather than raw resource usage.
    .Failed deployments are automatically rolled back when error thresholds are exceeded.
    .Managed services provide built-in redundancy and self-healing for common failure scenarios.

This approach prioritizes early detection, controlled recovery, and minimal user impact, aligning with Site Reliability Engineering best practices.
