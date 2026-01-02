# dotpop

**dotpop** is a professional-grade configuration engine for Python that extends the standard `.env` format with strict type safety, AES-encrypted secrets, and conditional logic. Designed for startups, microservices, and AI-generated applications, it eliminates "silent failures" by validating your environment variables at startup and protecting sensitive data at rest.

## Why dotpop?

Standard `.env` files are brittle—no validation, no types, no secrets protection. dotpop fixes this:

- ✅ **Strong typing** - int, float, bool, json, list, path, url, secret
- ✅ **Validation rules** - required, min/max, regex, one_of
- ✅ **AES-encrypted secrets** - Protect API keys and passwords at rest
- ✅ **Conditional logic** - Single file for dev/staging/prod
- ✅ **Variable interpolation** - DRY configuration with `${VAR}` syntax

## Installation

```bash
pip install dotpop
```

## Quick Start

**1. Basic usage** - Works with existing `.env` files:

```python
from dotpop import load

env = load(".env")
print(env["PORT"])  # "8080"
```

**2. Add types** - Create `config.dpop` with type safety:

```dpop
HOST:str=localhost
PORT:int=8000 | required | min=1024 | max=65535
DEBUG:bool=true
TAGS:list=api,database,cache
```

```python
env = load("config.dpop")
print(env["PORT"])  # 8000 (int, not string!)
```

**3. Add environment logic** - Single file for all environments:

```dpop
ENV:str=development | one_of=development,staging,production

@if ENV == "production"
    DEBUG:bool=false
    WORKERS:int=8
@else
    DEBUG:bool=true
    WORKERS:int=2
@end

HOST=${HOST:-localhost}
PORT:int=${PORT:-8000}
API_URL=http://${HOST}:${PORT}
```

**4. Encrypt secrets** - Protect sensitive data:

```bash
# Generate master key
export DOTPOP_MASTER_KEY=$(openssl rand -hex 32)

# Encrypt secrets
echo "my-api-key" | dotpop encrypt > api.key.enc
```

```dpop
API_KEY:secret=@encrypted:api.key.enc | required
DATABASE_PASSWORD:secret=@encrypted:db.password.enc | required
```

```python
env = load("config.dpop")
api_key = env["API_KEY"]  # Automatically decrypted!
```

## Real-World Example

```dpop
# config.dpop
ENV:str=${ENV:-development} | one_of=development,staging,production

@if ENV == "production"
    DEBUG:bool=false
    LOG_LEVEL=error
    WORKERS:int=4
@else
    DEBUG:bool=true
    LOG_LEVEL=debug
    WORKERS:int=1
@end

HOST:str=0.0.0.0
PORT:int=8000 | min=1024 | max=65535

DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
API_KEY:secret=@encrypted:api.key.enc | required

CORS_ORIGINS:list=http://localhost:3000,https://app.example.com
CACHE_TTL:int=3600
```

```python
from dotpop import load
from fastapi import FastAPI

env = load("config.dpop")

app = FastAPI(debug=env["DEBUG"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=env["HOST"], port=env["PORT"], workers=env["WORKERS"])
```

## CLI Tools

```bash
# Validate config
dotpop check config.dpop

# Encrypt secrets
dotpop encrypt --interactive

# View variables
dotpop print config.dpop

# Export formats
dotpop export config.dpop --format json
dotpop export config.dpop --format dotenv
```

## Features at a Glance

**Types**: `str`, `int`, `float`, `bool`, `json`, `list`, `path`, `url`, `secret`

**Validators**: `required`, `non_empty`, `one_of`, `regex`, `min`, `max`

**Conditionals**: `@if ENV == "prod"`, `@elif`, `@else`, `@end`

**Interpolation**: `URL=http://${HOST}:${PORT}`, `${VAR:-default}`

**Includes**: `@include "base.dpop"`, `@include "configs/${ENV}.dpop"`

## Documentation

- [Full Documentation](./docs/README.md)
- [API Reference](./docs/api-reference.md)
- [CLI Reference](./docs/cli-reference.md)
- [Security Guide](./docs/security.md)
- [Examples](./examples)

## Migration from dotenv

dotpop works with existing `.env` files—no changes needed:

```python
# Just change the import
from dotpop import load
env = load(".env")
```

Then add types and validation incrementally by renaming to `.dpop`.

## License

MIT License

---

**Questions?** Check the [docs](./docs) or open an issue on GitHub.
