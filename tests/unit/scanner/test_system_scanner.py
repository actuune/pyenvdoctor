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
