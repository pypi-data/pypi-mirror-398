# Target Users

## Primary Users: DevOps Engineers & SREs

**Profile**: 
- Manage 3-10 RabbitMQ clusters across dev/staging/prod environments
- Daily operations: monitor queue depths, troubleshoot message flow, manage topology
- Technical proficiency: Comfortable with CLI tools, API calls, infrastructure-as-code
- Pain points: Constantly switching between terminals, browsers, and documentation

**Current Behavior**:
- Starts day checking RabbitMQ Management UI dashboards (browser)
- Responds to alerts by SSH-ing to servers, running `rabbitmqctl` commands (terminal)
- Troubleshoots issues by crafting curl commands to Management API (terminal + docs)
- Shares findings in Slack/Teams (chat tool)

**Desired Experience**:
"I want to stay in my AI assistant conversation (Claude/ChatGPT) and ask natural questions like 'which queues have no consumers?' without switching to browser or memorizing API endpoints. When I need to purge a queue or create a binding, I want the AI to handle the API call with safety validations built-in."

**Value Delivered**:
- 80% reduction in context-switching during incident response
- Natural language operations replace API reference lookups
- Built-in safety validations prevent mistakes under pressure
- Audit trail for compliance without manual logging

## Secondary Users: Backend Developers (Development Environment)

**Profile**:
- Build microservices that use RabbitMQ for async communication
- Occasional RabbitMQ operations during local development and debugging
- Technical proficiency: Strong in application code, moderate infrastructure knowledge
- Pain points: RabbitMQ setup and troubleshooting takes time away from feature development

**Current Behavior**:
- Runs local RabbitMQ in Docker for development
- Uses Management UI to check if messages are flowing (browser)
- Googles RabbitMQ commands when something breaks (docs)
- Asks DevOps for help with complex topology issues (Slack)

**Desired Experience**:
"During development, I want my AI coding assistant (Cursor, GitHub Copilot) to help me verify message flow without leaving my IDE. If messages aren't being consumed, the AI should diagnose the issue (bindings missing? consumer down?) without me learning RabbitMQ internals."

**Value Delivered**:
- Faster local debugging (stay in IDE + AI assistant)
- Self-service problem solving reduces DevOps dependencies
- Learning through AI explanation (builds RabbitMQ knowledge over time)

## Tertiary Users: Platform Engineers (Internal Developer Platforms)

**Profile**:
- Build internal platforms that abstract RabbitMQ complexity for product teams
- Automate RabbitMQ provisioning, monitoring, and operations
- Technical proficiency: Infrastructure experts, API integration specialists
- Pain points: Building and maintaining custom tooling around RabbitMQ API

**Current Behavior**:
- Writes Python/Go scripts wrapping RabbitMQ Management API
- Maintains custom CLI tools for common operations
- Builds Terraform providers or Kubernetes operators for RabbitMQ
- Documents internal APIs and runbooks

**Desired Experience**:
"I want to provide our product teams with AI-assisted RabbitMQ access that follows our governance policies. MCP server becomes a platform primitive that we can embed in our internal tools, extending it with custom operations and organization-specific validations."

**Value Delivered**:
- Reduces custom API wrapper maintenance (reuse MCP server instead)
- Extensible architecture for platform-specific customizations
- Centralized audit logging for governance
- Faster platform feature delivery (leverage MCP ecosystem)

---
