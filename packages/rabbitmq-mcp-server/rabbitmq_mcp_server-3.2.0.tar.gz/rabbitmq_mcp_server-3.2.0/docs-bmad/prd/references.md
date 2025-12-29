# References

## Source Documents

**Product Brief**: [`docs-bmad/brief/`](../brief/index.md)
- Executive summary and core vision
- Market context and competitive analysis
- Target users and success metrics
- Technical architecture overview
- Complete feature specifications (Features 001-008)
- Implementation tasks and data models

**RabbitMQ Management API Specification**: [`docs-bmad/rabbitmq-http-api-openapi.yaml`](../rabbitmq-http-api-openapi.yaml)
- Single source of truth for all HTTP operations
- ~4800 lines defining 100+ Management API operations
- Component schemas for request/response validation
- Foundation for OpenAPI-driven code generation

**Epic Breakdown**: [`docs-bmad/epics/`](../epics/index.md)
- Detailed story-level implementation breakdown
- Acceptance criteria for all 8 MVP epics
- FR coverage mapping to stories
- Phase 2 growth feature specifications

## External References

**Model Context Protocol (MCP)**:
- Specification: https://spec.modelcontextprotocol.io/
- GitHub: https://github.com/modelcontextprotocol
- Protocol version: 2024-11-05

**RabbitMQ Documentation**:
- Management HTTP API: https://www.rabbitmq.com/management.html
- AMQP 0-9-1 Protocol: https://www.rabbitmq.com/amqp-0-9-1-reference.html
- Management Plugin: https://www.rabbitmq.com/management-cli.html

**Technology Stack**:
- Python 3.12+: https://docs.python.org/3.12/
- Pydantic v2: https://docs.pydantic.dev/latest/
- sentence-transformers (all-MiniLM-L6-v2): https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- pika (AMQP client): https://pika.readthedocs.io/
- httpx (HTTP client): https://www.python-httpx.org/
- structlog (structured logging): https://www.structlog.org/

## Research & Market Analysis

**First-Mover Advantage**: No existing RabbitMQ MCP server as of Q4 2024
- MCP ecosystem growing rapidly (Anthropic, OpenAI adoption)
- DevOps automation via AI assistants emerging trend
- Infrastructure-as-conversation paradigm shift

**Innovation Validation**:
- 3-tool semantic discovery pattern (architectural innovation)
- OpenAPI-driven build-time generation (performance innovation)
- Zero context switching use case (UX innovation)
- Production security by default (enterprise innovation)

**Target Market Insights**:
- 50,000+ companies use RabbitMQ in production
- DevOps engineers average 15-20 context switches per incident
- AI-assisted operations adoption: 15% current, 60% projected by 2026

**Source Documents**:
- Product Brief: `docs-bmad/brief.md` (comprehensive greenfield specification)
- RabbitMQ HTTP API OpenAPI: `docs-bmad/rabbitmq-http-api-openapi.yaml`
- Workflow Status: `docs-bmad/bmm-workflow-status.yaml`

**Technical Specifications** (Detailed in Brief):
- Feature 001: Base MCP Architecture (73 tasks, 7 phases)
- Feature 002: Basic RabbitMQ Connection (12 tasks, 3 phases)
- Feature 003: Essential Topology Operations (22 tasks, 4 phases)
- Feature 004: Message Publishing and Consumption (18 tasks, 3 phases)
- Feature 005: Basic Console Client (14 tasks, 3 phases)
- Feature 006: Basic Testing Framework (17 tasks, 3 phases)
- Feature 007: Basic Structured Logging (53 tasks, 9 phases)
- Feature 008: MVP Documentation (comprehensive documentation components)

**External References**:
- Model Context Protocol (MCP) Specification: Anthropic
- RabbitMQ Management API Documentation
- AMQP 0-9-1 Protocol Specification
- OpenAPI 3.0 Specification
- JSON-RPC 2.0 Specification

---
