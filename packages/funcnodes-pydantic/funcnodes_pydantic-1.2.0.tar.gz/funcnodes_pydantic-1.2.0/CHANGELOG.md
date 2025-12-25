## 1.2.0 (2025-12-21)

### Feat

- **funcnodes-pydantic**: include json schema in model encoding
- **tests**: add pytest-cov for coverage reporting

## 1.1.0 (2025-12-08)

### Feat

- **commitizen**: add commitizen configuration for conventional commits
- **dependencies**: add httpx and update project metadata
- **pydantic**: implement Union type flattening in PydanticUnpacker
- **pydantic**: enhance PydanticUnpacker with unlimited traversal levels
- **pydantic**: add node shelves and Pydantic unpacker

### Fix

- **dependencies**: update pydantic version constraint in pyproject.toml
- **pydantic**: reorder unpacked params and guard mixed unions

### Refactor

- **pydantic**: enhance flattening of Union outputs with base name support
