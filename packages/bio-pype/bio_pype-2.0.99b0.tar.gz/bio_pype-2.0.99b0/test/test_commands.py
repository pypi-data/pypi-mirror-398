"""Unit tests for pype.commands module.

Tests the main CLI entry point including:
- Profile configuration and defaults
- Module loading and registration
- Command-line argument parsing
- Subcommand dispatching
- Error handling for missing/invalid inputs
"""

import unittest
from io import StringIO
from unittest.mock import MagicMock, PropertyMock, patch

from pype.commands import main
from pype.exceptions import ProfileError


class TestMainProfileDetection(unittest.TestCase):
    """Test profile detection and default profile selection."""

    @patch("pype.commands.get_profiles")
    @patch("pype.commands.PYPE_PROFILES")
    @patch("pype.commands.get_modules")
    @patch("pype.commands.DefaultHelpParser")
    def test_default_profile_from_pype_profiles(
        self, mock_parser, mock_modules, mock_pype_profiles, mock_get_profiles
    ):
        """Test that default profile is used when set in PYPE_PROFILES."""
        # Setup
        mock_pype_profiles.default = "default"
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_known_args.return_value = (
            MagicMock(module=None, profile="default"),
            [],
        )
        mock_parser.return_value = mock_parser_instance
        mock_modules.return_value = {}

        # Execute
        main()

        # Verify
        mock_parser_instance.print_help.assert_called_once()

    @patch("pype.commands.get_profiles")
    @patch("pype.commands.PYPE_PROFILES")
    @patch("pype.commands.get_modules")
    @patch("pype.commands.DefaultHelpParser")
    def test_default_profile_from_profiles_dict(
        self, mock_parser, mock_modules, mock_pype_profiles, mock_get_profiles
    ):
        """Test fallback to 'default' profile from get_profiles() when PYPE_PROFILES has no default."""
        # Setup
        del mock_pype_profiles.default
        mock_get_profiles.return_value = {"default": {}, "other": {}}
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_known_args.return_value = (
            MagicMock(module=None, profile="default"),
            [],
        )
        mock_parser.return_value = mock_parser_instance
        mock_modules.return_value = {}

        # Execute
        main()

        # Verify
        mock_parser_instance.print_help.assert_called_once()

    @patch("pype.commands.get_profiles")
    @patch("pype.commands.PYPE_PROFILES")
    @patch("pype.commands.get_modules")
    @patch("pype.commands.DefaultHelpParser")
    def test_single_profile_fallback(
        self, mock_parser, mock_modules, mock_pype_profiles, mock_get_profiles
    ):
        """Test that single profile is used when 'default' doesn't exist."""
        # Setup
        del mock_pype_profiles.default
        mock_get_profiles.return_value = {"only_profile": {}}
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_known_args.return_value = (
            MagicMock(module=None, profile="only_profile"),
            [],
        )
        mock_parser.return_value = mock_parser_instance
        mock_modules.return_value = {}

        # Execute
        main()

        # Verify
        mock_parser_instance.print_help.assert_called_once()


class TestMainArgumentParsing(unittest.TestCase):
    """Test command-line argument parsing."""

    @patch("pype.commands.get_profiles")
    @patch("pype.commands.PYPE_PROFILES")
    @patch("pype.commands.get_modules")
    @patch("pype.commands.DefaultHelpParser")
    def test_no_module_specified(
        self, mock_parser, mock_modules, mock_pype_profiles, mock_get_profiles
    ):
        """Test behavior when no module is specified."""
        # Setup
        mock_pype_profiles.default = "default"
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_known_args.return_value = (
            MagicMock(module=None, profile="default"),
            [],
        )
        mock_parser.return_value = mock_parser_instance
        mock_modules.return_value = {}

        # Execute
        result = main()

        # Verify help is printed
        mock_parser_instance.print_help.assert_called_once()


class TestMainModuleDispatch(unittest.TestCase):
    """Test module loading and dispatching."""

    @patch("pype.commands.get_profiles")
    @patch("pype.commands.PYPE_PROFILES")
    @patch("pype.commands.get_modules")
    @patch("pype.commands.DefaultHelpParser")
    def test_valid_module_dispatch(
        self, mock_parser, mock_modules, mock_pype_profiles, mock_get_profiles
    ):
        """Test that valid module is correctly dispatched."""
        # Setup
        mock_pype_profiles.default = "default"
        mock_module_func = MagicMock()
        mock_modules_dict = {"pipelines": mock_module_func}

        mock_parser_instance = MagicMock()
        mock_subparsers = MagicMock()
        mock_parser_instance.add_subparsers.return_value = mock_subparsers
        mock_parser_instance.parse_known_args.return_value = (
            MagicMock(module="pipelines", profile="default"),
            ["arg1", "arg2"],
        )
        mock_parser.return_value = mock_parser_instance
        mock_modules.return_value = mock_modules_dict

        # Execute
        main()

        # Verify module function was called with correct arguments
        mock_module_func.assert_called_once_with(
            mock_subparsers, "pipelines", ["arg1", "arg2"], "default"
        )

    @patch("pype.commands.get_profiles")
    @patch("pype.commands.PYPE_PROFILES")
    @patch("pype.commands.get_modules")
    @patch("pype.commands.DefaultHelpParser")
    def test_invalid_module(
        self, mock_parser, mock_modules, mock_pype_profiles, mock_get_profiles
    ):
        """Test handling of invalid module name."""
        # Setup
        mock_pype_profiles.default = "default"
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_known_args.return_value = (
            MagicMock(module="nonexistent", profile="default"),
            [],
        )
        mock_parser_instance.parse_args.return_value = MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_modules.return_value = {"pipelines": MagicMock()}

        # Execute
        result = main()

        # Verify parse_args was called (fallback for invalid module)
        mock_parser_instance.parse_args.assert_called_once()


class TestMainIntegration(unittest.TestCase):
    """Integration tests for main() with mocked components."""

    @patch("pype.commands.get_profiles")
    @patch("pype.commands.PYPE_PROFILES")
    @patch("pype.commands.get_modules")
    @patch("pype.commands.DefaultHelpParser")
    def test_version_info_in_parser(
        self, mock_parser, mock_modules, mock_pype_profiles, mock_get_profiles
    ):
        """Test that version info is included in parser epilog."""
        # Setup
        mock_pype_profiles.default = "default"
        mock_get_profiles.return_value = {"default": {}}
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_known_args.return_value = (
            MagicMock(module=None, profile="default"),
            [],
        )
        mock_parser.return_value = mock_parser_instance
        mock_modules.return_value = {}

        # Execute
        main()

        # Verify parser was created with version info
        call_kwargs = mock_parser.call_args[1]
        self.assertIn("epilog", call_kwargs)
        self.assertIn("version", call_kwargs["epilog"].lower())


class TestProfileErrorHandling(unittest.TestCase):
    """Test profile-related error handling."""

    @patch("pype.commands.get_profiles")
    @patch("pype.commands.PYPE_PROFILES")
    @patch("pype.commands.get_modules")
    @patch("pype.commands.DefaultHelpParser")
    def test_multiple_profiles_no_default(
        self, mock_parser, mock_modules, mock_pype_profiles, mock_get_profiles
    ):
        """Test ProfileError when multiple profiles exist but no default."""
        # Setup
        del mock_pype_profiles.default
        mock_get_profiles.return_value = {
            "profile1": {},
            "profile2": {},
            "profile3": {},
        }
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_known_args.return_value = (
            MagicMock(module=None),
            [],
        )
        mock_parser.return_value = mock_parser_instance
        mock_modules.return_value = {}

        # Execute & Verify - should raise ProfileError with multiple profiles but no default
        with self.assertRaises(ProfileError):
            main()


if __name__ == "__main__":
    unittest.main()
