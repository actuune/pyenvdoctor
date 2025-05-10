import pytest
import subprocess
from unittest.mock import patch, MagicMock
from src.pyenvdoctor.scanner.system_scanner import SystemScanner

class TestSystemScanner:
    @pytest.fixture
    def scanner(self):
        return SystemScanner()
        
    def test_detect_system_python(self, scanner):
        """Test system Python detection"""
        scanner._detect_system_python()
        assert len(scanner.installations) > 0
        
    @patch('subprocess.run')
    def test_verify_installation_success(self, mock_run, scanner):
        """Test successful Python installation verification"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="OK\n",
            stderr=""
        )
        
        result = scanner._verify_installation("/usr/bin/python3")
        assert result is True
        
    @patch('subprocess.run')
    def test_verify_installation_failure(self, mock_run, scanner):
        """Test failed Python installation verification"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error"
        )
        
        result = scanner._verify_installation("/usr/bin/python3")
        assert result is False
        
    def test_comprehensive_scan(self, scanner):
        """Test comprehensive scan functionality"""
        issues = scanner.scan(comprehensive=True)
        assert isinstance(issues, list)
        
    def test_command_exists(self, scanner):
        """Test command existence checking"""
        # Test with a command that should exist
        assert scanner._command_exists("python3") is True
        
        # Test with a command that shouldn't exist
        assert scanner._command_exists("nonexistent_command_12345") is False
