# Security Model

The CodeAny Hub MCP server keeps application logic in the SDK and layers MCP-specific policies on top. This document
summarizes the core safeguards and provides recommendations for operators.

## Consent Controls

Consent prompts are enforced by `MCPAuthorizationGuard`. To protect the JSON-RPC stdio transport, the server **never
reads from STDIN** during prompts. Instead:

- If a controlling TTY is available, the server prompts on the TTY (POSIX: `/dev/tty`; Windows: console) without
  touching the JSON-RPC stream.
- In **headless** environments:
  - **Session consent** is auto-accepted so the server remains usable in IDEs/agents that do not support interactive prompts.
  - **Destructive prompts** are auto-rejected. Clients must pass `confirm=true` on mutating tools (e.g., `tasks.delete`)
    or disable the prompt for destructive ops via `MCP_ASK_ON_DESTRUCTIVE_OPS=false`.

Controls:

- **Session consent** (`MCP_ASK_ON_START`, default `true`): prompted once per process (accepted/rejected is cached).
- **Destructive consent** (`MCP_ASK_ON_DESTRUCTIVE_OPS`, default `true`): required for mutating actions unless the
  request includes `confirm=true`.

> Tip: For scripted pipelines, always include `confirm=true` on destructive calls to bypass interactive consent safely.

## Token Management

The server does **not** mint tokens, it only instructs the SDK which token store to use:

- `MCP_TOKEN_STORE_MODE=memory` (default) keeps tokens in process memory and clears them on restart.
- `MCP_TOKEN_STORE_MODE=file` requires `MCP_TOKEN_STORE_PATH`, enabling the SDK’s `FileTokenStore`.

Tokens never appear in logs. Even when `MCP_LOG_REQUESTS=true`, only HTTP method, path, and status are emitted.

## Hub Allowlist

`MCP_HUB_ALLOWLIST` constrains access to specific hub slugs. Attempts to operate on disallowed hubs fail fast before any
SDK call is executed.

Recommendations:

- Assign a dedicated token per environment (staging, production) and configure distinct MCP instances.
- Maintain separate allowlists for each deployment to enforce least-privilege access.

## Upload Safety

All upload handlers rely on `io_utils` helpers:

- Accepts bytes, bytearrays, data URIs, or **optional** local file paths (`MCP_ALLOW_LOCAL_PATHS=true`).
- Enforces `MCP_MAX_UPLOAD_MB` on every payload before sending to the SDK.
- Normalizes inputs for statement images, testset archives, and individual tests.

When `MCP_ALLOW_LOCAL_PATHS=false` (default), any path input results in `ValueError`.

## Logging and Telemetry

No body or token data is logged. To assist with debugging you may enable:

- `MCP_LOG_REQUESTS=true` to emit read-only request traces (method/path/status).
- External wrapper loggers around the MCP server process for audit trails.

## Concurrency

Router concurrency defaults to 8 via a semaphore in `Router.run_stdio()`. Tune this by instantiating `Router` manually
if your environment has different throughput requirements.

## Deployment Checklist

1. Store API tokens securely (environment secrets, vault, etc.).
2. Decide on token persistence mode (`memory` vs `file`) per deployment.
3. Configure hub allowlists to limit scope.
4. Review size limits for uploads; lower them if possible.
5. Confirm your MCP client presents destructive op confirmations (`confirm=true`) in headless mode.
6. Monitor process logs for `consent_rejected` or `hub_not_allowed` errors to detect policy enforcement.
