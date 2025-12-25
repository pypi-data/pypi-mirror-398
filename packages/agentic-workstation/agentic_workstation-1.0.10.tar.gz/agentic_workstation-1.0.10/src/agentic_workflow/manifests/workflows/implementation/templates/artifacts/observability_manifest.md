# Observability Manifest

> Instrumentation and monitoring plan for {{project_name}}

## Metadata

| Field | Value |
|-------|-------|
| **Project** | {{project_name}} |
| **Created** | {{timestamp}} |
| **Status** | DRAFT |

---

## Observability Pillars

### Metrics

| Metric Name | Type | Labels | SLI/SLO |
|-------------|------|--------|---------|
| request_duration_seconds | Histogram | method, endpoint, status | p99 < 200ms |
| request_total | Counter | method, endpoint, status | - |
| error_rate | Gauge | service, error_type | < 0.1% |

### Logs

| Log Level | Use Case | Format |
|-----------|----------|--------|
| ERROR | Exceptions, failures | JSON structured |
| WARN | Degraded states | JSON structured |
| INFO | Business events | JSON structured |
| DEBUG | Development only | JSON structured |

### Traces

| Span Name | Parent | Attributes |
|-----------|--------|------------|
| http_request | root | method, url, status |
| db_query | http_request | query_type, table |
| external_api | http_request | service, endpoint |

---

## Health Checks

### Readiness Probe

```yaml
path: /health/ready
interval: 10s
threshold: 3
```

### Liveness Probe

```yaml
path: /health/live
interval: 30s
threshold: 5
```

---

## Alerting Rules

| Alert Name | Condition | Severity | Runbook |
|------------|-----------|----------|---------|
| HighErrorRate | error_rate > 1% for 5m | critical | docs/runbooks/high-error-rate.md |
| HighLatency | p99 > 500ms for 10m | warning | docs/runbooks/high-latency.md |

---

## Dashboards

| Dashboard | Purpose | Key Metrics |
|-----------|---------|-------------|
| Service Overview | Health at a glance | Error rate, latency, throughput |
| Resource Utilization | Capacity planning | CPU, memory, connections |
| Business Metrics | Product KPIs | User actions, conversions |

---

## Integration Points

### Metrics Backend

- [ ] Prometheus / Datadog / CloudWatch
- [ ] Grafana dashboards

### Log Aggregation

- [ ] ELK / Loki / CloudWatch Logs
- [ ] Structured JSON logging

### Trace Collection

- [ ] OpenTelemetry / Jaeger / X-Ray
- [ ] Distributed trace context

---

## Notes

<!-- Observability planning notes -->
