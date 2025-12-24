"""Tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from basic_memory_hooks.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestConfigEndpoint:
    def test_get_config(self, client):
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "strictness" in data
        assert "note_types" in data


class TestValidateEndpoint:
    def test_validate_valid_note(self, client):
        note_content = """---
title: Test Note
type: memo
---

## Observations
- [fact] This is a fact
- [decision] This is a decision
- [technique] This is a technique

## Relations
- implements [[Feature A]]
"""
        response = client.post(
            "/validate",
            json={
                "content": note_content,
                "title": "Test Note",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "content" in data
        assert "errors" in data
        assert "warnings" in data

    def test_validate_with_stage(self, client):
        response = client.post(
            "/validate",
            json={
                "content": "---\ntitle: Test\ntype: memo\n---\n# Test",
                "title": "Test",
                "stage": "pre_write",
            },
        )
        assert response.status_code == 200

    def test_validate_invalid_stage(self, client):
        response = client.post(
            "/validate",
            json={
                "content": "# Test",
                "title": "Test",
                "stage": "invalid_stage",
            },
        )
        assert response.status_code == 400
        assert "Invalid stage" in response.json()["detail"]

    def test_validate_with_folder_and_project(self, client):
        response = client.post(
            "/validate",
            json={
                "content": "---\ntitle: Test\ntype: memo\n---\n# Test",
                "title": "Test",
                "folder": "notes",
                "project": "main",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_validate_missing_frontmatter(self, client):
        response = client.post(
            "/validate",
            json={
                "content": "# No frontmatter",
                "title": "Test",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # In balanced mode (default), errors become warnings
        assert len(data["warnings"]) > 0 or len(data["errors"]) > 0

    def test_validate_returns_modified_content(self, client):
        # Content with duplicate sections that should be fixed
        note_content = """---
title: Test
type: memo
---

## Observations
- [fact] First fact

## Observations
- [decision] Second observation
"""
        response = client.post(
            "/validate",
            json={
                "content": note_content,
                "title": "Test",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Content should be modified (duplicates removed/consolidated)
        assert data["content"].count("## Observations") == 1
