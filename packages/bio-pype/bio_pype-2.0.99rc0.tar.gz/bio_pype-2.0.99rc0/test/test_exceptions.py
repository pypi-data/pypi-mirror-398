"""Tests for the exceptions module."""

import pytest
from pype.exceptions import (
    PypeError, PipelineError, PipelineVersionError, PipelineItemError,
    SnippetError, SnippetNotFoundError, SnippetExecutionError,
    ArgumentError, BatchArgumentError, ProfileError,
    CommandError, CommandNamespaceError, EnvModulesError
)

def test_pype_error_basic():
    """Test basic PypeError functionality."""
    error = PypeError("test message", {"key": "value"})
    assert str(error) == "test message"
    assert error.context == {"key": "value"}
    assert isinstance(error, Exception)

def test_pipeline_error():
    """Test PipelineError with context."""
    error = PipelineError("failed", pipeline_name="test_pipe", extra="info")
    assert "Pipeline error: failed" in str(error)
    assert error.context["pipeline_name"] == "test_pipe"
    assert error.context["extra"] == "info"

def test_pipeline_version_error():
    """Test PipelineVersionError formatting."""
    error = PipelineVersionError("2.0.0", "1.0.0", "test_pipe")
    assert "Version mismatch: 2.0.0 != 1.0.0" in str(error)
    assert error.context["current_version"] == "2.0.0"
    assert error.context["required_version"] == "1.0.0"

def test_pipeline_item_error():
    """Test PipelineItemError construction."""
    error = PipelineItemError(
        "execution failed",
        item_name="item1",
        item_type="snippet",
        pipeline_name="pipe1"
    )
    assert "Error in snippet 'item1'" in str(error)
    assert error.context["item_name"] == "item1"
    assert error.context["item_type"] == "snippet"

def test_snippet_errors():
    """Test snippet-related errors."""
    # Basic SnippetError
    error = SnippetError("failed", snippet_name="test_snip")
    assert "Snippet error: failed" in str(error)
    assert error.context["snippet_name"] == "test_snip"

    # SnippetNotFoundError
    error = SnippetNotFoundError("missing_snip")
    assert "Snippet 'missing_snip' not found" in str(error)
    assert error.context["snippet_name"] == "missing_snip"

    # SnippetExecutionError
    error = SnippetExecutionError(
        "execution failed",
        snippet_name="failed_snip",
        exit_code=1
    )
    assert error.context["exit_code"] == 1
    assert error.context["snippet_name"] == "failed_snip"

def test_argument_errors():
    """Test argument-related errors."""
    # Basic ArgumentError
    error = ArgumentError("invalid value", argument="--test")
    assert "Argument error: invalid value" in str(error)
    assert error.context["argument"] == "--test"

    # BatchArgumentError
    error = BatchArgumentError("parsing failed", batch_file="test.txt")
    assert error.context["batch_file"] == "test.txt"

def test_profile_error():
    """Test ProfileError construction."""
    error = ProfileError(
        "invalid config",
        profile_name="test_profile",
        detail="missing field"
    )
    assert "Profile error: invalid config" in str(error)
    assert error.context["profile_name"] == "test_profile"
    assert error.context["detail"] == "missing field"

def test_command_errors():
    """Test command-related errors."""
    # Basic CommandError
    error = CommandError(
        "execution failed",
        command="test_cmd",
        exit_code=1
    )
    assert "Command error: execution failed" in str(error)
    assert error.context["command"] == "test_cmd"
    assert error.context["exit_code"] == 1

    # CommandNamespaceError
    error = CommandNamespaceError("invalid namespace", command="test_ns")
    assert error.context["command"] == "test_ns"

def test_env_modules_error():
    """Test EnvModulesError construction."""
    error = EnvModulesError("module not found", module_name="test_module")
    assert "Environment module error: module not found" in str(error)
    assert error.context["module_name"] == "test_module"

def test_error_inheritance():
    """Test exception inheritance chain."""
    error = PipelineError("test")
    assert isinstance(error, PypeError)
    assert isinstance(error, Exception)

    error = SnippetNotFoundError("test")
    assert isinstance(error, SnippetError)
    assert isinstance(error, PypeError)

def test_error_without_context():
    """Test errors created without context."""
    error = PypeError("test")
    assert error.context == {}

    error = PipelineError("test")
    assert error.context["pipeline_name"] is None
