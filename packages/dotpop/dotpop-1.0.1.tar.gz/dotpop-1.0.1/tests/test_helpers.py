"""Tests for helper functions."""

import pytest
import os
from dotpop import loads
from dotpop.helpers import apply, export


class TestApply:
    """Test applying environment variables to os.environ."""
    
    def test_apply_basic(self):
        env = loads("KEY=value")
        apply(env.values)
        assert os.environ.get("KEY") == "value"
        del os.environ["KEY"]
    
    def test_apply_no_overwrite(self):
        os.environ["EXISTING"] = "original"
        env = loads("EXISTING=new")
        apply(env.values, overwrite=False)
        assert os.environ["EXISTING"] == "original"
        del os.environ["EXISTING"]
    
    def test_apply_with_overwrite(self):
        os.environ["EXISTING"] = "original"
        env = loads("EXISTING=new")
        apply(env.values, overwrite=True)
        assert os.environ["EXISTING"] == "new"
        del os.environ["EXISTING"]


class TestExport:
    """Test exporting to different formats."""
    
    def test_export_dotenv(self):
        env = loads("KEY=value\nKEY2=value2")
        output = export(env.values, format="dotenv", redact_secrets=False)
        assert 'KEY="value"' in output
        assert 'KEY2="value2"' in output
    
    def test_export_json(self):
        env = loads("KEY=value\nKEY2=value2")
        output = export(env.values, format="json", redact_secrets=False)
        assert '"KEY": "value"' in output
        assert '"KEY2": "value2"' in output
    
    def test_export_cmake(self):
        env = loads("KEY=value")
        output = export(env.values, format="cmake", redact_secrets=False)
        assert 'set(KEY "value")' in output
    
    def test_export_cpp_header(self):
        env = loads("KEY=value")
        output = export(env.values, format="cpp-header", redact_secrets=False)
        assert '#define KEY "value"' in output
        assert '#pragma once' in output
    
    def test_secret_redaction(self):
        env = loads("API_KEY=secret123\nNORMAL=value")
        output = export(env.values, format="dotenv", redact_secrets=True)
        assert "***REDACTED***" in output
        assert "secret123" not in output
        assert 'NORMAL="value"' in output
    
    def test_custom_secret_patterns(self):
        env = loads("CUSTOM_SECRET=secret\nNORMAL=value")
        output = export(
            env.values,
            format="dotenv",
            secret_patterns=[r".*CUSTOM.*"],
            redact_secrets=True
        )
        assert "***REDACTED***" in output
        assert "secret" not in output
