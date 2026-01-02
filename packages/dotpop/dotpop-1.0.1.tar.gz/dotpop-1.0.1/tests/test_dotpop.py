"""Unit tests for dotpop."""

import pytest
from pathlib import Path
import tempfile
import os

from dotpop import load, loads
from dotpop.exceptions import (
    ParseError, ValidationError, ResolutionError,
    CircularIncludeError, ConditionError, TypeError_
)


class TestBasicParsing:
    """Test basic .env parsing."""
    
    def test_simple_key_value(self):
        env = loads("KEY=value")
        assert env["KEY"] == "value"
        assert env.get_str("KEY") == "value"
    
    def test_quoted_values(self):
        env = loads('KEY="quoted value"')
        assert env["KEY"] == "quoted value"
        
        env = loads("KEY='single quoted'")
        assert env["KEY"] == "single quoted"
    
    def test_comments(self):
        text = """
        # This is a comment
        KEY=value
        # Another comment
        KEY2=value2
        """
        env = loads(text)
        assert env["KEY"] == "value"
        assert env["KEY2"] == "value2"
    
    def test_blank_lines(self):
        text = """
        KEY=value
        
        KEY2=value2
        """
        env = loads(text)
        assert env["KEY"] == "value"
        assert env["KEY2"] == "value2"
    
    def test_export_syntax(self):
        env = loads("export KEY=value")
        assert env["KEY"] == "value"
    
    def test_escaped_quotes(self):
        env = loads(r'KEY="escaped \"quotes\""')
        assert env["KEY"] == 'escaped "quotes"'
    
    def test_escaped_newlines(self):
        env = loads(r'KEY="line1\nline2"')
        assert env["KEY"] == "line1\nline2"


class TestTypes:
    """Test type conversions."""
    
    def test_string_type(self):
        env = loads("KEY:str=hello", format="intenv")
        assert env["KEY"] == "hello"
        assert isinstance(env["KEY"], str)
    
    def test_int_type(self):
        env = loads("PORT:int=8080", format="intenv")
        assert env["PORT"] == 8080
        assert isinstance(env["PORT"], int)
    
    def test_float_type(self):
        env = loads("RATE:float=3.14", format="intenv")
        assert env["RATE"] == 3.14
        assert isinstance(env["RATE"], float)
    
    def test_bool_type(self):
        env = loads("DEBUG:bool=true", format="intenv")
        assert env["DEBUG"] is True
        
        env = loads("DEBUG:bool=false", format="intenv")
        assert env["DEBUG"] is False
        
        env = loads("DEBUG:bool=1", format="intenv")
        assert env["DEBUG"] is True
        
        env = loads("DEBUG:bool=0", format="intenv")
        assert env["DEBUG"] is False
    
    def test_json_type(self):
        env = loads('CONFIG:json={"key": "value"}', format="intenv")
        assert env["CONFIG"] == {"key": "value"}
        assert isinstance(env["CONFIG"], dict)
    
    def test_list_type(self):
        env = loads("TAGS:list=tag1,tag2,tag3", format="intenv")
        assert env["TAGS"] == ["tag1", "tag2", "tag3"]
        assert isinstance(env["TAGS"], list)
    
    def test_path_type(self):
        env = loads("FILE:path=/tmp/file.txt", format="intenv")
        assert env["FILE"] == Path("/tmp/file.txt")
        assert isinstance(env["FILE"], Path)
    
    def test_url_type(self):
        env = loads("API:url=https://example.com", format="intenv")
        assert env["API"] == "https://example.com"
    
    def test_invalid_type_conversion(self):
        with pytest.raises(TypeError_):
            loads("PORT:int=not_a_number", format="intenv")


class TestInterpolation:
    """Test variable interpolation."""
    
    def test_basic_interpolation(self):
        text = """
        HOST=localhost
        PORT=8080
        URL=http://${HOST}:${PORT}
        """
        env = loads(text)
        assert env["URL"] == "http://localhost:8080"
    
    def test_interpolation_with_default(self):
        env = loads("HOST=${HOST:-localhost}")
        assert env["HOST"] == "localhost"
    
    def test_interpolation_with_existing_var(self):
        text = """
        HOST=myhost
        URL=${HOST:-localhost}
        """
        env = loads(text)
        assert env["URL"] == "myhost"
    
    def test_nested_interpolation(self):
        text = """
        A=hello
        B=${A}
        C=${B}
        """
        env = loads(text)
        assert env["C"] == "hello"
    
    def test_undefined_variable(self):
        with pytest.raises(ResolutionError):
            loads("URL=${UNDEFINED_VAR}", use_os_env=False)
    
    def test_circular_reference(self):
        text = """
        A=${B}
        B=${A}
        """
        with pytest.raises(ResolutionError, match="Circular reference"):
            loads(text)


class TestValidation:
    """Test validators."""
    
    def test_required_validator(self):
        with pytest.raises(ValidationError):
            loads("KEY:str= | required", format="intenv")
    
    def test_non_empty_validator(self):
        with pytest.raises(ValidationError):
            loads("KEY:str= | non_empty", format="intenv")
    
    def test_one_of_validator(self):
        env = loads("ENV:str=production | one_of=development,staging,production", format="intenv")
        assert env["ENV"] == "production"
        
        with pytest.raises(ValidationError):
            loads("ENV:str=invalid | one_of=development,staging,production", format="intenv")
    
    def test_regex_validator(self):
        env = loads(r"EMAIL:str=test@example.com | regex=^[^@]+@[^@]+\.[^@]+$", format="intenv")
        assert env["EMAIL"] == "test@example.com"
        
        with pytest.raises(ValidationError):
            loads(r"EMAIL:str=invalid | regex=^[^@]+@[^@]+\.[^@]+$", format="intenv")
    
    def test_min_validator(self):
        env = loads("PORT:int=8080 | min=1", format="intenv")
        assert env["PORT"] == 8080
        
        with pytest.raises(ValidationError):
            loads("PORT:int=0 | min=1", format="intenv")
    
    def test_max_validator(self):
        env = loads("PORT:int=8080 | max=65535", format="intenv")
        assert env["PORT"] == 8080
        
        with pytest.raises(ValidationError):
            loads("PORT:int=99999 | max=65535", format="intenv")
    
    def test_chained_validators(self):
        env = loads("PORT:int=8080 | required | min=1 | max=65535", format="intenv")
        assert env["PORT"] == 8080


class TestConditions:
    """Test conditional blocks."""
    
    def test_simple_if(self):
        text = """
        ENV=production
        @if ENV == "production"
        DEBUG:bool=false
        @end
        """
        env = loads(text, format="intenv")
        assert env["DEBUG"] is False
    
    def test_if_else(self):
        text = """
        ENV=development
        @if ENV == "production"
        DEBUG:bool=false
        @else
        DEBUG:bool=true
        @end
        """
        env = loads(text, format="intenv")
        assert env["DEBUG"] is True
    
    def test_if_elif_else(self):
        text = """
        ENV=staging
        @if ENV == "production"
        LOG_LEVEL=error
        @elif ENV == "staging"
        LOG_LEVEL=warning
        @else
        LOG_LEVEL=debug
        @end
        """
        env = loads(text, format="intenv")
        assert env["LOG_LEVEL"] == "warning"
    
    def test_defined_condition(self):
        text = """
        HOST=localhost
        @if defined(HOST)
        PORT:int=8080
        @end
        """
        env = loads(text, format="intenv")
        assert env["PORT"] == 8080
    
    def test_not_defined_condition(self):
        text = """
        @if not_defined(HOST)
        HOST=localhost
        @end
        """
        env = loads(text, format="intenv", use_os_env=False)
        assert env["HOST"] == "localhost"
    
    def test_not_equals_condition(self):
        text = """
        ENV=development
        @if ENV != "production"
        DEBUG:bool=true
        @end
        """
        env = loads(text, format="intenv")
        assert env["DEBUG"] is True
    
    def test_nested_conditions(self):
        text = """
        ENV=production
        FEATURE_FLAG=enabled
        @if ENV == "production"
        @if FEATURE_FLAG == "enabled"
        FEATURE:bool=true
        @end
        @end
        """
        env = loads(text, format="intenv")
        assert env["FEATURE"] is True
    
    def test_unclosed_condition(self):
        text = """
        @if ENV == "production"
        DEBUG:bool=false
        """
        with pytest.raises(ConditionError, match="Unclosed"):
            loads(text, format="intenv")


class TestIncludes:
    """Test file inclusion."""
    
    def test_basic_include(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_file = Path(tmpdir) / "base.Intenv"
            base_file.write_text("BASE_KEY=base_value")
            
            main_file = Path(tmpdir) / "main.Intenv"
            main_file.write_text('@include "base.Intenv"\nMAIN_KEY=main_value')
            
            env = load(str(main_file))
            assert env["BASE_KEY"] == "base_value"
            assert env["MAIN_KEY"] == "main_value"
    
    def test_include_with_interpolation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prod_file = Path(tmpdir) / "production.Intenv"
            prod_file.write_text("DEBUG:bool=false")
            
            main_file = Path(tmpdir) / "main.Intenv"
            main_file.write_text('ENV=production\n@include "${ENV}.Intenv"')
            
            env = load(str(main_file))
            assert env["DEBUG"] is False
    
    def test_circular_include(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = Path(tmpdir) / "a.Intenv"
            file_b = Path(tmpdir) / "b.Intenv"
            
            file_a.write_text('@include "b.Intenv"')
            file_b.write_text('@include "a.Intenv"')
            
            with pytest.raises(CircularIncludeError):
                load(str(file_a))
    
    def test_missing_include(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = Path(tmpdir) / "main.Intenv"
            main_file.write_text('@include "missing.Intenv"')
            
            with pytest.raises(Exception):  # IncludeError
                load(str(main_file))


class TestOverrides:
    """Test override behavior."""
    
    def test_basic_override(self):
        text = """
        KEY=original
        KEY=overridden
        """
        env = loads(text)
        assert env["KEY"] == "original"  # First value wins
    
    def test_force_override(self):
        text = """
        KEY=original
        !KEY=forced
        """
        env = loads(text, format="intenv")
        assert env["KEY"] == "forced"
    
    def test_override_syntax(self):
        text = """
        KEY=original
        @override KEY=forced
        """
        env = loads(text, format="intenv")
        assert env["KEY"] == "forced"


class TestSources:
    """Test source tracking."""
    
    def test_source_info(self):
        env = loads("KEY=value", file="test.env")
        assert "KEY" in env.sources
        assert env.sources["KEY"].file == "test.env"
        assert env.sources["KEY"].line == 1


class TestOSEnvironment:
    """Test OS environment integration."""
    
    def test_use_os_env(self):
        os.environ["TEST_OS_VAR"] = "from_os"
        env = loads("KEY=${TEST_OS_VAR}", use_os_env=True)
        assert env["KEY"] == "from_os"
        del os.environ["TEST_OS_VAR"]
    
    def test_no_os_env(self):
        os.environ["TEST_OS_VAR"] = "from_os"
        with pytest.raises(ResolutionError):
            loads("KEY=${TEST_OS_VAR}", use_os_env=False)
        del os.environ["TEST_OS_VAR"]


class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_production_config(self):
        text = """
        # Base configuration
        HOST=${HOST:-localhost}
        PORT:int=${PORT:-8000} | required | min=1 | max=65535
        ENV:str=${ENV:-development} | one_of=development,staging,production
        
        @if ENV == "production"
        DEBUG:bool=false
        LOG_LEVEL:str=warning
        DATABASE_URL:url=https://prod.db.example.com
        @elif ENV == "staging"
        DEBUG:bool=true
        LOG_LEVEL:str=info
        DATABASE_URL:url=https://staging.db.example.com
        @else
        DEBUG:bool=true
        LOG_LEVEL:str=debug
        DATABASE_URL:url=http://localhost:5432
        @end
        
        # Computed values
        API_URL="http://${HOST}:${PORT}"
        """
        env = loads(text, format="intenv", use_os_env=False)
        
        assert env["HOST"] == "localhost"
        assert env["PORT"] == 8000
        assert env["ENV"] == "development"
        assert env["DEBUG"] is True
        assert env["LOG_LEVEL"] == "debug"
        assert env["API_URL"] == "http://localhost:8000"
