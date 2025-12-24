"""FastAPI application for Basic Memory Hooks validation API."""

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from basic_memory_hooks.engine import HookEngine
from basic_memory_hooks.types import HookStage

app = FastAPI(
    title="Basic Memory Hooks",
    description="Validation and formatting API for Basic Memory notes",
    version="0.1.0",
)


class ValidateRequest(BaseModel):
    """Request body for /validate endpoint."""

    content: str
    title: str
    folder: str | None = None
    project: str | None = None
    stage: str = "pre_write"


class ValidateResponse(BaseModel):
    """Response body for /validate endpoint."""

    success: bool
    content: str
    errors: list[str]
    warnings: list[str]
    metadata: dict[str, Any]


def get_format_config_path() -> Path | None:
    """Get path to format.md config file.

    Checks BASIC_MEMORY_PROJECT env var for project root.
    """
    project_root = os.environ.get("BASIC_MEMORY_PROJECT")
    if project_root:
        config_path = Path(project_root) / ".basic-memory" / "format.md"
        if config_path.exists():
            return config_path
    return None


def create_engine() -> HookEngine:
    """Create and configure a HookEngine instance."""
    engine = HookEngine()

    config_path = get_format_config_path()
    if config_path:
        engine.load_config(config_path)
    else:
        # Use defaults - register standard hooks with default config
        engine._register_standard_hooks()

    return engine


@app.post("/validate", response_model=ValidateResponse)
async def validate(request: ValidateRequest) -> ValidateResponse:
    """Validate and optionally format note content.

    Runs all configured hooks for the specified stage.
    Returns validation results with optionally modified content.
    """
    # Map stage string to enum
    stage_map = {
        "pre_write": HookStage.PRE_WRITE,
        "post_write": HookStage.POST_WRITE,
        "pre_edit": HookStage.PRE_EDIT,
        "post_edit": HookStage.POST_EDIT,
    }

    stage = stage_map.get(request.stage)
    if stage is None:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage: {request.stage}. Must be one of: {list(stage_map.keys())}",
        )

    engine = create_engine()

    result = engine.run(
        stage=stage,
        content=request.content,
        title=request.title,
        folder=request.folder,
        project=request.project,
    )

    return ValidateResponse(
        success=result.success,
        content=result.content if result.content is not None else request.content,
        errors=result.errors,
        warnings=result.warnings,
        metadata=result.metadata,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/config")
async def get_config() -> dict[str, Any]:
    """Get current configuration.

    Returns the loaded configuration or defaults if no config file found.
    """
    engine = create_engine()
    config = engine.config

    return {
        "version": config.version,
        "strictness": config.strictness,
        "note_types": {
            "default": config.note_types.default,
            "allowed": config.note_types.allowed,
        },
        "observation_categories": {
            "required": config.observation_categories.required,
            "optional": config.observation_categories.optional,
        },
        "tag_taxonomy": {
            "enforce": config.tag_taxonomy.enforce,
            "prefixes": config.tag_taxonomy.prefixes,
        },
        "relation_types": {
            "primary": config.relation_types.primary,
            "secondary": config.relation_types.secondary,
        },
        "quality": {
            "minimum_observations": config.quality.minimum_observations,
            "minimum_relations": config.quality.minimum_relations,
            "require_tags": config.quality.require_tags,
            "require_frontmatter": config.quality.require_frontmatter,
            "allow_forward_references": config.quality.allow_forward_references,
            "auto_fix": config.quality.auto_fix,
        },
        "config_loaded": get_format_config_path() is not None,
    }
