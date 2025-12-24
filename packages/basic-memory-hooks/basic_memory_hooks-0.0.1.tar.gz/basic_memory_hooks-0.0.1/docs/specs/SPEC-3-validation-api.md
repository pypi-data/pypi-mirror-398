# SPEC-3: Validation API

## Why

Not all AI platforms can execute Python directly. An HTTP API enables these platforms to use Basic Memory Hooks. The API is available:
- **Self-hosted**: FastAPI service users run themselves
- **Basic Memory Cloud**: Hosted endpoints for cloud users

## What

- FastAPI application in `basic_memory_hooks.api`
- Single validation endpoint
- Health check endpoint
- Config read from project (not passed in request)

## How (High Level)

### Endpoints

#### POST /hooks/validate

Validate note content against project configuration.

**Request:**
```json
{
  "content": "---\ntitle: My Note\ntype: note\n---\n\n# My Note\n...",
  "title": "My Note",
  "folder": "research",
  "project_id": "main",
  "stage": "pre_write"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | yes | Note markdown content |
| title | string | yes | Note title |
| folder | string | no | Target folder |
| project_id | string | no | Project identifier (Cloud only) |
| stage | string | no | `pre_write` (default) or `post_write` |

**Response (200):**
```json
{
  "success": true,
  "content": "---\ntitle: My Note\n...",
  "errors": [],
  "warnings": ["Missing section: ## Relations"],
  "hooks_run": ["validate_frontmatter", "format_observations"]
}
```

All valid requests return 200. Check `success` field for validation result.

**Response (400):**
```json
{
  "error": "Invalid request",
  "detail": "content field is required"
}
```

#### GET /health

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Error Codes

| Status | Meaning |
|--------|---------|
| 200 | Valid request (check `success` for validation result) |
| 400 | Malformed request |
| 401 | Unauthorized (Cloud: invalid token) |
| 404 | Project not found (Cloud) |
| 500 | Server error |

### Configuration

**Self-hosted:**

Config read from project path set via environment variable:

```bash
BASIC_MEMORY_PROJECT=/path/to/project uvicorn basic_memory_hooks.api:app --port 8080
```

The API reads `.basic-memory/format.md` from that path. If not found, uses defaults.

**Cloud:**

Config read from project storage via `project_id` parameter. Uses `read_content` internally to fetch `.basic-memory/format.md`.

### Authentication

**Self-hosted:** None. User controls network access.

**Cloud:** Bearer token in Authorization header.

```
Authorization: Bearer <basic-memory-api-token>
```

### Running the Service

```bash
pip install basic-memory-hooks

# Self-hosted
BASIC_MEMORY_PROJECT=/path/to/project uvicorn basic_memory_hooks.api:app --host 0.0.0.0 --port 8080

# Development
uvicorn basic_memory_hooks.api:app --reload
```

### OpenAPI Specification

Available at runtime:
- `/openapi.json` - JSON schema
- `/docs` - Swagger UI
- `/redoc` - ReDoc UI

## How to Evaluate

### Success Criteria
- [ ] POST /hooks/validate returns correct results
- [ ] 200 returned for all valid requests
- [ ] success=false when validation fails (strict mode)
- [ ] success=true with warnings (balanced mode)
- [ ] GET /health returns status
- [ ] Self-hosted reads config from BASIC_MEMORY_PROJECT
- [ ] Cloud reads config via project_id

### Test Cases
- Valid note passes validation
- Invalid note returns errors
- Missing format.md uses defaults
- Malformed JSON returns 400
- Cloud: invalid token returns 401
- Cloud: unknown project returns 404
