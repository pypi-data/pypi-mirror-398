# nlbone

**nlbone** (NumberLand Backbone) is a lightweight Python package that provides the foundational interfaces and
infrastructure for NumberLand projects.  
It follows a clean architecture style (ports & adapters) so that domain logic is separated from infrastructure concerns.

---

## ✨ Features

- **Domain interfaces**
- **Immutable domain models**
- **Application services** (use cases) independent of infrastructure.
- **Infrastructure adapters** (DB, HTTP, etc.).
- **Config management** with [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
- **Dependency injection container** for easy wiring.
- **Testing ready** with pytest + pytest-asyncio.
- **Dev tools**: Ruff (lint), Mypy (typing), Pre-commit hooks.

---

## 📦 Installation

```bash
pip install nlbone
``` 

## 🛠 For development:

```bash
git clone https://github.com/your-org/nlbone.git
cd nlbone
python -m venv .venv
source .venv/bin/activate   # (Linux/macOS)
# .venv\Scripts\activate    # (Windows)

pip install -e ".[dev]"

python -m pip install build twine
python -m build
```

## 🚀 Quick Example

```python
import anyio
from nlbone import build_container


async def main():
    container = build_container()
    user = await container.register_user("me@numberland.com")
    print(user)


anyio.run(main)
```

## 📦 Used In
- **Explore**
- **Pricing**
