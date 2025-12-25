"""Main LSP server implementation for bio_pype.

Uses pygls (Python Language Server Protocol) library to provide
real-time IDE support across multiple editors.
"""

import asyncio
import logging
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from lsprotocol import types
from pygls.server import LanguageServer

from pype.lsp.handlers import (
    CompletionHandler,
    DiagnosticsHandler,
    HoverHandler,
)
from pype.validation import (
    ValidationContext,
    discover_modules,
)

# Configure logging
logger = logging.getLogger("bio_pype_lsp")


class BioPypeLspServer(LanguageServer):
    """LSP server for bio_pype validation.

    Provides real-time validation diagnostics for snippet, profile,
    and pipeline files.
    """

    def __init__(self):
        """Initialize LSP server."""
        super().__init__("bio-pype-lsp", "v0.1.0")

        self.workspace_root: Optional[Path] = None
        self.validation_context: Optional[ValidationContext] = None

        # Thread pool executor for running validation and other CPU-bound operations
        # without blocking the main LSP event loop
        self.executor_pool = ThreadPoolExecutor(max_workers=5)

        # Shared cache: stores validation results per file URI
        # This allows handlers to share cached validation data without re-validating
        self.validation_cache: dict = {}  # {uri: ValidationResult}
        self.completion_handler = CompletionHandler(self)

        # Initialize handlers (debounce_delay=0.1 for responsive validation)
        self.diagnostics_handler = DiagnosticsHandler(self, debounce_delay=0.1)

        self.hover_handler = HoverHandler(self)

        # Register LSP feature handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all LSP message handlers."""

        @self.feature(types.TEXT_DOCUMENT_DID_OPEN)
        def did_open(params) -> None:
            """Handle document open."""
            uri = params.text_document.uri
            logger.info(f"Document opened: {uri}")
            asyncio.create_task(self.diagnostics_handler.validate_document(uri))

        @self.feature(types.TEXT_DOCUMENT_DID_CHANGE)
        async def did_change(params) -> None:
            """Handle document change - real-time validation with debouncing."""
            uri = params.text_document.uri
            logger.info(f"Document changed: {uri}")
            # Validate with debouncing (500ms delay) - avoids validating on every keystroke
            await self.diagnostics_handler.validate_document_debounced(uri)

        @self.feature(types.TEXT_DOCUMENT_DID_SAVE)
        def did_save(params) -> None:
            """Handle document save."""
            uri = params.text_document.uri
            logger.info(f"Document saved: {uri}")
            asyncio.create_task(self.diagnostics_handler.validate_document(uri))

        @self.feature(types.TEXT_DOCUMENT_DID_CLOSE)
        def did_close(params) -> None:
            """Handle document close."""
            uri = params.text_document.uri
            logger.info(f"Document closed: {uri}")

        @self.feature(types.TEXT_DOCUMENT_HOVER)
        async def hover(params: types.HoverParams) -> Optional[types.Hover]:
            """Handle hover request."""
            # Run hover handler in executor pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor_pool,
                self.hover_handler.get_hover_info,
                params.text_document.uri,
                params.position,
            )

        @self.feature(types.TEXT_DOCUMENT_COMPLETION)
        async def completion(
            params: types.CompletionParams,
        ) -> Optional[types.CompletionList]:
            """Handle completion request."""
            # Run completion handler in executor pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor_pool,
                self.completion_handler.get_completions,
                params.text_document.uri,
                params.position,
            )

    def path_to_uri(self, file_path: Path) -> str:
        """Convert filesystem path to LSP URI format.

        Args:
            file_path: Filesystem path (Path object or string)

        Returns:
            URI in file:// format
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        # Convert to absolute path and add file:// scheme
        return file_path.absolute().as_uri()

    def initialize_workspace(self, root_uri: str) -> None:
        """Initialize workspace with validation context.

        Args:
            root_uri: Workspace root URI (file:// format)
        """
        try:
            # Convert file:// URI to path
            root_path = Path(root_uri.replace("file://", ""))
            self.workspace_root = root_path

            logger.info(f"Initializing workspace at: {root_path}")

            # Try to discover modules at root first
            logger.info(
                f"Searching for modules at: {root_path}/snippets/, {root_path}/profiles/, {root_path}/pipelines/"
            )
            self.validation_context = discover_modules(root_path)

            # If not found at root, search subdirectories and aggregate ALL results
            if (
                not self.validation_context.snippet_paths
                and not self.validation_context.profile_paths
                and not self.validation_context.pipeline_paths
            ):
                logger.info(
                    f"No modules found at root, searching subdirectories recursively..."
                )
                all_snippets = []
                all_profiles = []
                all_pipelines = []

                # Search immediate subdirectories only (one level deep)
                for subdir in sorted(root_path.glob("*")):
                    if not subdir.is_dir():
                        continue
                    try:
                        context = discover_modules(subdir)
                        if context.snippet_paths:
                            logger.debug(
                                f"Found {len(context.snippet_paths)} snippets in {subdir}"
                            )
                            all_snippets.extend(context.snippet_paths)
                        if context.profile_paths:
                            logger.debug(
                                f"Found {len(context.profile_paths)} profiles in {subdir}"
                            )
                            all_profiles.extend(context.profile_paths)
                        if context.pipeline_paths:
                            logger.debug(
                                f"Found {len(context.pipeline_paths)} pipelines in {subdir}"
                            )
                            all_pipelines.extend(context.pipeline_paths)
                    except Exception as e:
                        # Skip directories that can't be discovered
                        logger.debug(f"Could not discover modules in {subdir}: {e}")
                        pass

                # Create context with aggregated results
                if all_snippets or all_profiles or all_pipelines:
                    from pype.validation.core import ValidationContext

                    self.validation_context = ValidationContext(
                        workspace_root=root_path,
                        snippet_paths=sorted(set(all_snippets)),  # Remove duplicates
                        profile_paths=sorted(set(all_profiles)),
                        pipeline_paths=sorted(set(all_pipelines)),
                    )
                    logger.info(
                        f"Found modules in subdirectories: {len(all_snippets)} snippets, {len(all_profiles)} profiles, {len(all_pipelines)} pipelines"
                    )

            logger.info(f"Initialized workspace at {root_path}")
            logger.info(
                f"Found {len(self.validation_context.snippet_paths)} snippets, "
                f"{len(self.validation_context.profile_paths)} profiles, "
                f"{len(self.validation_context.pipeline_paths)} pipelines"
            )
        except Exception as e:
            logger.error(f"Failed to initialize workspace: {e}")
            raise


def start_server(
    use_stdio: bool = True,
    tcp_port: Optional[int] = None,
    log_file: Optional[str] = None,
) -> None:
    """Start the LSP server.

    Args:
        use_stdio: Use stdio for communication (default True)
        tcp_port: Optional TCP port for debugging
        log_file: Optional log file path
    """
    # Configure logging to both file and stderr
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if log_file:
        # Log to file at DEBUG level
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))

        # Also log to stderr at INFO level
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.INFO)
        stderr_handler.setFormatter(logging.Formatter(log_format))

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stderr_handler)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
        )

    logger.info("Starting bio_pype LSP server")

    # Create server instance
    server = BioPypeLspServer()

    # Register initialization handler
    @server.feature("initialize")
    def initialize(params: types.InitializeParams):
        """Initialize server with workspace information."""
        if params.root_uri:
            server.initialize_workspace(params.root_uri)

        # Return server capabilities
        return {
            "capabilities": {
                "textDocumentSync": types.TextDocumentSyncKind.Full,
                "diagnosticProvider": {},
                "hoverProvider": True,
                "completionProvider": {
                    "resolveProvider": False,
                    "triggerCharacters": ["%", "(", "-", "@"],
                },
            }
        }

    @server.feature("initialized")
    def on_initialized(params: types.InitializedParams) -> None:
        """Handle initialization complete."""
        logger.info("Initialization complete")

    # Setup signal handling for graceful shutdown
    def signal_handler(signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start server
    try:
        if use_stdio:
            logger.info("Starting server on stdio")
            server.start_io()
        elif tcp_port:
            logger.info(f"Starting server on TCP port {tcp_port}")
            server.start_tcp("127.0.0.1", tcp_port)
        else:
            logger.error("Must specify either stdio or tcp_port")
            raise ValueError("Must specify either stdio or tcp_port")
    except KeyboardInterrupt:
        logger.info("Server interrupted, shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
