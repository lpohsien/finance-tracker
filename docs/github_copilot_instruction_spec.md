# GitHub Copilot System Instructions Specification

This document outlines the configuration required to prompt GitHub Copilot to strictly adhere to Docker-based workflows for the `finance-tracker` project.

## Overview
By adding a custom instruction file, we can condition Copilot to assume a containerized environment. This prevents it from suggesting local commands (like `npm run dev` or `python main.py`) which may fail due to missing local dependencies or environment variables.

## Implementation Guide

To enable these instructions, create the following directory and file in the workspace root:

**Path:** `.github/copilot-instructions.md`

### 1. File Placement
This file must be located at the root of the (open) repository in VS Code for Copilot to pick it up.

```bash
mkdir -p .github
touch .github/copilot-instructions.md
```

### 2. Instruction Content
Copy the following content into `.github/copilot-instructions.md`. This content is tailored to the project's `docker-compose` structure.

```markdown
You are an expert developer assisting with the 'finance-tracker' project.
**CRITICAL CONTEXT:** This project runs entirely within Docker containers. The host machine DOES NOT have the project dependencies installed (Node.js, Python packages, etc.).

When answering questions or generating code/commands, you MUST adhere to the following rules:

# 1. Execution & CLI Commands
- **NEVER** suggest running commands locally (e.g., `npm run dev`, `python script.py`).
- **ALWAYS** suggest the `docker compose` equivalent.

## Mapping Table for Commands:
| Local Command | Docker Equivalent |
| :--- | :--- |
| `npm run dev` | `docker compose up frontend-dev` |
| `python scripts/x.py` | `docker compose run --rm backend python scripts/x.py` |
| `pytest` | `docker compose run --rm backend pytest` |
| Access database | `docker compose run --rm backend python scripts/view_db.py` |

# 2. Dependency Management
- **Python:** We use `uv` in the `backend` container. If a new package is needed, suggest adding it to `pyproject.toml` and rebuilding: `docker compose build backend`.
- **Frontend:** Dependencies are in `frontend/package.json`. Suggest `docker compose run --rm frontend-dev npm install <package>` if strictly necessary, but prefer rebuilding the container.

# 3. Development Workflow
- The `frontend-dev` service is configured for Hot Module Replacement (HMR) via Vite.
- The `backend` service mounts the source code, so restarts are required for Python changes unless a reloader is active.
- Database is persisted in `./data/finance.db`.

# 4. Troubleshooting
- If a script fails, assume it is because it wasn't run in the container. Remind the user to use `docker compose run`.
- To debug logs: `docker compose logs -f [service_name]`.
```

## References and Resources

- [VS Code Docs: Custom Instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
  - Official documentation on how `.github/copilot-instructions.md` works.
- [VS Code Docs: Prompt Files](https://code.visualstudio.com/docs/copilot/customization/prompt-files)
  - Information on reusable prompt files (an alternative for specific tasks, though instructions are better for system-wide defaults).
