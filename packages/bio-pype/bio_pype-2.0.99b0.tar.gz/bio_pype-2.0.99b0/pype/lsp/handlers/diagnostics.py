"""Diagnostics handler for LSP server.

Provides real-time validation diagnostics with debouncing for
text change events.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict

from lsprotocol import types

from pype.validation import (
    PipelineValidator,
    ProfileValidator,
    SnippetValidator,
)
from pype.validation.core import DiagnosticSeverity

logger = logging.getLogger("bio_pype_lsp.diagnostics")


class DiagnosticsHandler:
    """Manages diagnostic validation and publishing.

    Provides debouncing for text change events to avoid excessive
    validation while the user is typing.
    """

    def __init__(self, server, debounce_delay: float = 0.5):
        """Initialize diagnostics handler.

        Args:
            server: BioPypeLspServer instance
            debounce_delay: Delay in seconds before validating after change
        """
        self.server = server
        self.debounce_delay = debounce_delay
        self.pending_validations: Dict[str, asyncio.Task] = {}

    async def validate_document_debounced(self, uri: str) -> None:
        """Validate document with debouncing.

        Cancels any pending validation for this URI and schedules
        a new one after the debounce delay.

        Args:
            uri: Document URI (file:// format)
        """
        # Cancel existing pending validation for this document
        if uri in self.pending_validations:
            task = self.pending_validations[uri]
            if not task.done():
                task.cancel()
                logger.debug(f"Cancelled pending validation for {uri}")

        # Schedule new validation
        task = asyncio.create_task(self._validate_after_delay(uri))
        self.pending_validations[uri] = task

    async def _validate_after_delay(self, uri: str) -> None:
        """Validate document after delay.

        Args:
            uri: Document URI
        """
        try:
            await asyncio.sleep(self.debounce_delay)
            await self.validate_document(uri)
        except asyncio.CancelledError:
            logger.debug(f"Validation cancelled for {uri}")
        except Exception as e:
            logger.error(f"Error in delayed validation for {uri}: {e}")

    async def validate_document(self, uri: str) -> None:
        """Validate a document and publish diagnostics (async).

        Args:
            uri: Document URI (file:// format)
        """
        try:
            # Convert URI to path
            file_path = Path(uri.replace("file://", ""))
            logger.info(f"Starting validation for {file_path.name}")

            # Check if file exists on disk
            if not file_path.exists():
                logger.info(f"File not found on disk: {file_path.name}")
                return

            # Auto-detect module root from file location (exactly like the CLI does)
            from pype.validation import detect_module_root, discover_modules

            workspace_root = detect_module_root(file_path)
            if not workspace_root:
                # Fallback: same as CLI - for file, use parent.parent.parent
                workspace_root = file_path.parent.parent.parent
                logger.info(f"Using fallback workspace root: {workspace_root}")
            else:
                logger.info(f"Auto-detected module root: {workspace_root}")

            validation_context = discover_modules(workspace_root)

            # Get appropriate validator based on file type
            validator = self._get_validator_for_file(file_path, validation_context)
            if not validator:
                logger.info(f"No validator for file type: {file_path.suffix}")
                return
            logger.info(f"Using validator: {type(validator).__name__}")

            logger.info(f"Validating file: {file_path.name}")

            # Get content from workspace (automatically tracks all edits)
            try:
                text_document = self.server.workspace.get_text_document(uri)
                content = text_document.source
                logger.debug(f"Validating content from workspace: {len(content)} chars")
            except Exception as e:
                logger.warning(f"Could not get text document from workspace: {e}")
                # Fall back to reading from disk
                content = file_path.read_text()
                logger.debug(f"Validating disk content: {len(content)} chars")

            # Run validation in executor pool (CPU-bound operation)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.server.executor_pool,
                self._validate_with_content,
                validator,
                file_path,
                content,
                validation_context,
            )

            # Cache validation result for hover/completion handlers
            self.server.validation_cache[uri] = result

            # Convert to LSP diagnostics
            lsp_diagnostics = [
                self._convert_diagnostic(diag) for diag in result.diagnostics
            ]

            # Publish diagnostics
            self.server.publish_diagnostics(uri, lsp_diagnostics)

            logger.info(
                f"✓ Validated {file_path.name}: {len(result.diagnostics)} diagnostics"
            )

        except Exception as e:
            logger.error(f"⚠ Error validating document {uri}: {e}", exc_info=True)
            # Don't crash validation - just log and continue
            self.server.publish_diagnostics(uri, [])

    def _validate_with_content(
        self, validator, file_path: Path, content: str, validation_context
    ):
        """Validate file content using the workspace content, not disk.

        Creates a temp file with the editor content and validates it.
        This allows validators to see real-time editor changes.

        Args:
            validator: Validator instance
            file_path: Actual file path (used for context only)
            content: Current content from editor
            validation_context: ValidationContext to use

        Returns:
            ValidationResult with diagnostics
        """
        temp_path = None
        try:
            # Log validation context for debugging
            logger.info(f"Validating {file_path.name} with module context:")
            if validation_context:
                num_snippets = len(validation_context.snippet_paths)
                num_profiles = len(validation_context.profile_paths)
                num_pipelines = len(validation_context.pipeline_paths)
                logger.info(f"  Module root: {validation_context.workspace_root}")
                logger.info(
                    f"  Available: {num_snippets} snippets, {num_profiles} profiles, {num_pipelines} pipelines"
                )

            # Create a temp file with the current editor content
            # Place it in the same directory as the original file so validators
            # can resolve relative imports/references correctly
            temp_name = f".{file_path.name}.tmp"
            temp_path = file_path.parent / temp_name

            try:
                temp_path.write_text(content)
                logger.debug(
                    f"Created temp file with editor content: {temp_path} ({len(content)} chars)"
                )

                # Validate the temp file (contains current editor content)
                logger.info(f"Calling validator.validate({temp_path.name})")
                result = validator.validate(temp_path)

                logger.info(
                    f"Validation complete: {len(result.diagnostics)} diagnostics found"
                )
                if result.diagnostics:
                    for diag in result.diagnostics:
                        logger.info(
                            f"  - {diag.severity.name}: {diag.message} (code: {diag.code})"
                        )
                return result

            finally:
                # Clean up temp file
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                        logger.debug(f"Cleaned up temp file: {temp_path}")
                    except Exception as e:
                        logger.debug(f"Could not delete temp file {temp_path}: {e}")

        except Exception as e:
            logger.error(f"Validation error for {file_path.name}: {e}", exc_info=True)
            from pype.validation.core import ValidationResult

            return ValidationResult(
                file_path=file_path, file_type="unknown", diagnostics=[]
            )

    def _get_validator_for_file(self, file_path: Path, validation_context):
        """Get appropriate validator for file type.

        Args:
            file_path: Path to file being validated
            validation_context: ValidationContext to use for validation

        Returns:
            Validator instance or None if file type not supported
        """
        if file_path.suffix == ".md":
            # Markdown snippet
            return SnippetValidator(validation_context)
        elif file_path.suffix in [".yaml", ".yml"]:
            # YAML file - determine if profile or pipeline based on parent directory
            parent_name = file_path.parent.name.lower()

            if "profile" in parent_name:
                return ProfileValidator(validation_context)
            elif "pipeline" in parent_name:
                return PipelineValidator(validation_context)
            else:
                # Default to pipeline for unknown YAML files
                logger.info(
                    f"Defaulting to pipeline validator for {file_path.name} (parent: {parent_name})"
                )
                return PipelineValidator(self.server.validation_context)
        return None

    def _convert_diagnostic(self, pype_diag) -> types.Diagnostic:
        """Convert bio_pype diagnostic to LSP diagnostic.

        Args:
            pype_diag: Diagnostic from pype.validation module

        Returns:
            LSP-compatible Diagnostic
        """
        # Map severity levels
        severity_map = {
            DiagnosticSeverity.ERROR: types.DiagnosticSeverity.Error,
            DiagnosticSeverity.WARNING: types.DiagnosticSeverity.Warning,
            DiagnosticSeverity.INFO: types.DiagnosticSeverity.Information,
        }

        # Create LSP Range from Location
        start_pos = types.Position(
            line=pype_diag.location.line,
            character=pype_diag.location.start_char,
        )
        end_pos = types.Position(
            line=pype_diag.location.line,
            character=pype_diag.location.end_char,
        )

        return types.Diagnostic(
            range=types.Range(start=start_pos, end=end_pos),
            severity=severity_map.get(
                pype_diag.severity, types.DiagnosticSeverity.Error
            ),
            code=pype_diag.code,
            message=pype_diag.message,
            source="bio_pype",
        )
