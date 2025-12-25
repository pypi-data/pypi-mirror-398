# Release Notes

## Release 1.0.9 (2025-11-11)

This release delivers complete GitHub-style alert rendering for JupyterLab 4 with full theme support and optional customization.

**Key Features**:
- **Complete Alert Support** - All five GitHub alert types (NOTE, TIP, IMPORTANT, WARNING, CAUTION) with proper icons and colors
- **Theme Integration** - Automatic color adaptation for light and dark themes matching GitHub's exact styling
- **Icon Rendering** - SVG icons encoded as data URIs with theme-specific colors for each alert type
- **Optional Backgrounds** - User-configurable colored backgrounds via Settings → GitHub Markdown Alerts (disabled by default)
- **Markdown Compatibility** - Full markdown parsing within alert blocks (bold, italic, links, code, etc.)
- **Code Block Awareness** - Alert syntax in code blocks displays as examples rather than rendering as alerts

**Technical Implementation**:
- Two-phase processing using HTML comment markers to preserve markdown features
- Base64-encoded SVG data URIs to bypass JupyterLab's HTML sanitizer
- CSS theme detection using `body[data-jp-theme-light='false']` selector
- Settings integration via `@jupyterlab/settingregistry`
