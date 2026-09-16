# Security

## MVP controls implemented

- Environment-based configuration (no hardcoded secrets)
- API key auth abstraction for future SSO/OIDC
- Path traversal protection for all file tools
- Sandbox execution abstraction with timeout and resource flags
- Default disabled sandbox networking in Docker mode
- Repository treated as untrusted input
- Explicit iteration limits and run timeout
- Agent cancellation endpoint
- Structured audit-style logging with request/session/run fields

## Remaining hardening for production

- Strong tenant isolation and per-user sandboxes
- Mandatory Docker sandbox execution in all environments
- Seccomp/AppArmor and rootless containers
- Output and prompt sanitization policies
- Full OIDC and RBAC integration
