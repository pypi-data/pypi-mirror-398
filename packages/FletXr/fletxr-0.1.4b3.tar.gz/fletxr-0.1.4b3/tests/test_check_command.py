"""
Tests for the fletx check command.
"""

import pytest
import json
import sys
from unittest.mock import patch, MagicMock
from fletx.cli.commands.check import CheckCommand
from fletx.utils.version_checker import VersionChecker, CompatibilityResult, VersionInfo


class TestCheckCommand:
    """Test cases for the CheckCommand class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.command = CheckCommand()
    
    def test_command_name(self):
        """Test that the command has the correct name."""
        assert self.command.command_name == "check"
    
    def test_command_description(self):
        """Test that the command has a proper description."""
        description = self.command.get_description()
        assert "compatibility" in description.lower()
        assert "fletx" in description.lower()
        assert "flet" in description.lower()
    
    def test_missing_args_message(self):
        """Test that no missing args message is returned."""
        assert self.command.get_missing_args_message() is None
    
    @patch('fletx.cli.commands.check.VersionChecker')
    def test_handle_compatible_versions(self, mock_checker_class):
        """Test handling of compatible versions."""
        # Mock the checker and result
        mock_checker = MagicMock()
        mock_checker_class.return_value = mock_checker
        
        compatible_result = CompatibilityResult(
            is_compatible=True,
            fletx_version=VersionInfo("0.1.4", "FletX"),
            flet_version=VersionInfo("0.28.3", "Flet"),
            message="Versions are compatible"
        )
        mock_checker.check_compatibility.return_value = compatible_result
        
        # Test with default arguments
        with patch('sys.stdout') as mock_stdout:
            self.command.handle()
            
            # Verify the checker was called
            mock_checker.check_compatibility.assert_called_once()
            
            # Verify output was written
            assert mock_stdout.write.called
    
    @patch('fletx.cli.commands.check.VersionChecker')
    def test_handle_incompatible_versions(self, mock_checker_class):
        """Test handling of incompatible versions."""
        # Mock the checker and result
        mock_checker = MagicMock()
        mock_checker_class.return_value = mock_checker
        
        incompatible_result = CompatibilityResult(
            is_compatible=False,
            fletx_version=VersionInfo("0.1.4", "FletX"),
            flet_version=VersionInfo("0.20.0", "Flet"),
            message="Versions are incompatible",
            suggestions=["Upgrade Flet to 0.28.3 or later"]
        )
        mock_checker.check_compatibility.return_value = incompatible_result
        
        # Test with default arguments
        with patch('sys.stdout') as mock_stdout:
            self.command.handle()
            
            # Verify the checker was called
            mock_checker.check_compatibility.assert_called_once()
            
            # Verify output was written
            assert mock_stdout.write.called
    
    @patch('fletx.cli.commands.check.VersionChecker')
    def test_handle_json_output(self, mock_checker_class):
        """Test JSON output format."""
        # Mock the checker and result
        mock_checker = MagicMock()
        mock_checker_class.return_value = mock_checker
        
        result = CompatibilityResult(
            is_compatible=True,
            fletx_version=VersionInfo("0.1.4", "FletX"),
            flet_version=VersionInfo("0.28.3", "Flet"),
            message="Versions are compatible"
        )
        mock_checker.check_compatibility.return_value = result
        
        # Test with JSON output
        with patch('sys.stdout') as mock_stdout:
            self.command.handle(json=True)
            
            # Verify the checker was called
            mock_checker.check_compatibility.assert_called_once()
            
            # Verify JSON output was written
            assert mock_stdout.write.called
    
    @patch('fletx.cli.commands.check.VersionChecker')
    def test_handle_quiet_mode(self, mock_checker_class):
        """Test quiet mode output."""
        # Mock the checker and result
        mock_checker = MagicMock()
        mock_checker_class.return_value = mock_checker
        
        result = CompatibilityResult(
            is_compatible=True,
            fletx_version=VersionInfo("0.1.4", "FletX"),
            flet_version=VersionInfo("0.28.3", "Flet"),
            message="Versions are compatible"
        )
        mock_checker.check_compatibility.return_value = result
        
        # Test with quiet mode
        with patch('sys.stdout') as mock_stdout:
            self.command.handle(quiet=True)
            
            # Verify the checker was called
            mock_checker.check_compatibility.assert_called_once()
            
            # Verify output was written
            assert mock_stdout.write.called
    
    @patch('fletx.cli.commands.check.VersionChecker')
    def test_handle_exit_code_incompatible(self, mock_checker_class):
        """Test exit code behavior for incompatible versions."""
        # Mock the checker and result
        mock_checker = MagicMock()
        mock_checker_class.return_value = mock_checker
        
        incompatible_result = CompatibilityResult(
            is_compatible=False,
            fletx_version=VersionInfo("0.1.4", "FletX"),
            flet_version=VersionInfo("0.20.0", "Flet"),
            message="Versions are incompatible"
        )
        mock_checker.check_compatibility.return_value = incompatible_result
        
        # Test with exit code enabled
        with patch('sys.exit') as mock_exit:
            with patch('sys.stdout'):
                self.command.handle(exit_code=True)
                
                # Verify sys.exit was called with code 1
                mock_exit.assert_called_once_with(1)
    
    @patch('fletx.cli.commands.check.VersionChecker')
    def test_handle_exit_code_compatible(self, mock_checker_class):
        """Test exit code behavior for compatible versions."""
        # Mock the checker and result
        mock_checker = MagicMock()
        mock_checker_class.return_value = mock_checker
        
        compatible_result = CompatibilityResult(
            is_compatible=True,
            fletx_version=VersionInfo("0.1.4", "FletX"),
            flet_version=VersionInfo("0.28.3", "Flet"),
            message="Versions are compatible"
        )
        mock_checker.check_compatibility.return_value = compatible_result
        
        # Test with exit code enabled
        with patch('sys.exit') as mock_exit:
            with patch('sys.stdout'):
                self.command.handle(exit_code=True)
                
                # Verify sys.exit was not called
                mock_exit.assert_not_called()
    
    @patch('fletx.cli.commands.check.VersionChecker')
    def test_handle_exception(self, mock_checker_class):
        """Test handling of exceptions."""
        # Mock the checker to raise an exception
        mock_checker = MagicMock()
        mock_checker_class.return_value = mock_checker
        mock_checker.check_compatibility.side_effect = Exception("Test error")
        
        # Test with default arguments
        with patch('sys.stdout') as mock_stdout:
            self.command.handle()
            
            # Verify error output was written
            assert mock_stdout.write.called
    
    def test_add_arguments(self):
        """Test that arguments are properly added to the parser."""
        from fletx.cli.commands import CommandParser
        
        parser = CommandParser()
        self.command.add_arguments(parser)
        
        # Check that the expected arguments exist
        actions = [action.dest for action in parser._actions]
        assert 'json' in actions
        assert 'quiet' in actions
        assert 'exit_code' in actions


class TestVersionChecker:
    """Test cases for the VersionChecker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = VersionChecker()
    
    def test_compatibility_matrix_structure(self):
        """Test that the compatibility matrix has the expected structure."""
        matrix = VersionChecker.COMPATIBILITY_MATRIX
        
        # Check that all entries have required keys
        for version, requirements in matrix.items():
            assert 'flet' in requirements
            assert 'python' in requirements
            
            # Check that version strings are valid
            assert isinstance(version, str)
            assert isinstance(requirements['flet'], str)
            assert isinstance(requirements['python'], str)
    
    def test_version_info_creation(self):
        """Test VersionInfo object creation."""
        version_info = VersionInfo("1.2.3", "TestPackage")
        
        assert version_info.version_str == "1.2.3"
        assert version_info.package_name == "TestPackage"
        assert str(version_info) == "TestPackage v1.2.3"
    
    def test_compatibility_result_creation(self):
        """Test CompatibilityResult object creation."""
        fletx_version = VersionInfo("0.1.4", "FletX")
        flet_version = VersionInfo("0.28.3", "Flet")
        
        result = CompatibilityResult(
            is_compatible=True,
            fletx_version=fletx_version,
            flet_version=flet_version,
            message="Test message",
            suggestions=["Test suggestion"]
        )
        
        assert result.is_compatible is True
        assert result.fletx_version == fletx_version
        assert result.flet_version == flet_version
        assert result.message == "Test message"
        assert result.suggestions == ["Test suggestion"]
    
    def test_normalize_version_for_matrix(self):
        """Test version normalization for matrix lookup."""
        # Test with pre-release version
        normalized = self.checker._normalize_version_for_matrix("0.1.4.b1")
        assert normalized == "0.1.4"
        
        # Test with regular version
        normalized = self.checker._normalize_version_for_matrix("0.1.4")
        assert normalized == "0.1.4"
    
    def test_version_matches(self):
        """Test version matching logic."""
        # Test matching versions (same major.minor)
        assert self.checker._version_matches("0.1.4", "0.1.4")
        assert self.checker._version_matches("0.1.4.b1", "0.1.4")
        assert self.checker._version_matches("0.1.4.1", "0.1.4")
        assert self.checker._version_matches("0.1.3", "0.1.4")  # Same major.minor
        
        # Test non-matching versions (different major.minor)
        assert not self.checker._version_matches("0.2.4", "0.1.4")
        assert not self.checker._version_matches("1.1.4", "0.1.4")
        assert not self.checker._version_matches("0.0.4", "0.1.4")
