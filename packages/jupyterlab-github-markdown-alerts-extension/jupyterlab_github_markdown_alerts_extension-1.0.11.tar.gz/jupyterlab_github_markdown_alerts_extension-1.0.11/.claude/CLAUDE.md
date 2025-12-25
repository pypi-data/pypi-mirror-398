<!-- Import workspace-level CLAUDE.md configuration -->
<!-- See /home/lab/workspace/.claude/CLAUDE.md for complete rules -->

# Project-Specific Configuration

This file extends workspace-level configuration with project-specific rules.

## Project Context

**Project**: JupyterLab GitHub Markdown Alerts Extension

**Purpose**: A JupyterLab 4 extension that renders GitHub-style alert blocks in Markdown cells, supporting NOTE, TIP, IMPORTANT, WARNING, and CAUTION alert types.

**Technology Stack**:
- JupyterLab 4.x
- TypeScript 5.8
- CSS modules for styling
- Jest for unit testing
- Playwright/Galata for integration testing
- Hatchling for Python packaging
- Yarn (jlpm) for JavaScript package management

**Key Components**:
- `/src/index.ts` - Main extension entry point
- `/style/base.css` - Alert styling definitions
- `/style/index.css` - Style module entry
- `pyproject.toml` - Python package configuration
- `package.json` - JavaScript package configuration

**Alert Types Supported**:
```markdown
> [!NOTE]
> [!TIP]
> [!IMPORTANT]
> [!WARNING]
> [!CAUTION]
```

**Development Workflow**:
- Use `jlpm` for JavaScript operations (JupyterLab's pinned yarn)
- Development mode: `jupyter labextension develop . --overwrite`
- Watch mode: `jlpm watch` + `jupyter lab` in separate terminals
- Tests: `jlpm test` (unit), `ui-tests/` (integration)

**Naming Conventions**:
- Python package: `jupyterlab_github_markdown_alerts_extension` (underscores)
- NPM package: `jupyterlab_github_markdown_alerts_extension` (underscores, matching Python)
- CSS classes: kebab-case with `jp-` prefix for JupyterLab conventions
- TypeScript: PascalCase for interfaces (must start with `I`), camelCase for functions

**Build Process**:
- Development: `jlpm build` (with source maps)
- Production: `jlpm build:prod` (optimized)
- Clean: `jlpm clean:all` (removes all build artifacts)

**Publishing**:
- Python: PyPI via hatchling
- JavaScript: Bundled with Python package (labextension)
- See RELEASE.md for release process

**GitHub Repository**: https://github.com/stellarshenson/jupyterlab_github_markdown_alerts_extension
