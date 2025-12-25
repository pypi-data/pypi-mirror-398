"""LSP (Language Server Protocol) server for bio_pype validation.

Provides real-time IDE support for snippet (.md), profile (.yaml),
and pipeline (.yaml) files across VSCode, Helix, Neovim, Zed, and Cursor.

Features:
- Real-time diagnostics (validation errors/warnings)
- Hover information (argument help, variable descriptions)
- Autocomplete (snippet/profile/variable suggestions)
- Go-to-definition (navigate between files)
- Special: Pipeline command preview on hover
"""

__version__ = "0.1.0"
__all__ = ["start_server"]

from pype.lsp.server import start_server
