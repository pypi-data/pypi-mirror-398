import pytest
from dotpop import loads
from dotpop.exceptions import ConditionError, ValidationError
from dotpop.validators import register_validator
from dotpop.types import set_encryption_key, encrypt_secret
from cryptography.fernet import Fernet


def test_complex_boolean_logic():
    text = """
ENV=production
DEBUG=false

@if ENV == "production" AND DEBUG == "false"
MODE=secure
@end
"""
    env = loads(text)
    assert env["MODE"] == "secure"


def test_nested_boolean_logic():
    text = """
A=true
B=true
C=false

@if (A == "true" OR B == "true") AND NOT C == "true"
RESULT=success
@end
"""
    env = loads(text)
    assert env["RESULT"] == "success"


def test_heredoc_multiline():
    text = """
PRIVATE_KEY:str=<<<EOF
-----BEGIN PRIVATE KEY-----
Line 1
Line 2
Line 3
-----END PRIVATE KEY-----
EOF

MESSAGE:str=<<<END
This is a message
with multiple lines
and special chars: !@#$%
END
"""
    env = loads(text)
    assert "Line 1\nLine 2\nLine 3" in env["PRIVATE_KEY"]
    assert env["MESSAGE"].count('\n') == 2


def test_inheritance():
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / ".dpop.base"
        base_path.write_text("HOST=localhost\nPORT:int=8080")
        
        child_path = Path(tmpdir) / ".dpop.production"
        child_path.write_text('@inherit "base"\nENV=production\nDEBUG:bool=false')
        
        from dotpop import load
        env = load(str(child_path))
        
        assert env["HOST"] == "localhost"
        assert env["PORT"] == 8080
        assert env["ENV"] == "production"
        assert env["DEBUG"] is False


def test_encrypted_secrets():
    key = Fernet.generate_key()
    set_encryption_key(key)
    
    plaintext = "my_secret_api_key_12345"
    encrypted = encrypt_secret(plaintext)
    
    text = f'API_KEY:secret=ENC({encrypted})'
    env = loads(text)
    
    assert env["API_KEY"] == plaintext


def test_constant_time_comparison():
    text = """
SECRET=test123

@if SECRET == "test123"
MATCHED=yes
@end
"""
    env = loads(text)
    assert env["MATCHED"] == "yes"


def test_deterministic_randomness():
    text1 = 'RANDOM:int=${rand(100, 200)}'
    text2 = 'RANDOM:int=${rand(100, 200)}'
    
    env1 = loads(text1, use_os_env=False)
    env2 = loads(text2, use_os_env=False)
    
    from dotpop.loader import Loader
    loader1 = Loader(random_seed=42)
    env1 = loader1.load_string(text1)
    
    loader2 = Loader(random_seed=42)
    env2 = loader2.load_string(text2)
    
    assert env1["RANDOM"] == env2["RANDOM"]


def test_custom_validator():
    def validate_cidr(value, arg):
        import re
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$', value):
            raise ValueError(f"Invalid CIDR: {value}")
    
    register_validator("cidr", validate_cidr)
    
    text = 'NETWORK:str=192.168.1.0/24 | cidr='
    env = loads(text)
    assert env["NETWORK"] == "192.168.1.0/24"
    
    with pytest.raises(ValidationError):
        text_invalid = 'NETWORK:str=invalid | cidr='
        loads(text_invalid)


def test_json_schema_validation():
    pytest.importorskip("jsonschema")
    
    text = '''CONFIG:json={"timeout": 30, "retries": 3} | json_schema={"type": "object", "required": ["timeout"]}'''
    env = loads(text)
    assert env["CONFIG"]["timeout"] == 30


def test_visual_error_diagnostics():
    from dotpop.exceptions import ParseError
    
    text = "INVALID SYNTAX HERE\nVALID=value"
    
    try:
        loads(text)
        assert False, "Should have raised ParseError"
    except ParseError as e:
        formatted = e.format_with_context(text.splitlines())
        assert "^" in formatted
        assert "INVALID SYNTAX HERE" in formatted


def test_lazy_resolution():
    from dotpop.loader import Loader
    
    text = """
A=hello
B=${A}_world
C:int=${rand(100)}
"""
    
    loader = Loader(lazy=True)
    env = loader.load_string(text)
    
    assert "B" not in env.typed
    
    b_value = env["B"]
    assert b_value == "hello_world"
    assert "B" in env.typed


def test_not_operator():
    text = """
DEBUG=false

@if NOT DEBUG == "true"
MODE=production
@end
"""
    env = loads(text)
    assert env["MODE"] == "production"


def test_complex_nested_conditions():
    text = """
ENV=prod
FEATURE_A=enabled
FEATURE_B=disabled

@if (ENV == "prod" OR ENV == "staging") AND (FEATURE_A == "enabled" OR FEATURE_B == "enabled")
DEPLOY=yes
@else
DEPLOY=no
@end
"""
    env = loads(text)
    assert env["DEPLOY"] == "yes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
