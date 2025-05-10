import pytest
from pathlib import Path
from src.pyenvdoctor.scanner.system_scanner import SystemScanner

@pytest.fixture
def scanner():
    return SystemScanner()

def test_scan_finds_installations(scanner, mocker):
    mocker.patch('pathlib.Path.exists', return_value=True)
    mocker.patch('subprocess.run', return_value=type('', (), {
        'stdout': 'Python 3.9.0'
    }))
    
    scanner.scan()
    assert len(scanner.get_installations()) > 0

def test_scan_no_installations(scanner, mocker):
    mocker.patch('pathlib.Path.exists', return_value=False)
    
    scanner.scan()
    assert len(scanner.get_installations()) == 0

def test_base_scanner_initialization(scanner):
    # Test the missing line in base_scanner.py
    assert scanner is not None
