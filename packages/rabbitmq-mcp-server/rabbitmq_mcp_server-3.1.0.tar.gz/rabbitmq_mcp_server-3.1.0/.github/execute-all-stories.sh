#!/bin/bash

# Shell script to execute all epic stories and tasks using GitHub Copilot CLI
# Non-dev tasks use: bmad-agent-bmm-sm
# Dev tasks use: bmad-agent-bmm-dev
# Model: claude-sonnet-4.5

set -e  # Exit on error

# Parse command line arguments
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No commands will be executed"
    echo ""
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to execute SM (non-dev) tasks
execute_sm_task() {
    local task="$1"
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${CYAN}[SM] Would execute: ${task}${NC}"
        echo -e "${CYAN}    Command: copilot --prompt \"${task}\" --allow-all-tools --allow-all-paths --agent \"bmad-agent-bmm-sm\" --model claude-sonnet-4.5${NC}\n"
    else
        echo -e "${BLUE}[SM] Executing: ${task}${NC}"
        copilot --prompt "${task}" --allow-all-tools --allow-all-paths --agent "bmad-agent-bmm-sm" --model claude-sonnet-4.5
        echo -e "${GREEN}[SM] Completed: ${task}${NC}\n"
    fi
}

# Function to execute DEV (development) tasks
execute_dev_task() {
    local task="$1"
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${CYAN}[DEV] Would execute: ${task}${NC}"
        echo -e "${CYAN}    Command: copilot --prompt \"${task}\" --allow-all-tools --allow-all-paths --agent \"bmad-agent-bmm-dev\" --model claude-sonnet-4.5${NC}\n"
    else
        echo -e "${YELLOW}[DEV] Executing: ${task}${NC}"
        copilot --prompt "${task}" --allow-all-tools --allow-all-paths --agent "bmad-agent-bmm-dev" --model claude-sonnet-4.5
        echo -e "${GREEN}[DEV] Completed: ${task}${NC}\n"
    fi
}

# Function to execute epic workflow
execute_epic() {
    local epic_num="$1"

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}STARTING EPIC ${epic_num}${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    execute_sm_task "4. epic-tech-context epic-${epic_num}"
    execute_sm_task "5. validate-epic-tech-context epic-${epic_num}. If any issues, gaps or recommendations found, fix them all using best judgement and/or most commonly option used in such scenario and app type (spotify mcp server). Assure fixes do not introduce new issues or gaps or recommendations."

    # Commit after validate-epic-tech-context
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${CYAN}Would run: git add -A${NC}"
        echo -e "${CYAN}Would run: git commit -m \"chore(epic-${epic_num}): validate epic tech context\"${NC}\n"
    else
        git add -A
        git commit -m "chore(epic-${epic_num}): validate epic tech context" || true
    fi
}

# Function to execute story workflow
execute_story() {
    local story_id="$1"

    echo -e "${GREEN}----------------------------------------${NC}"
    echo -e "${GREEN}PROCESSING STORY: ${story_id}${NC}"
    echo -e "${GREEN}----------------------------------------${NC}\n"

    # SM Tasks
    execute_sm_task "6. create-story ${story_id}"
    execute_sm_task "7. validate-create-story ${story_id}. If any issues, gaps or recommendations found, fix them all using best judgement and/or most commonly option used in such scenario and app type (spotify mcp server). Assure fixes do not introduce new issues or gaps or recommendations."
    execute_sm_task "8. create story context ${story_id}"
    execute_sm_task "9. validate-story-context ${story_id}. If any issues, gaps or recommendations found, fix them all using best judgement and/or most commonly option used in such scenario and app type (spotify mcp server). Assure fixes do not introduce new issues or gaps or recommendations."
    execute_sm_task "10. set story-ready-for-dev ${story_id}"

    # DEV Tasks
    execute_dev_task "3. develop-story ${story_id}. Complete all tasks, do not skip any task."
    execute_dev_task "5. code-review ${story_id} If any issues, gaps or recommendations found, fix them all using best judgement and/or most commonly option used in such scenario and app type (spotify mcp server). Assure fixes do not introduce new issues or gaps or recommendations."
    execute_dev_task "4. story-done ${story_id}"

    # Commit after story-done
    local story_short=$(echo "$story_id" | sed 's/-/./' | cut -d'-' -f1)
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${CYAN}Would run: git add -A${NC}"
        echo -e "${CYAN}Would run: git commit -m \"chore(story-${story_short}): complete story\"${NC}\n"
    else
        git add -A
        git commit -m "chore(story-${story_short}): complete story" || true
    fi
}

# Function to execute epic retrospective
execute_epic_retrospective() {
    local epic_num="$1"

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}EPIC ${epic_num} RETROSPECTIVE${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    execute_sm_task "11. epic-retrospective epic-${epic_num}. Use dev notes. It says it all."

    # Commit after epic-retrospective
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${CYAN}Would run: git add -A${NC}"
        echo -e "${CYAN}Would run: git commit -m \"chore(epic-${epic_num}): complete epic retrospective\"${NC}\n"
    else
        git add -A
        git commit -m "chore(epic-${epic_num}): complete epic retrospective" || true
    fi

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}EPIC ${epic_num} COMPLETED${NC}"
    echo -e "${GREEN}========================================${NC}\n\n"
}

# MAIN EXECUTION
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  RabbitMQ MCP Server - Complete Story Execution Pipeline      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}\n"

# ============================================================================
# PHASE 1: FOUNDATION & MVP
# ============================================================================

echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║                    PHASE 1: FOUNDATION & MVP                   ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}\n"

# EPIC 1: Foundation & MCP Protocol
#execute_epic "1"
#execute_story "1-1-project-setup-repository-structure"
execute_story "1-2-development-quality-tools-cicd-pipeline"
execute_story "1-3-openapi-specification-integration"
execute_story "1-4-pydantic-schema-generation"
execute_story "1-5-operation-registry-generation"
execute_story "1-6-semantic-embeddings-generation"
execute_story "1-7-mcp-server-foundation-json-rpc-20"
execute_story "1-8-search-ids-tool-implementation"
execute_story "1-9-get-id-tool-implementation"
execute_story "1-10-call-id-tool-implementation-http-operations"
execute_story "1-11-multi-version-api-support"
execute_epic_retrospective "1"

# EPIC 2: Connection Management & Authentication
execute_epic "2"
execute_story "2-1-configuration-management-system"
execute_story "2-2-amqp-connection-establishment"
execute_story "2-3-http-management-api-client"
execute_story "2-4-connection-health-checks"
execute_story "2-5-automatic-reconnection-with-exponential-backoff"
execute_story "2-6-connection-pooling-for-http-with-cache-invalidation-strategy"
execute_story "2-7-tlsssl-certificate-handling"
execute_epic_retrospective "2"

# EPIC 3: Topology Management
execute_epic "3"
execute_story "3-1-list-queues-operation"
execute_story "3-2-create-queue-operation"
execute_story "3-3-delete-queue-operation-with-safety-validation"
execute_story "3-4-purge-queue-operation"
execute_story "3-5-list-exchanges-operation"
execute_story "3-6-create-exchange-operation"
execute_story "3-7-delete-exchange-operation-with-protection"
execute_story "3-8-list-bindings-operation"
execute_story "3-9-create-binding-operation"
execute_story "3-10-delete-binding-operation"
execute_story "3-11-vhost-validation-middleware"
execute_epic_retrospective "3"

# EPIC 4: Message Operations
execute_epic "4"
execute_story "4-1-publish-message-to-exchange"
execute_story "4-2-consume-messages-from-queue"
execute_story "4-3-acknowledge-messages-acknackreject"
execute_story "4-4-message-property-validation"
execute_story "4-5-payload-size-limits-and-validation"
execute_story "4-6-consumer-lifecycle-management"
execute_story "4-7-message-routing-validation-pre-publish"
execute_story "4-8-amqp-operation-schemas-manual"
execute_epic_retrospective "4"

# EPIC 5: CLI Interface
execute_epic "5"
execute_story "5-1-cli-command-structure-argument-parsing"
execute_story "5-2-queue-management-commands"
execute_story "5-3-exchange-management-commands"
execute_story "5-4-binding-management-commands"
execute_story "5-5-message-publishing-command"
execute_story "5-6-message-consumption-command"
execute_story "5-7-connection-health-check-command"
execute_story "5-8-rich-terminal-output-formatting"
execute_story "5-9-help-system-examples"
execute_epic_retrospective "5"

# EPIC 6: Testing Infrastructure
execute_epic "6"
execute_story "6-1-test-infrastructure-setup"
execute_story "6-2-unit-tests-for-mcp-tools"
execute_story "6-3-unit-tests-for-rabbitmq-operations"
execute_story "6-4-integration-tests-with-real-rabbitmq"
execute_story "6-5-contract-tests-for-mcp-protocol-compliance"
execute_story "6-6-performance-tests-benchmarks"
execute_story "6-7-test-coverage-reporting-quality-gates"
execute_story "6-8-test-data-fixtures-factories"
execute_epic_retrospective "6"

# EPIC 7: Observability & Security
execute_epic "7"
execute_story "7-1-structured-logging-foundation-structlog-integration"
execute_story "7-2-structured-logging-configuration-output"
execute_story "7-3-correlation-id-tracking"
execute_story "7-4-automatic-sensitive-data-sanitization"
execute_story "7-5-file-based-logging-with-daily-rotation"
execute_story "7-6-logging-performance-optimization"
execute_story "7-7-audit-trail-for-operations"
execute_story "7-8-opentelemetry-instrumentation"
execute_story "7-9-rate-limiting-implementation"
execute_story "7-10-security-logging-monitoring"
execute_story "7-11-log-aggregation-search"
execute_epic_retrospective "7"

# EPIC 8: Documentation & Release
execute_epic "8"
execute_story "8-1-readme-with-quick-start"
execute_story "8-2-api-reference-documentation"
execute_story "8-3-architecture-documentation"
execute_story "8-4-usage-examples-tutorials"
execute_story "8-5-contributing-guide"
execute_story "8-6-changelog-release-notes"
execute_story "8-7-security-compliance-documentation"
execute_story "8-8-performance-tuning-guide"
execute_story "8-9-license-legal-documentation"
execute_story "8-10-release-preparation-publishing"
execute_epic_retrospective "8"

# ============================================================================
# PHASE 2: GROWTH FEATURES
# ============================================================================

echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║                   PHASE 2: GROWTH FEATURES                     ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}\n"

# EPIC 9: Advanced Search & Discovery
execute_epic "9"
execute_story "9-1-sqlite-vec-integration"
execute_story "9-2-incremental-embedding-updates"
execute_epic_retrospective "9"

# EPIC 10: Advanced Retry & Dead Letter Queue (DLQ) Patterns
execute_epic "10"
execute_story "10-1-exponential-backoff-retry-for-message-publishing"
execute_story "10-2-dead-letter-exchange-dlx-configuration-monitoring"
execute_epic_retrospective "10"

# EPIC 11: Configuration Import/Export
execute_epic "11"
execute_story "11-1-export-topology-to-yamljson"
execute_story "11-2-import-topology-from-yamljson"
execute_epic_retrospective "11"

# EPIC 12: Monitoring & Metrics Dashboards
execute_epic "12"
execute_story "12-1-prometheus-metrics-exporter"
execute_story "12-2-grafana-dashboard-templates"
execute_epic_retrospective "12"

# EPIC 13: Advanced Authentication
execute_epic "13"
execute_story "13-1-oauth2oidc-authentication"
execute_story "13-2-role-based-access-control-rbac"
execute_epic_retrospective "13"

# EPIC 14: Multi-Language Support
execute_epic "14"
execute_story "14-1-i18n-framework-integration"
execute_epic_retrospective "14"

# EPIC 15: Enhanced Testing
execute_epic "15"
execute_story "15-1-performance-load-testing-suite"
execute_story "15-2-chaos-engineering-tests"
execute_story "15-3-security-testing-vulnerability-scanning"
execute_epic_retrospective "15"

# EPIC 16: Enterprise Integrations
execute_epic "16"
execute_story "16-1-elk-stack-integration-elasticsearch-logstash-kibana"
execute_story "16-2-splunk-integration"
execute_story "16-3-aws-cloudwatch-integration"
execute_epic_retrospective "16"

# EPIC 17: Performance Optimization
execute_epic "17"
execute_story "17-1-advanced-caching-strategies"
execute_story "17-2-connection-pool-optimization"
execute_story "17-3-query-optimization-batch-operations"
execute_epic_retrospective "17"

# EPIC 18: Advanced Messaging Features
execute_epic "18"
execute_story "18-1-delayed-message-publishing"
execute_story "18-2-message-priority-queues"
execute_story "18-3-message-ttl-time-to-live"
execute_epic_retrospective "18"

# EPIC 19: Community & Learning Resources
execute_epic "19"
execute_story "19-1-video-tutorial-series"
execute_story "19-2-interactive-documentation-with-live-examples"
execute_story "19-3-api-cookbook-recipes"
execute_epic_retrospective "19"

# EPIC 20: DevOps & Automation
execute_epic "20"
execute_story "20-1-github-actions-workflow-orchestration"
execute_story "20-2-semantic-release-automation"
execute_story "20-3-quality-dashboard-metrics-tracking"
execute_epic_retrospective "20"

# ============================================================================
if [[ "$DRY_RUN" == true ]]; then
    echo -e "${CYAN}DRY RUN completed - no commands were executed${NC}"
else
    echo -e "${GREEN}Project execution pipeline completed successfully!${NC}"
fi
# ============================================================================

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ALL EPICS AND STORIES COMPLETED!                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}Summary:${NC}"
echo -e "  • Phase 1 (Foundation & MVP): Epics 1-8"
echo -e "  • Phase 2 (Growth Features): Epics 9-20"
echo -e "  • Total Epics: 20"
echo -e "  • Agent SM: Non-dev tasks (planning, validation, retrospectives)"
echo -e "  • Agent DEV: Development tasks (coding, code reviews)"
echo -e "  • Model: claude-sonnet-4.5\n"

echo -e "${GREEN}Project execution pipeline completed successfully!${NC}"
