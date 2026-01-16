Deployments are allowed as long as the service remains within its error budget. If SLOs are violated, releases pause automatically.

# Observability & SRE Model
Observability goals:

    .Measure user-facing behavior
    .Support SLO-driven delivery
    .Detect failures early
    .Enable fast root-cause analysis
    .Drive automated rollback

## Observability  Model (The 3 Pillars)

 Metrics  → What is happening?
 Logs     → Why is it happening?
 Traces   → Where is it happening?

Note:"Metrics are primary,Logs and traces are supporting evidence."

## Objectives
- Measure user experience
- Detect failures early
- Enable data-driven decisions

## Metrics Strategy

We define metrics based on user experience, not infrastructure noise.

Core service metrics

    .Request success rate
    .Request latency (p95 / p99)
    .Availability
    .Error rate

Supporting metrics

    .Resource saturation
    .Database connection health
    .Cold start behavior

## Service Level Objectives(SLOs)

We deploy as long as we are within our error budget.

    .Availability SLO: 99.9% successful requests over 30 days
    .Latency SLO: 95% of requests < 500ms
    .Error Budget: 0.1% failure allowance

## Alerting Philosophy
Alerts represent users being harmed.

What you alert on:

    .SLO violations
    .User-visible degradation

What you do NOT alert on:

    .CPU spikes
    .Pod restarts
    .Single instance failures

## Observability-Driven Deployment 

Deployments are monitored events.

During rollout:

    .Metrics are evaluated continuously
    .Canary traffic is compared to baseline
    .Rollout pauses or rolls back automatically

Observability is part of CI/CD, not after.

## Dashboard Design Principles

Dashboards answer questions, not show data.

Core dashboards

    .Service health overview
    .Deployment comparison
    .Error budget burn rate
    .Latency distribution

Each dashboard answers:

   “Should I act right now?”

## Incident Response

    .Detection → via SLO alerts
    .Triage → dashboards first, logs second
    .Mitigation → rollback or traffic shift
    .Post-incident → review and improvement

