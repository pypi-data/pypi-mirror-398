# Streaming & Upload Handling

Several tools deal with large payloads. This document explains how the MCP server orchestrates uploads and how
streaming responses are emitted.

## Input Formats

Upload handlers (`tasks.statements.upload_image`, `tasks.testsets.upload_zip`, `tasks.tests.upload_single`) accept the
following payload variants:

1. **Raw bytes** (preferred)
   ```json
   { "image": "base64-encoded via client" }
   ```
   Ensure your client sends raw bytes over JSON-RPC (most SDKs base64-encode automatically).

2. **Data URI strings**
   ```json
   {
     "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
   }
   ```

3. **Local file paths** (only when `MCP_ALLOW_LOCAL_PATHS=true`)
   ```json
   { "zip": "/absolute/path/to/tests.zip" }
   ```
   The server reads the file, enforces size limits, and streams the bytes to the CodeAny API.

All payloads are normalized by `io_utils.coerce_bytes_or_path` and validated by `io_utils.enforce_size_limit`.

## Size Limits

- `MCP_MAX_UPLOAD_MB` controls the maximum size for any single payload.
- Size checks happen before SDK calls, preventing unnecessary network requests.
- Exceeding the limit yields an `invalid_request` error.

## Streaming Responses

`tasks.testsets.upload_zip` supports streaming progress events:

```json
// partial response
{"jsonrpc":"2.0","id":42,"result":{"event":{"status":"processing"}},"partial":true}

// another partial
{"jsonrpc":"2.0","id":42,"result":{"event":{"status":"done"}},"partial":true}

// final sentinel (no payload)
{"jsonrpc":"2.0","id":42,"result":null}
```

### Client Guidance

1. Treat any response with `partial=true` as an in-flight update.
2. Stop listening after the final message without `partial`.
3. Individual events reflect the SDK’s streaming objects; their payloads match what the SDK exposes (converted via
   `.model_dump()` when available).

If the request declares `"stream": false`, the handler buffers the SDK response and returns a single terminal result.

## Error Propagation

Any exception raised mid-stream is converted into:

```json
{"jsonrpc":"2.0","id":42,"error":{"code":"validation_error","message":"..."}}
```

No additional terminal message is sent after an error payload.

## Upload Recommendations

- Use streaming (`stream=true`) for large ZIP archives to avoid buffering.
- Always supply filenames for better diagnostics on the CodeAny side.
- Combine `confirm=true` with scripted pipelines to bypass manual prompts when safe.
