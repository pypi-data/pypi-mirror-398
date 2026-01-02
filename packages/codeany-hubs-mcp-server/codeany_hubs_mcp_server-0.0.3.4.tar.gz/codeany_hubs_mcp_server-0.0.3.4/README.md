## CodeAny Hubs MCP Server

This repository packages a Model Context Protocol (MCP) JSON-RPC server that exposes the full CodeAny Hub task
authoring surface area. It builds on the official `codeany-hub` Python SDK without modifying it, wiring in consent
policies, token storage rules, and per-tool routing so that IDE assistants can author and manage tasks securely.

### Features
- Session and destructive-action consent prompts with configurable messaging.
- Hub allowlist filtering and token store controls (memory or file-backed).
- Task CRUD, limits, statements, IO/checker, testsets, per-test management, and examples tools.
- Multiple Choice Question (MCQ) tooling to create/convert tasks and manage question configs directly from MCP clients.
- Streaming support for large uploads (e.g., ZIP testsets) with size enforcement.
- Drop-in CLI entrypoint `codeany-hubs-mcp` for stdio transports.
- **MCP-spec compatibility:** spec-compliant `initialize` (includes `protocolVersion`) and standard endpoints
  `tools/list` & `tools/call` (plus `prompts/list`, `resources/list` aliases).

## Quickstart

1. **Install the package**
   ```bash
   pip install codeany-hubs-mcp-server
   ```

2. **Set required environment**
   ```bash
   export CODEANY_API_TOKEN="your-codeany-hub-token"
   export MCP_ASK_ON_START=true
   export MCP_TOKEN_STORE_MODE=memory  # or 'file'
   ```
   The SDK also accepts other credential styles—`CODEANY_USERNAME`/`CODEANY_PASSWORD`, device codes, or JWTs. Use whichever
   combination you already rely on; the MCP server reuses the SDK's authentication logic.

3. **Run the MCP server**
   ```bash
   codeany-hubs-mcp
   ```

   The server listens on stdio. Pair it with your MCP-compatible client or IDE integration.

> Documentation for configuration flags, security posture, and tool schemas lives under `docs/`.

## Configuration

`MCPServerConfig` is loaded from environment variables prefixed with `MCP_`. Highlights:

| Variable | Description | Default |
| --- | --- | --- |
| `MCP_ASK_ON_START` | Prompt once per session for consent | `true` |
| `MCP_ASK_ON_DESTRUCTIVE_OPS` | Reconfirm before mutating actions | `true` |
| `MCP_TOKEN_STORE_MODE` | `memory` or `file` token persistence | `memory` |
| `MCP_TOKEN_STORE_PATH` | File path for tokens (required if mode=`file`) | `None` |
| `MCP_HUB_ALLOWLIST` | Comma separated hub slugs allowed | `None` (all) |
| `MCP_MAX_UPLOAD_MB` | Max upload size across tools | `25` |
| `MCP_MAX_EXAMPLES` | Cap on examples saved per task | `50` |
| `MCP_ALLOW_LOCAL_PATHS` | Permit reading local files for uploads | `false` |
| `MCP_NONINTERACTIVE_CONSENT` | Auto-answer session prompts when stdin isn't a TTY | `true` |
| `MCP_NONINTERACTIVE_CONSENT_DESTRUCTIVE` | Auto-answer destructive prompts when stdin isn't a TTY | `false` |
| `MCP_LOG_PATH` | File path for server logs (`None` to disable file logging) | `"codeany-hub-mcp.log"` |
| `MCP_LOG_LEVEL` | Logging verbosity (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`) | `INFO` |

Refer to `docs/getting-started.md` for the full list and examples.

## Tool Catalog

All handlers register under the following namespaces:

- `hubs.*` for discovery.
- `tasks.*` for task lifecycle, limits, statements, IO/checker, testsets, tests, and examples.
- `tasks.mcq.*` for Multiple Choice Question configuration (question text, options, correctness flags).
- `tools.capabilities` returns the above registry.
- Tools are exposed under both a sanitized name (for example `tasks_list`) and their original dotted name (for example `tasks.list`); `tools/call` accepts either form, but not UI decorations such as `tasks_create (codeany-hubs MCP Server)`.
- Many `tasks.*` tools, including `tasks.create`, are thin wrappers around the CodeAny Hub SDK. The MCP server forwards all arguments except `confirm` directly into SDK methods such as `client.tasks.create`. For these tools, consult the SDK docs for the full parameter list and avoid inventing new fields.

Each handler returns plain JSON dictionaries (obtained via `model_dump()` on SDK models). See
`docs/tools-reference.md` for parameter and result schemas.

## Development

Run linting and tests via:

```bash
scripts/run_tests.sh
```

The script runs Ruff, MyPy, and pytest. Tests rely on lightweight stubs instead of live HTTP calls to keep the suite
fast and deterministic.

### Development Checklist

- [ ] Install dev dependencies: `pip install -e '.[dev]'` (or update your active venv).
- [ ] Export/verify required env vars (`CODEANY_*`, `MCP_*`) or load from `.env`.
- [ ] Run `scripts/run_tests.sh` before pushing (Ruff → MyPy → pytest).
- [ ] Update docs when adding or changing tool signatures (`docs/tools-reference.md`).
- [ ] Validate security posture: consent prompts flow, `MCP_TOKEN_STORE_MODE` defaults to `memory`, no secrets committed, and logging redacts sensitive fields.
- [ ] Regenerate roadmap/status updates in `README.md` and `AGENTS.md` when milestones shift.
- [ ] For releases: bump version in `pyproject.toml`, tag, and publish to PyPI/registry.

## Roadmap & TODOs

- **Transport Options**  
  - Deliver a WebSocket gateway so IDEs can connect over persistent channels (target Q4 2024).  
  - Ship a reverse proxy recipe for MCP-over-HTTP to simplify remote deployments.
- **Schema & Tooling**  
  - Publish JSON Schema definitions for every tool payload (param/result) to unblock code generation.  
  - Add auto-generated OpenAPI-style docs mirroring the schema to aid documentation sites.
- **Testing & Quality**  
  - Stand up a mocked CodeAny Hub API harness for deterministic integration tests.  
  - Add contract tests ensuring server responses align with SDK model versions.  
  - Automate regression suites in CI (GitHub Actions) with matrix runs across Python 3.9-3.12.
- **Async & Performance**  
  - Expose async handler variants when the SDK’s async clients exit beta.  
  - Implement configurable concurrency limits and request queue metrics.
- **Deployment & Ops**  
  - Publish container images (`ghcr.io/codeany/codeany-hubs-mcp-server`) with baked-in health endpoints.  
  - Provide Terraform/Helm snippets for managed rollouts.  
  - Integrate structured logging (JSON) and optional OpenTelemetry exporters for tracing.

## Security Highlights

- Consent prompts are enforced centrally (`MCPAuthorizationGuard`).
- **Transport-safe prompts**: the server never reads from STDIN (which carries JSON-RPC). It uses the controlling TTY when available. In headless environments, session consent is auto-accepted and **destructive prompts are auto-rejected** (clients must pass `confirm=true`), preventing transport corruption and working reliably across IDEs.
- Token storage defaults to in-memory; file-backed storage must be explicitly configured.
- Upload helpers coerce data URIs, byte blobs, or (optionally) vetted local paths while enforcing size limits.
- No request bodies or secrets are logged unless `MCP_LOG_REQUESTS=true`, which only prints method/path/status.

### Logging & Diagnostics

- On startup, the server writes a readiness message to stderr indicating the active log destination.
- File logs default to `codeany-hub-mcp.log`; adjust via `MCP_LOG_PATH` or disable by setting it to an empty value.
- Set `MCP_LOG_LEVEL` to `DEBUG` when troubleshooting; leave at `INFO` in production.
- Router-level debug logs capture incoming requests and streaming progress while avoiding payload contents.

## IDE / Tool Integration

The MCP server communicates via stdio by default. Follow the platform-specific steps below to wire it into your tooling:

- **Codex CLI / VS Code (Codex extension)**  
  1. Ensure the package is installed in your project environment.  
  2. Add the following entry to your Codex configuration (`.codex/config.json` or settings UI):  
     ```json
     {
       "name": "codeany-hubs",
       "command": "codeany-hubs-mcp",
       "cwd": "/path/to/your/project",
       "env": {
         "CODEANY_API_TOKEN": "…",
         "MCP_TOKEN_STORE_MODE": "memory"
       }
     }
     ```  
  3. Restart Codex; the tool list should now include `codeany-hubs` under MCP providers.

- **Claude Code / Cursor**  
  1. Open the MCP server panel (`Claude → Settings → MCP Servers`).  
  2. Add a new server with command `codeany-hubs-mcp` and inherit your workspace environment.  
  3. For remote runs, point to a wrapper script that exports the required env vars before launching the server.  
  4. Save and reconnect; Claude Code will request consent via the prompt hook when first used.

- **Other MCP-compatible tools**  
  - Provide the executable (`codeany-hubs-mcp`) as the server command.  
  - Ensure stdin/stdout remain unbuffered (most frameworks handle this automatically).  
  - For GUI clients, implement the consent prompt callback to display the text passed from the server.

> Tip: keep a dedicated `.env` file with both `CODEANY_*` and `MCP_*` variables and load it before spawning the server to maintain consistent environments across tools.

**Non-interactive hosts (Cursor / Claude Code / JetBrains / others):** The server avoids reading prompts from **stdin** when it isn’t a TTY to preserve JSON‑RPC framing. Control answers via:
- `MCP_NONINTERACTIVE_CONSENT` (defaults to `true`) for session prompts.
- `MCP_NONINTERACTIVE_CONSENT_DESTRUCTIVE` (defaults to `false`) for destructive prompts.

For scripted/automated flows, prefer passing `confirm=true` on destructive tool calls to skip prompts entirely.

## MCP Usage Instructions for AI Agents

AI assistants that consume this MCP server should follow the same operating rules captured in `AGENTS.md`. In short:

1. **Always load the environment contract**  
   - Read `AGENTS.md` before issuing tool calls; it documents required env vars, consent expectations, and the full dev checklist.
   - Verify `CODEANY_*` credentials plus `MCP_*` toggles (token store mode, allowlist, upload limits) are set in the session.

2. **Respect consent + confirmation semantics**  
   - Invoke `guard.ensure_session_consent` once per session (the server does this automatically, but agents should surface prompts to users).  
   - Pass `confirm=true` for destructive tools when the operator already approved the action (delete, rename, update, etc.).

3. **Use documented tool schemas**  
   - Parameters and responses are defined in `docs/tools-reference.md`. Only send fields listed there; pass task references as slugs or IDs consistently.
   - For thin wrappers around the SDK (for example `tasks.create`), this MCP server does not reshape arguments: it calls the underlying SDK client (for `tasks.create` this is `client.tasks.create`) with your parameters, except that `confirm` is stripped before the call. Always use exactly the field names supported by the SDK and do not add extra top-level keys like `name` or `task_type` unless the SDK documents them.
   - Prefer `tasks.statements.update` for statement mutations (instead of legacy upsert calls); include `statement_id` and the desired payload.

4. **Handle errors deterministically**  
   - All failures surface structured `errors.to_mcp_error` payloads. Detect `consent_rejected`, `hub_not_allowed`, `validation_error`, etc., and relay actionable guidance to the user.

5. **Keep README and `AGENTS.md` in sync**  
   - If you edit the roadmap, checklist, or security posture for agent consumption, update both files so every AI client shares the same playbook.

Following these steps ensures any AI agent—Codex, Claude Code, Cursor, or future MCP clients—uses the server safely and consistently. Refer to `AGENTS.md` for the canonical format of responsibilities, checklists, and escalation procedures.

## Additional Resources

- [`docs/getting-started.md`](docs/getting-started.md)
- [`docs/security.md`](docs/security.md)
- [`docs/tools-reference.md`](docs/tools-reference.md)
- [`docs/streaming-and-uploads.md`](docs/streaming-and-uploads.md)
