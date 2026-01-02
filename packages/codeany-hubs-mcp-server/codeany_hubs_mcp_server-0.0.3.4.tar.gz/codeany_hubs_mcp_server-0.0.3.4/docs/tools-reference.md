# Tool Reference

This document describes every MCP tool exposed by `codeany-hub-mcp-server`,
including parameters, return shapes, and example payloads. All tools mirror the
official `codeany-hub` SDK (≥ 0.2.2.9) and support JSON-RPC transports via
`tools/call`.

- **Consent:** Session consent is enforced automatically. Destructive tools
  require either a user prompt or `confirm=true`.
- **Hubs:** All hub-scoped tools expect a hub slug (e.g., `awesome-hub`).
- **Errors:** Failures are normalized (see “Errors” at the end).

## Invocation Cheatsheet

```jsonc
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "tasks_list",
    "arguments": {
      "hub": "awesome-hub",
      "page": 1,
      "filters": { "query": "dp" }
    }
  }
}
```

`tools/list` / `tools.list` return the full catalog (with descriptions and
examples), while `tools.capabilities` provides sanitized names only.

Tool names appear in two equivalent forms:

- **Sanitized name** (e.g. `tasks_list`) – this is the `name` returned by `tools.list` / `tools.capabilities`.
- **Original dotted name** (e.g. `tasks.list`) – you can also pass this value as `name` to `tools/call`.

Some IDEs display labels such as `tasks_create (codeany-hubs MCP Server)`. When calling `tools/call`, use only the tool name (`tasks_create` or `tasks.create`), **without** the provider label or any extra text.

---

## Hubs

### `hubs.list_mine`
- **Purpose:** Discover every hub the authenticated user owns.
- **Parameters:** _(none)_
- **Returns:** Array of hub dicts (slug, display name, visibility, etc.)
- **Example args:** `{}`

### `hubs.detail`
- **Purpose:** Get metadata for a specific hub.
- **Parameters:** `hub`
- **Example args:** `{ "hub": "awesome-hub" }`

---

## Tasks – Core Lifecycle

### `tasks.create`
- **Purpose:** Create a task by delegating to the CodeAny Hub SDK’s `client.tasks.create`.
- **Parameters:**
  - `hub` (required): hub slug.
  - _All other fields_: forwarded unchanged as keyword arguments to `client.tasks.create`.
- **Important:** Do **not** invent fields (for example `name` or `task_type`) unless they are documented as valid parameters of `client.tasks.create` in the CodeAny Hub SDK. Otherwise you will see errors such as `TasksClient.create() got an unexpected keyword argument 'name'`.
- **CRITICAL:** Do **NOT** nest parameters inside a `payload` object. They must be top-level.
- **Returns:** The new task as a dict (SDK model serialized via `model_dump()`).
- **Example args (skeleton):**
  ```jsonc
  {
    "hub": "awesome-hub",
    "name": "My Task",   // Top-level!
    "time_limit": 1000,  // Top-level!
    "type": "batch",     // Top-level!
    "confirm": true
    // plus whatever fields the CodeAny Hub SDK documents for client.tasks.create(...)
  }
  ```

### `tasks.list`
- **Purpose:** Paginated task listing (supports `filters` such as `query`,
  `search`, `visibility`, `type`).
- **Parameters:** `hub`, optional `page`, `page_size`, `filters`.
- **Example args:** `{ "hub": "awesome-hub", "page": 1, "filters": { "query": "sum" } }`

### `tasks.delete`, `tasks.rename`, `tasks.toggle_visibility`
- **Purpose:** Mutate task metadata. All accept `confirm` to bypass prompts.
- **Example args (rename):**
  ```json
  {
    "hub": "awesome-hub",
    "task_id": 42,
    "name": "new-title",
    "confirm": true
  }
  ```

### `tasks.get_settings`
- **Purpose:** Retrieve the task settings blob (statements/testset options).

### `tasks.type.get` / `tasks.type.update`
- **Purpose:** Inspect or mutate the task type (batch/mcq/etc.).
- **Example args (update):**
  ```json
  { "hub": "awesome-hub", "task_id": 42, "payload": { "type": "mcq" }, "confirm": true }
  ```

## Tasks – MCQ

MCQ tools sit under `tasks.mcq.*` and map directly to the CodeAny SDK's `hubs.mcq` client. All handlers require a hub slug and task ID/slug referencing a Multiple Choice task (or one being converted).

### `tasks.mcq.get_config`
- **Purpose:** Fetch the full MCQ configuration (question text, options, flags).
- **Parameters:** `hub`, `task_id`.
- **Returns:** Serialized `MCConfig` (question, options, allow_multiple, shuffle options, metadata, etc.)
- **Example args:** `{ "hub": "awesome-hub", "task_id": 42 }`

### `tasks.mcq.replace_config`
- **Purpose:** Replace the entire MCQ configuration with a new `MCConfig` payload.
- **Parameters:** `hub`, `task_id`, `config` (dict matching `MCConfig`). Accepts `confirm=true` to skip destructive prompts.
- **Example args:**
  ```json
  {
    "hub": "awesome-hub",
    "task_id": 42,
    "config": {
      "question": "Which planet is known as the Red Planet?",
      "options": [
        { "id": "A", "text": "Mars", "is_correct": true },
        { "id": "B", "text": "Venus", "is_correct": false }
      ],
      "allow_multiple": false
    },
    "confirm": true
  }
  ```

### `tasks.mcq.patch_config`
- **Purpose:** Apply partial updates (via `MCPatch`) to the MCQ configuration without resending the full object.
- **Parameters:** `hub`, `task_id`, `patch` (dict containing fields to update), optional `confirm`.
- **Example args:** `{ "hub": "awesome-hub", "task_id": 42, "patch": { "question": "Updated question" }, "confirm": true }`

### `tasks.mcq.set_correct`
- **Purpose:** Update which option IDs count as correct answers.
- **Parameters:** `hub`, `task_id`, `correct_option_ids` (array of option IDs), optional `confirm`.
- **Returns:** Result payload from `set_correct` (typically success metadata).
- **Example args:** `{ "hub": "awesome-hub", "task_id": 42, "correct_option_ids": ["A"], "confirm": true }`

---

## Tasks – Limits

### `tasks.limits.get`
- **Purpose:** Fetch execution limits (`time_limit`, `memory_limit`).

### `tasks.limits.update`
- **Purpose:** Update execution limits (ms/MB). Provide `time_limit` and
  `memory_limit` either directly or inside `limits`.
- **Example args:** `{ "hub": "awesome-hub", "task_id": 42, "time_limit": 2000, "memory_limit": 256, "confirm": true }`

---

## Tasks – Statements

### `tasks.statements.get`
- **Purpose:** Retrieve statements (optionally per `language`). Accepts task
  ID or slug.

### `tasks.statements.list`
- **Purpose:** List available statement languages.

### `tasks.statements.create_lang`
- **Purpose:** Add a localized statement payload.
- **Example:** `{ "hub": "awesome-hub", "task_id": 42, "language": "en", "content": { ... }, "confirm": true }`

### `tasks.statements.delete_lang`
- **Purpose:** Remove statement content for a locale.

### `tasks.statements.update`
- **Purpose:** Invoke the SDK’s `update_statement`. Requires `statement_id`
  and a `payload` dict.
- **Example:** `{ "hub": "awesome-hub", "task_id": 42, "statement_id": 7, "payload": { "title": "Updated" }, "confirm": true }`

### `tasks.statements.upload_image`
- **Purpose:** Upload inline images (bytes, data URI, or local path if
  `MCP_ALLOW_LOCAL_PATHS=true`).

---

## Tasks – IO & Checker

### `tasks.io.get` / `tasks.io.update`
- **Purpose:** Retrieve/update IO + checker payload (input/output format,
  checker metadata).
- **Example (update):** `{ "hub": "awesome-hub", "task_id": 42, "io": { "input": "...", "checker": ... }, "confirm": true }`

### `tasks.checker.get`
- **Purpose:** Return checker metadata from the SDK’s `get_checker` endpoint
  (checker type, precision, custom code, etc.)

### `tasks.checker.update`
- **Purpose:** Update the checker via `update_checker`. `checker_type` is
  required. Supported built-ins:
  - `compare_lines_ignore_whitespaces.cpp`
  - `single_or_multiple_double_ignore_whitespaces.cpp`
  - `single_or_multiple_int64_ignore_whitespaces.cpp`
  - `single_or_multiple_yes_or_no_case_insensitive.cpp`
  - `single_yes_or_no_case_insensitive.cpp`
  - `custom_checker` (include `checker` source and optional
    `checker_language`, e.g., `cpp:20-clang13`)
- **Example:**  
  `{ "hub": "awesome-hub", "task_id": 42, "checker": { "checker_type": "custom_checker", "checker": "// C++", "checker_language": "cpp:20-clang13" }, "confirm": true }`

---

## Tasks – Testsets

### `tasks.testsets.list`
- **Purpose:** Paginated list of testsets. Defaults to `page=1`,
  `page_size=10` (clamped to a max of 50). Response includes the final
  `page`/`page_size`.
- **Example:** `{ "hub": "awesome-hub", "task_id": 42 }`

### `tasks.testsets.get`
- **Purpose:** Fetch testset metadata by `testset_id`.

### `tasks.testsets.create`
- **Purpose:** Create a new testset (optional `index`). Requires confirm.

### `tasks.testsets.update`
- **Purpose:** Call `client.tasks.update_testset`. Provide `update` with at
  least one field (e.g., `index`, `score`, `metadata`).
- **Example:** `{ "hub": "awesome-hub", "task_id": 42, "testset_id": 7, "update": { "index": 1 }, "confirm": true }`

### `tasks.testsets.delete`
- **Purpose:** Delete a testset (requires confirm).

### `tasks.testsets.upload_zip`
- **Purpose:** Upload a ZIP archive to a specific testset. Provide
  `testset_id`, `zip` bytes/data URI/path, and `stream` flag. When `stream=true`
  the handler yields SSE-style events; when `false` it returns the final event.
- **Example:** `{ "hub": "awesome-hub", "task_id": 42, "testset_id": 7, "zip": "data:application/zip;base64,...", "stream": true, "confirm": true }`

---

## Tasks – Tests

### `tasks.tests.get`
- **Purpose:** Retrieve a single testcase by `testset_id`/`index`.

### `tasks.tests.upload_single`
- **Purpose:** Use the SDK’s `upload_single_test`. Accepts byte blobs, data
  URIs, or file paths (`input_data`, `answer_data`) and optional
  `position` (defaults to `-1`).

### `tasks.tests.delete_one` / `tasks.tests.delete_many`
- **Purpose:** Remove testcases. `delete_many` accepts `indexes` array.

---

## Tasks – Examples

### `tasks.examples.get`
- **Purpose:** Fetch example IO sets.

### `tasks.examples.set`
- **Purpose:** Replace example sets. Provide `inputs`, `outputs`, or both.

### `tasks.examples.add`
- **Purpose:** Append a single example pair.

---

## Capabilities & Discovery

- **`tools.capabilities`** – sanitized names.
- **`tools.list` / `tools/list`** – detailed metadata (description + example
  args + sanitized/original names).
- **`tools/call`** – Execute any tool via sanitized name (`tasks_list`) or dotted name (`tasks.list`).

---

## Common Fields

- `hub`: Always a hub slug (allowlist enforced when configured).
- `task`, `task_id`: Accept string or integer. Some handlers resolve slugs to IDs (e.g., statements).
- `confirm`: Optional; required to skip destructive prompts.
- Upload parameters (`zip`, `input_data`, `answer_data`, `image`): Accept
  raw bytes, base64 data URIs, or file paths if `MCP_ALLOW_LOCAL_PATHS=true`.

---

## Errors

All unexpected exceptions are normalized via
`codeany_mcp_server.errors.to_mcp_error`. Typical payload:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Time limit must be positive",
    "data": { "status_code": 422 }
  }
}
```

Common `code` values:

- `consent_rejected`
- `hub_not_allowed`
- `not_found`
- `auth_error`
- `rate_limited`
- `validation_error`
- `api_error`
- `invalid_request`
- `internal_error`

For streaming handlers, errors may appear as `{ "error": {...} }` in the
iterator stream; clients should stop processing when encountered.
