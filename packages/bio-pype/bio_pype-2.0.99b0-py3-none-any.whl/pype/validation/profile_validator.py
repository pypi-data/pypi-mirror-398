"""Profile validation implementation.

Validates bio_pype YAML profile configurations using the Profile class.
The Profile class handles all YAML loading, parsing, and structure validation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from pype.exceptions import CommandNamespaceError, ProfileError
from pype.process import Namespace
from pype.utils.profiles import Profile
from pype.validation.core import (
    Diagnostic,
    DiagnosticSeverity,
    Location,
    ValidationContext,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class ProfileValidator:
    """Validator for bio_pype YAML profiles.

    Uses the Profile class from pype.utils.profiles for all validation.
    The Profile class handles:
    - YAML loading and parsing
    - Structure validation
    - Program conversion to ProfileProgram objects
    - All attribute setting and validation

    Structure follows the snippet validator pattern for consistency.
    """

    def __init__(self, context: ValidationContext) -> None:
        """Initialize profile validator.

        Args:
            context: ValidationContext for workspace information
        """
        self.context = context
        self.diagnostics: List[Diagnostic] = []
        self.file_lines: List[str] = []
        self.profile: Optional[Profile] = None
        self.profile_files: Dict[str, str] = {}
        self.profile_programs: Dict[str, str] = {}

    def _add_diagnostic(
        self,
        severity: DiagnosticSeverity,
        line: int,
        start_char: int,
        end_char: int,
        message: str,
        code: str,
    ) -> None:
        """Add a diagnostic to the list."""
        self.diagnostics.append(
            Diagnostic(
                severity=severity,
                location=Location(line, start_char, end_char),
                message=message,
                code=code,
            )
        )

    def _load_file_lines(self, file_path: Path) -> None:
        """Load file into memory for line number lookup."""
        if not self.file_lines:
            with open(file_path, "rt") as f:
                self.file_lines = f.readlines()

    def _get_line_nr(self, words_match: List[str]) -> int:
        """Find line number for a section, using pre-loaded file lines.

        Args:
            words_match: List of words that must all appear on the line

        Returns:
            0-based line number, or 0 if not found
        """
        for line_nr, line in enumerate(self.file_lines):
            if all(x in line for x in words_match):
                return line_nr
        return 0

    def _load_profile(self, file_path: Path) -> None:
        """Load profile using Profile class. Handles exceptions as diagnostics.

        Args:
            file_path: Path to profile file
        """
        if self.profile is not None:
            return  # Already loaded

        try:
            profile_name = file_path.stem
            self.profile = Profile(str(file_path), profile_name)

        except ProfileError as e:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                0,
                0,
                10,
                f"Profile validation failed: {e}",
                "profile-error",
            )

        except Exception as e:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                0,
                0,
                10,
                f"Failed to load profile: {e}",
                "profile-load-error",
            )

    def _validate_files(self) -> None:
        """Validate profile files and extract file mappings."""
        if not self.profile:
            return

        for profile_file in self.profile.files:
            file_value = self.profile.files[profile_file]
            if isinstance(file_value, str):
                self.profile_files[profile_file] = (
                    f"{self.profile.__name__}: {file_value}"
                )
            else:
                line_nr = self._get_line_nr([profile_file, ":"])
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    line_nr,
                    0,
                    10,
                    f"Profile file: {profile_file} is not a string",
                    "profile-file-error",
                )

    def _validate_programs(self) -> None:
        """Validate profile programs and extract program mappings."""
        if not self.profile:
            return

        for profile_program in self.profile.programs:
            try:
                self.profile_programs[profile_program] = Namespace(
                    self.profile.programs[profile_program], logger, self.profile
                ).namespace
            except CommandNamespaceError as e:
                line_nr = self._get_line_nr([profile_program, ":"])
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    line_nr,
                    0,
                    10,
                    f"Profile program {profile_program} error: {e}",
                    "profile-program-error",
                )

    def validate(self, file_path: Path) -> ValidationResult:
        """Validate a profile file by attempting to load it with the Profile class.

        The Profile class does all the validation - if it loads successfully,
        the profile is valid. If it raises an exception, that's a validation error.

        Args:
            file_path: Path to the profile file to validate

        Returns:
            ValidationResult with diagnostics
        """
        # Reset state for fresh validation
        self.diagnostics = []
        self.file_lines = []
        self.profile = None
        self.profile_files = {}
        self.profile_programs = {}

        # Load file for line number lookup
        try:
            self._load_file_lines(file_path)
        except IOError as e:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                0,
                0,
                10,
                f"Failed to read file: {e}",
                "file-read-error",
            )
            return ValidationResult(file_path, "profile", self.diagnostics, False)

        # Load profile (handles exceptions internally)
        self._load_profile(file_path)

        # Validate profile components
        self._validate_files()
        self._validate_programs()

        is_valid = not any(
            d.severity == DiagnosticSeverity.ERROR for d in self.diagnostics
        )
        return ValidationResult(file_path, "profile", self.diagnostics, is_valid)

    def load_profile(self, file_path: Path) -> tuple[Optional[Profile], List[Diagnostic]]:
        """Load a profile and return it with any diagnostics.

        This method uses cached data if available (from a previous validate() call),
        otherwise it performs validation first.

        Args:
            file_path: Path to the profile file

        Returns:
            Tuple of (Profile object or None, list of diagnostics)
        """
        # If not yet validated, run validation first
        if self.profile is None and not self.diagnostics:
            self._load_file_lines(file_path)
            self._load_profile(file_path)
            self._validate_files()
            self._validate_programs()

        return self.profile, self.diagnostics

    def extract_profile_files(self, profile_path: Path) -> Dict[str, str]:
        """Extract profile files from a loaded Profile object.

        Uses cached data if available (from a previous validate() or load_profile() call).

        Args:
            profile_path: Path to the profile file

        Returns:
            Dict mapping file keys to file paths, or empty dict if profile is None
        """
        # Ensure profile is loaded
        if self.profile is None and not self.diagnostics:
            self._load_file_lines(profile_path)
            self._load_profile(profile_path)
            self._validate_files()

        return self.profile_files

    def extract_profile_programs(self, profile_path: Path) -> Dict[str, str]:
        """Extract profile programs from a loaded Profile object.

        Uses cached data if available (from a previous validate() or load_profile() call).

        Args:
            profile_path: Path to the profile file

        Returns:
            Dict mapping program names to namespace strings, or empty dict if profile is None
        """
        # Ensure profile is loaded
        if self.profile is None and not self.diagnostics:
            self._load_file_lines(profile_path)
            self._load_profile(profile_path)
            self._validate_programs()

        return self.profile_programs
