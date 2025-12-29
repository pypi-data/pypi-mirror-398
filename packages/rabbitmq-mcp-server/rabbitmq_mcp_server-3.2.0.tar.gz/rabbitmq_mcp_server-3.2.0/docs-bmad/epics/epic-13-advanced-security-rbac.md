# Epic 13: Advanced Security & RBAC

**Goal**: Implement enterprise-grade security features including OAuth2 authentication, role-based access control (RBAC), and enhanced audit logging for compliance.

**Value**: Enables enterprise adoption by meeting security requirements for large organizations, supports multi-tenant scenarios, and provides fine-grained access control.

**Priority**: High (Enterprise requirement)

---

## Story 13.1: OAuth2/OIDC Authentication

As a security engineer,
I want OAuth2/OpenID Connect authentication support,
So that users can authenticate with corporate identity providers (Azure AD, Okta, Auth0) instead of username/password.

**Acceptance Criteria:**

**Given** OAuth2 configuration with identity provider
**When** user authenticates
**Then** authentication uses OAuth2 authorization code flow with PKCE

**And** identity providers supported: Azure AD, Okta, Auth0, Google, generic OIDC

**And** configuration via environment: OAUTH_PROVIDER (azure/okta/auth0/oidc), OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_AUTHORITY, OAUTH_REDIRECT_URI

**And** token validation: verify signature, check expiration, validate issuer and audience

**And** token refresh: automatically refresh expired tokens using refresh token

**And** user info extracted from token: user_id, email, name, groups/roles

**And** fallback to basic auth: if OAuth not configured, use username/password

**And** authentication logged: {event: "auth_success", method: "oauth2", user: "user@example.com", provider: "azure"}

**Prerequisites:** Epic 2 complete (connection management)

**Technical Notes:**
- Use authlib library for OAuth2/OIDC: from authlib.integrations.httpx_client import OAuth2Client
- Authorization flow: redirect to provider → user consents → callback with code → exchange code for token
- PKCE (Proof Key for Code Exchange): code_verifier, code_challenge for security
- Token storage: secure storage (keyring), never log tokens
- JWT validation: use python-jose or PyJWT to verify token signatures
- Scopes: openid, profile, email
- Integration examples: ./docs/oauth-azure.md, ./docs/oauth-okta.md

---

## Story 13.2: Role-Based Access Control (RBAC)

As an administrator,
I want role-based access control to restrict operations by user roles,
So that I can enforce least-privilege principle and prevent unauthorized actions.

**Acceptance Criteria:**

**Given** RBAC configuration with roles and permissions
**When** user attempts operation
**Then** operation is authorized based on user's assigned roles

**And** built-in roles: admin (all permissions), operator (read/write queues/exchanges, no delete), viewer (read-only), auditor (audit logs only)

**And** custom roles supported: define in config file with permissions list

**And** permissions granularity: operation-level (queues.list, queues.create, queues.delete) or resource-level (queue:orders:delete)

**And** role assignment: users assigned roles via config, OAuth claims, or RabbitMQ user tags

**And** authorization check before operation execution: raises PermissionDenied error if unauthorized

**And** unauthorized attempts logged: {event: "authorization_denied", user: "user@example.com", operation: "queues.delete", required_permission: "queue:delete"}

**And** RBAC configuration: ./config/rbac.yaml with roles, permissions, user assignments

**Prerequisites:** Story 13.1 (OAuth2 authentication)

**Technical Notes:**
- RBAC config structure:
  ```yaml
  roles:
    admin:
      permissions: ["*"]
    operator:
      permissions: ["queues.*", "exchanges.*", "bindings.*", "!*.delete"]
    viewer:
      permissions: ["*.list", "*.get"]
  users:
    user@example.com: [operator]
  ```
- Permission check: @require_permission("queues.delete") decorator
- Wildcard matching: *.list matches queues.list, exchanges.list
- Negation: !*.delete excludes delete operations
- OAuth integration: extract roles from token claims (groups, roles)
- Cache permissions: avoid repeated config file reads

---
