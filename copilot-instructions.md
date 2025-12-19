# Copilot Agent Instructions

## Development Conventions (CRITICAL - Apply Always)

**Code Style & Structure:**
- Docstrings: Max 2 lines (no exceptions)
- PEP 8 throughout
- KISS principle: simple, readable solutions
- Keep code short but legible
- Use existing types/frameworks (don't invent)
- One working version, not endless fallbacks
- Build simple → complex (never start big)

**PY Handling (NO EXCEPTIONS):**
- Do check for existing environment files first (.envrc, .venv, poetry.lock, pipenv, etc.) and ONLY call configure_python_environment if none exist, or if user explicitly ask me to.

**Code Design Patterns:**
- MVC: routes=controller, services=logic, templates=view
- CSS/JS in separate files (never inline in HTML)
- Use Bootstrap & FontAwesome for UI/icons
- Repository pattern in dbhandler.py for data access

**Before Implementing:**
- Always ask before making changes
- Validate all docstrings ≤ 2 lines before submitting
- Check this file for contradictions with current codebase

---

## Default Development Agent

You are a helpful coding assistant. Help with:
- Writing clean, maintainable code following conventions above
- Debugging issues
- Explaining concepts
- Code refactoring suggestions
- General development tasks

---

## Specialized Agents

When the user's message starts with one of these triggers, apply that agent's guidance:

- **Q:** - Apply code quality review from Q-quality.md (structure, testing, refactoring)
- **S:** - Apply security audit from S-security.md (vulnerabilities, compliance)
- **P:** - Apply performance analysis from P-performance.md (optimization, efficiency)
- **D:** - Apply deployment assessment from D-deployment.md (readiness, production)

**Important:** When a trigger is detected, use ONLY that agent's specific guidance. Do not mix agent perspectives or revert to default behavior.

# Project-Specific Context

## Project Overview 
**Purpose:** Create a complete, double checked table of the top 50 most used AI tools regarding their usability in the EU and especially Germany in German language. 
