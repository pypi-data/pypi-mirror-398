# Getting Started

This guide walks through installing, configuring, and running the CodeAny Hub MCP server.

## 1. Install Dependencies

1. Install Python 3.9+.
2. Install the CodeAny Hub SDK (pulled automatically as a dependency):
   ```bash
   pip install codeany-hub-mcp-server
````

## 2. Authenticate with CodeAny Hub

The MCP server uses the SDK’s credential loading. Provide **one** of the supported mechanisms:

| Method              | Environment variables                  | Notes                               |
| ------------------- | -------------------------------------- | ----------------------------------- |
| Personal API token  | `CODEANY_API_TOKEN`                    | Easiest for service accounts        |
| Username / password | `CODEANY_USERNAME`, `CODEANY_PASSWORD` | Supported by the SDK’s login flow   |
| Simple JWT          | `CODEANY_JWT`                          | JWT issued by the hub               |
| OAuth device code   | `CODEANY_DEVICE_CODE`                  | Use only if your flow provisions it |

Refer to the SDK README for more authentication options.

## 3. Configure the MCP Server

The server reads configuration from environment variables prefixed with `MCP_`. These do **not** overlap with the SDK’s
`CODEANY_*` settings, but both can be set simultaneously.

| Variable                           | Description                                                          | Default                 |
| ---------------------------------- | -------------------------------------------------------------------- | ----------------------- |
| `MCP_ASK_ON_START`                 | Prompt once per MCP session                                          | `true`                  |
| `MCP_ASK_ON_DESTRUCTIVE_OPS`       | Prompt before mutating actions                                       | `true`                  |
| `MCP_CONSENT_MESSAGE`              | Custom session consent text                                          | Built-in                |
| `MCP_DESTRUCTIVE_MESSAGE_TEMPLATE` | Template for destructive prompts (`{op_name}`, `{hub}` placeholders) | Built-in                |
| `MCP_TOKEN_STORE_MODE`             | `memory` or `file`                                                   | `memory`                |
| `MCP_TOKEN_STORE_PATH`             | File path for persistent tokens (required when mode=`file`)          | `None`                  |
| `MCP_HUB_ALLOWLIST`                | Comma-separated hub slugs allowed                                    | `None` (no restriction) |
| `MCP_MAX_UPLOAD_MB`                | Max upload size in MB for statement/testset data                     | `25`                    |
| `MCP_MAX_EXAMPLES`                 | Max examples stored per task                                         | `50`                    |
| `MCP_ALLOW_LOCAL_PATHS`            | Allow `upload_*` handlers to read local files                        | `false`                 |
| `MCP_RETRIES`                      | Forwarded to SDK retry policy                                        | `2`                     |
| `MCP_RETRY_BACKOFF`                | SDK retry backoff seconds                                            | `0.3`                   |
| `MCP_LOG_REQUESTS`                 | Enable SDK request logging                                           | `false`                 |
| `MCP_LOG_PATH`                     | File path used for server logs (`None` disables file logging)        | `codeany-hub-mcp.log`   |
| `MCP_LOG_LEVEL`                    | Logging verbosity (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`)  | `INFO`                  |

### Example `.env`

```bash
CODEANY_API_TOKEN=...
MCP_ASK_ON_START=true
MCP_TOKEN_STORE_MODE=file
MCP_TOKEN_STORE_PATH=/secure/codeany_tokens.json
MCP_HUB_ALLOWLIST=training,playground
MCP_MAX_UPLOAD_MB=50
MCP_LOG_PATH=/var/log/codeany-hub-mcp/server.log
MCP_LOG_LEVEL=INFO
```

## 4. Run the Server

```bash
codeany-hub-mcp
```

The CLI launches a stdio JSON-RPC loop. Integrate it with your MCP-compatible client by forwarding stdin/stdout. For
local experiments:

```bash
python examples/run_stdio.py
```

## 5. Prompts & Consent in Headless Environments

To avoid breaking the JSON-RPC transport, the server **never reads from STDIN** for prompts. It will:

* Use the controlling TTY when available (safe for CLI usage).
* In headless IDE/agent contexts:

  * **Auto-accept session consent** (so initialization and non-mutating tools work everywhere).
  * **Auto-reject destructive prompts.** For mutating tools (e.g., `tasks.delete`, `tasks.rename`, uploads), include
    `confirm=true` in the tool arguments to bypass the prompt, or disable destructive prompts with
    `MCP_ASK_ON_DESTRUCTIVE_OPS=false`.

Example destructive call:

```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "method": "tasks.delete",
  "params": { "hub": "playground", "task_id": "abc123", "confirm": true }
}
```

## 6. Next Steps

* Review [`docs/security.md`](security.md) for deployment considerations.
* Explore [`docs/tools-reference.md`](tools-reference.md) for per-tool parameters and return types.
* Check [`docs/streaming-and-uploads.md`](streaming-and-uploads.md) to understand streaming semantics for large
  payloads.
