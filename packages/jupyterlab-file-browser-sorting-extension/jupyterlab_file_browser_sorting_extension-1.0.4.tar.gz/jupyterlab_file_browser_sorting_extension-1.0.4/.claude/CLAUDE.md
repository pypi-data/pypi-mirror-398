<!-- Import workspace-level CLAUDE.md configuration -->
<!-- See /home/lab/workspace/.claude/CLAUDE.md for complete rules -->

# Project-Specific Configuration

This file extends workspace-level configuration with project-specific rules.

## Project Context

JupyterLab extension providing file browser sorting capabilities including case-sensitive sorting options.

**Technology Stack**:

- TypeScript for frontend extension code
- JupyterLab 4.x extension API
- Python packaging with `pyproject.toml` and `hatch`

**Package Names**:

- npm: `jupyterlab_file_browser_sorting_extension`
- PyPI: `jupyterlab-file-browser-sorting-extension`
- GitHub: `stellarshenson/jupyterlab_file_browser_sorting_extension`

**Build and Install**:

- Always use `make install` to build and install the extension
- Always commit both `package.json` and `package-lock.json` together
