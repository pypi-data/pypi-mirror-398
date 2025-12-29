# Epic 16: Enterprise Logging Integrations

**Goal**: Integrate with enterprise log aggregation and SIEM platforms (ELK Stack, Splunk, CloudWatch) for centralized logging and security monitoring.

**Value**: Enables enterprise adoption by fitting into existing logging infrastructure, supports compliance requirements, and provides centralized visibility.

**Priority**: High (Enterprise requirement)

---

## Story 16.1: ELK Stack Integration (Elasticsearch, Logstash, Kibana)

As a platform engineer,
I want logs shipped to Elasticsearch with Kibana dashboards,
So that I can search, analyze, and visualize logs in our centralized logging platform.

**Acceptance Criteria:**

**Given** ELK stack configured
**When** logs are shipped
**Then** logs are indexed in Elasticsearch with schema: index name "rabbitmq-mcp-{date}", document structure matches JSON log format

**And** shipping method: Filebeat (reads log files, ships to Elasticsearch), Logstash (parses logs, enriches, ships), direct shipping (via elasticsearch-py)

**And** Kibana dashboards provided: ./dashboards/kibana-rabbitmq-mcp.ndjson with visualizations (operation timeline, error rate, top operations, user activity)

**And** log retention: index lifecycle management (ILM) policy for 90-day retention

**And** search examples documented: find errors in last hour, trace by correlation_id, filter by operation/vhost

**And** alerting configured: Kibana Watcher alerts for high error rate, failed authentications

**And** integration guide: ./docs/LOGGING-ELK.md with setup instructions, Filebeat config, Kibana import

**Prerequisites:** Story 7.1 (structured logging), Story 7.4 (file logging)

**Technical Notes:**
- Filebeat config: inputs (log files), output (Elasticsearch), processors (add fields)
- Elasticsearch index template: define field mappings (correlation_id as keyword, timestamp as date)
- Kibana dashboards: visualizations (line chart for operations over time, bar chart for error types)
- ILM policy: hot (7 days) → warm (30 days) → cold (90 days) → delete
- Search queries: GET /rabbitmq-mcp-*/_search?q=level:ERROR AND timestamp:[now-1h TO now]
- Watcher alerts: trigger on: error_rate > 5% over 5 minutes
- Document: ELK installation, Filebeat setup, dashboard import, alert configuration

---

## Story 16.2: Splunk Integration

As an enterprise security team,
I want logs shipped to Splunk for security monitoring and compliance,
So that we can correlate RabbitMQ events with other security data.

**Acceptance Criteria:**

**Given** Splunk configured
**When** logs are shipped
**Then** logs are indexed in Splunk with sourcetype: rabbitmq:mcp, index: main or custom index

**And** shipping method: Splunk Universal Forwarder (monitors log files), HTTP Event Collector (HEC, direct HTTP POST), syslog (legacy)

**And** Splunk app provided: ./splunk-app/rabbitmq-mcp/ with dashboards, alerts, saved searches

**And** dashboards include: operations dashboard, security dashboard (auth failures, unauthorized access), performance dashboard (latency, throughput)

**And** alerts configured: failed authentication attempts (>5 in 10 min), high error rate (>10/min), suspicious activity

**And** search examples: index=main sourcetype=rabbitmq:mcp level=ERROR | stats count by operation

**And** field extraction: automatic extraction of structured fields (correlation_id, operation, user, vhost)

**And** integration guide: ./docs/LOGGING-SPLUNK.md with Forwarder setup, HEC configuration, app installation

**Prerequisites:** Story 7.1 (structured logging), Story 7.6 (audit trail)

**Technical Notes:**
- Universal Forwarder: monitors ./logs/ directory, forwards to Splunk indexers
- HEC: HTTP POST logs directly to Splunk: https://splunk.example.com:8088/services/collector
- Sourcetype config: props.conf defines field extraction (JSON auto-extraction)
- Splunk app: XML dashboards, savedsearches.conf for alerts
- Field aliases: map JSON fields to Splunk CIM (Common Information Model)
- Alerts: use correlation searches, send to PagerDuty/email/Slack
- Document: Splunk version requirements (8.x+), licensing (log volume), app install

---

## Story 16.3: AWS CloudWatch Integration

As a cloud engineer,
I want logs shipped to AWS CloudWatch,
So that we can monitor RabbitMQ MCP server in AWS environment with native tools.

**Acceptance Criteria:**

**Given** AWS CloudWatch configured
**When** logs are shipped
**Then** logs are sent to CloudWatch Logs with log group: /aws/rabbitmq-mcp, log stream: {instance-id}

**And** shipping method: CloudWatch agent (monitors log files), direct SDK (boto3), Lambda forwarder

**And** CloudWatch Insights queries provided: ./docs/cloudwatch-queries.txt with example queries

**And** CloudWatch dashboards: operations metrics, error rates, latency percentiles (using Insights queries)

**And** alarms configured: high error rate (>10 errors/5min), high latency (p95 >500ms), connection failures

**And** log retention: 30 days default (configurable via CloudWatch Logs retention setting)

**And** IAM permissions documented: logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents

**And** integration guide: ./docs/LOGGING-CLOUDWATCH.md with agent setup, IAM policy, alarm config

**Prerequisites:** Story 7.1 (structured logging)

**Technical Notes:**
- CloudWatch agent config: /opt/aws/amazon-cloudwatch-agent/etc/config.json
  ```json
  {
    "logs": {
      "logs_collected": {
        "files": {
          "collect_list": [{
            "file_path": "./logs/rabbitmq-mcp-*.log",
            "log_group_name": "/aws/rabbitmq-mcp",
            "log_stream_name": "{instance_id}"
          }]
        }
      }
    }
  }
  ```
- Direct logging: use watchtower library (Python CloudWatch handler)
- Insights queries: fields @timestamp, correlation_id, operation, level | filter level="ERROR" | stats count() by operation
- Alarms: use CloudWatch Metrics Filters → extract error count → alarm on threshold
- IAM policy: least privilege (logs:Put* only)
- Document: EC2/ECS/Lambda deployment, agent installation, cost optimization

---
