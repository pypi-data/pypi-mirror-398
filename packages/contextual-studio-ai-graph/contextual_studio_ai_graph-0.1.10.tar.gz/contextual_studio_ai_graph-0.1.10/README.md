## 🧩 Development Setup (Required)

Before contributing or developing locally, you **must** use [`uv`](https://github.com/astral-sh/uv) for environment management and dependency installation,
and [`pre-commit`](https://pre-commit.com/) for code formatting, linting, typing, and commit validation.

These tools ensure consistency across contributors and enforce quality checks automatically.

---

### 🧰 1️⃣ Install and sync environment with `uv`

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, sync all dependencies including development ones:

```bash
uv sync --dev
```

---

### 🪝 2️⃣ Install and enable `pre-commit` using `uv`

```bash
# Add pre-commit as a dev dependency
uv add --dev pre-commit

# Install both pre-commit and commit-msg hooks
uv run pre-commit install --install-hooks

# (Optional) Run pre-commit checks across the entire repository
uv run pre-commit run --all-files
```

> 💡 The hooks automatically enforce:
>
> - Code formatting (`black`, `isort`)
> - Static analysis (`flake8`, `ruff`, `mypy`)
> - Conventional commit messages
> - Basic hygiene checks (whitespace, EOFs, merge conflicts, etc.)

---

### ⚙️ Example `.pre-commit-config.yaml`

Your project already includes a very rich pre-commit setup:

```yaml
default_install_hook_types:
  - pre-commit
  - commit-msg

exclude: ^(?!COMMIT_EDITMSG$).*\.py$

repos:
  # Conventional Commits
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v4.3.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [--strict, --verbose, feat, fix, ci, docs, style, refactor, test, custom]

  # Basic repo hygiene
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
      - id: check-toml
      - id: check-yaml
        args: [--unsafe]
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-added-large-files
      - id: check-case-conflict
      - id: mixed-line-ending
        args: [--fix=lf]

  # Sorting imports
  - repo: https://github.com/timothycrosley/isort
    rev: 6.0.1
    hooks:
      - id: isort
        additional_dependencies: [toml]

  # Code formatting
  - repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
      - id: black

  # Linting
  - repo: https://github.com/pycqa/flake8
    rev: 7.3.0
    hooks:
      - id: flake8
        exclude: tests
        args: [--config=.flake8]
        additional_dependencies: [flake8-docstrings]

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.17.1
    hooks:
      - id: mypy
        exclude: "tests"
        additional_dependencies:
          - types-PyYAML
          - types-requests
          - pydantic
          - sqlmodel

  # Fast lint + autofix
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: "v0.12.7"
    hooks:
      - id: ruff
        args: [--fix]
```

---

### ✅ Development Workflow Summary

```bash
# 1. Clone the repository
git clone https://github.com/contextual-studio/graph.git
cd graph

# 2. Sync dependencies
uv sync --all-groups --all-extras

# 3. Enable pre-commit hooks
uv run pre-commit install --install-hooks

# 4. Run tests before pushing
uv run pytest -v
```
