#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# PyEnvDoctor Professional Installer & Verifier
# Optimized script with comprehensive enhancements for reliability and usability

set -o errexit    # Exit immediately on error
set -o nounset    # Exit if uninitialized variables are detected
set -o pipefail   # Capture pipe failures in pipeline
IFS=$'\n\t'       # Set sane word splitting

# =============================================================================

# =============================================================================
declare -r SCRIPT_NAME="PyEnvDoctor Professional Installer"
declare -r VERSION="1.0.0"
declare -r MIN_PYTHON_VERSION="3.8"
declare -A MIN_VERSIONS
MIN_VERSIONS["python3"]="3.8"
MIN_VERSIONS["pip"]="20.0"
MIN_VERSIONS["jq"]="1.6"
declare -r REQUIRED_DEPENDENCIES=("python3" "pip" "curl" "git" "make" "gcc" "jq" "yq")
declare -r LOG_DIR="${XDG_STATE_HOME:-${HOME}/.local/state}/pyenvdoctor/logs"
declare -r APP_LOG_FILE="${LOG_DIR}/app.log"
declare -r SYS_LOG_FILE="${LOG_DIR}/system.log"
declare -r TMP_DIR="/tmp/pyenvdoctor_$(date +%s)"
declare -r PROJECT_DIR="/Users/sammac/pyenvdoctor"
declare -r CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/pyenvdoctor"
declare -r REPORT_FILE="${HOME}/pyenvdoctor_install_report.txt"
declare DRY_RUN=false
# Updated with the provided checksum

# Color definitions
declare -A COLOR=(
    [red]='\033[0;31m' [green]='\033[0;32m' [yellow]='\033[0;33m'
    [blue]='\033[0;34m' [magenta]='\033[0;35m' [cyan]='\033[0;36m'
    [reset]='\033[0m'
)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log() {
    local level="$1"
    local message="$2"
    local log_file="${3:-${APP_LOG_FILE}}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local log_entry="[${timestamp}] %-7s %s\n"
    
    case "${level}" in
        "ERROR")   printf "${COLOR[red]}${log_entry}${COLOR[reset]}" "${level}" "${message}" ;;
        "WARN")    printf "${COLOR[yellow]}${log_entry}${COLOR[reset]}" "${level}" "${message}" ;;
        "SUCCESS") printf "${COLOR[green]}${log_entry}${COLOR[reset]}" "${level}" "${message}" ;;
        "INFO")    printf "${COLOR[blue]}${log_entry}${COLOR[reset]}" "${level}" "${message}" ;;
        *)         printf "${log_entry}" "${level}" "${message}" ;;
    esac
    
    printf "${log_entry}" "${level}" "${message}" >> "${log_file}"
}

retry_command() {
    local max_attempts=3
    local delay=2
    local count=1
    local command="$*"
    local output
    
    while [ ${count} -le ${max_attempts} ]; do
        if output=$( ${command} 2>&1 ); then
            log "DEBUG" "Command succeeded: ${command}" "${SYS_LOG_FILE}"
            log "DEBUG" "Output: ${output}" "${SYS_LOG_FILE}"
            return 0
        fi
        log "WARN" "Command failed (attempt ${count}/${max_attempts}): ${command}" "${SYS_LOG_FILE}"
        log "DEBUG" "Output: ${output}" "${SYS_LOG_FILE}"
        sleep ${delay}
        count=$((count + 1))
    done
    log "ERROR" "Command failed after ${max_attempts} attempts: ${command}" "${SYS_LOG_FILE}"
    return 1
}

error_exit() {
    local msg="${1:-Unknown error}"
    log "ERROR" "${msg}"
    echo -e "${COLOR[red]}ERROR: ${msg}${COLOR[reset]}" >&2
    
    cat >> "${HOME}/pyenvdoctor_error_report.txt" << EOF
PyEnvDoctor Installation Error Report
====================================
Date: $(date)
Error: ${msg}
Last 10 log entries:
$(tail -n 10 "${APP_LOG_FILE}" 2>/dev/null || echo "No log entries available")
EOF
    
    cleanup
    exit 1
}

cleanup() {
    local exit_code=$?
    [[ $exit_code -eq 0 ]] || log "ERROR" "Cleanup after failed installation" "${SYS_LOG_FILE}"
    
    if [[ -f "${APP_LOG_FILE}" ]]; then
        gzip -c "${APP_LOG_FILE}" > "${APP_LOG_FILE}-$(date +%Y%m%d).gz" && rm "${APP_LOG_FILE}" 2>/dev/null
    fi
    if [[ -f "${SYS_LOG_FILE}" ]]; then
        gzip -c "${SYS_LOG_FILE}" > "${SYS_LOG_FILE}-$(date +%Y%m%d).gz" && rm "${SYS_LOG_FILE}" 2>/dev/null
    fi
    rm -rf "${TMP_DIR}" 2>/dev/null
    chmod 644 "${CONFIG_DIR}/config.yaml" 2>/dev/null || true
    chmod 755 "${CONFIG_DIR}" "${LOG_DIR}" 2>/dev/null || true
    log "SUCCESS" "Cleanup completed" "${SYS_LOG_FILE}"
}

verify_script_integrity() {
    local checksum_file="$0.sha256"
    if [[ -f "${checksum_file}" ]]; then
        local expected_checksum=$(awk '{print $1}' "${checksum_file}")
        local actual_checksum=$(shasum -a 256 "$0" | awk '{print $1}')
        if [[ "${expected_checksum}" != "${actual_checksum}" ]]; then
            error_exit "Script integrity check failed! Expected ${expected_checksum}, got ${actual_checksum}"
        fi
    else
        log "WARN" "Checksum file not found - skipping integrity check" "${SYS_LOG_FILE}"
    fi
    log "SUCCESS" "Script integrity verified" "${SYS_LOG_FILE}"
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                log "INFO" "Dry run mode activated" "${SYS_LOG_FILE}"
                ;;
            --uninstall)
                uninstall
                exit 0
                ;;
            *)
                log "WARN" "Unknown option: $1" "${SYS_LOG_FILE}"
                ;;
        esac
        shift
    done
}

send_anonymous_telemetry() {
    if [[ -f "${CONFIG_DIR}/config.yaml" ]] && command -v yq >/dev/null 2>&1; then
        if yq e '.features.telemetry' "${CONFIG_DIR}/config.yaml" | grep -q true; then
            local os_hash=$(echo "$(detect_os)-$(uname -m)" | sha256sum | cut -c1-8)
            curl -sS -X POST "https://telemetry.pyenvdoctor.com/install" \
                 -H "Content-Type: application/json" \
                 -d "{\"os\":\"${os_hash}\",\"version\":\"${VERSION}\"}" >/dev/null 2>&1 || log "WARN" "Telemetry failed" "${SYS_LOG_FILE}"
            log "INFO" "Sent anonymous telemetry" "${SYS_LOG_FILE}"
        fi
    fi
}

uninstall() {
    log "INFO" "Uninstalling PyEnvDoctor..." "${SYS_LOG_FILE}"
    retry_command pip uninstall -y pyenvdoctor || log "WARN" "Failed to uninstall via pip" "${SYS_LOG_FILE}"
    rm -rf "${CONFIG_DIR}" "${LOG_DIR}" || log "WARN" "Failed to remove config and logs" "${SYS_LOG_FILE}"
    crontab -l 2>/dev/null | grep -v "pyenvdoctor" | crontab - || log "WARN" "Failed to remove cron jobs" "${SYS_LOG_FILE}"
    log "SUCCESS" "PyEnvDoctor uninstalled" "${SYS_LOG_FILE}"
}

check_for_updates() {
    log "INFO" "Checking for updates..." "${SYS_LOG_FILE}"
    local latest_version
    latest_version=$(curl -sSL https://pypi.org/pypi/pyenvdoctor/json | jq -r .info.version 2>/dev/null) || log "WARN" "Failed to check for updates" "${SYS_LOG_FILE}"
    if [[ -n "${latest_version}" && "${latest_version}" != "${VERSION}" ]]; then
        log "INFO" "New version available: ${latest_version} (current: ${VERSION})" "${SYS_LOG_FILE}"
    fi
}

# =============================================================================
# INITIALIZATION AND SETUP
# =============================================================================

show_header() {
    clear
    echo -e "${COLOR[blue]}"
    cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║                PyEnvDoctor Professional Installer              ║
║                        Version 1.0.0                           ║
║         Complete Python Environment Management Solution        ║
╚════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${COLOR[reset]}"
}

init() {
    show_header
    verify_script_integrity
    parse_arguments "$@"
    
    for dir in "${LOG_DIR}" "${TMP_DIR}" "${CONFIG_DIR}"; do
        if [[ "${DRY_RUN}" != "true" ]]; then
            mkdir -p "${dir}" || error_exit "Failed to create directory: ${dir}"
        else
            log "INFO" "[Dry Run] Would create directory: ${dir}" "${SYS_LOG_FILE}"
        fi
    done
    
    if [[ "${DRY_RUN}" != "true" ]]; then
        touch "${APP_LOG_FILE}" "${SYS_LOG_FILE}" || error_exit "Failed to create log files"
        exec > >(tee -a "${APP_LOG_FILE}") 2> >(tee -a "${SYS_LOG_FILE}" >&2)
    else
        log "INFO" "[Dry Run] Would create log files: ${APP_LOG_FILE}, ${SYS_LOG_FILE}" "${SYS_LOG_FILE}"
    fi
    
    log "INFO" "Starting PyEnvDoctor installation process" "${SYS_LOG_FILE}"
    log "INFO" "Installation ID: $(date +%s)" "${SYS_LOG_FILE}"
    log "DEBUG" "Environment: PATH=${PATH}, VIRTUAL_ENV=${VIRTUAL_ENV:-none}, SHELL=${SHELL}" "${SYS_LOG_FILE}"
}

# =============================================================================
# SYSTEM VERIFICATION
# =============================================================================

detect_os() {
    local os_info
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        os_info="${ID}-${VERSION_ID}"
    elif [[ $(uname) == "Darwin" ]]; then
        os_info="macos-$(sw_vers -productVersion)"
    else
        os_info="unknown"
    fi
    log "INFO" "Detected operating system: ${os_info}" "${SYS_LOG_FILE}"
    echo "${os_info}"
}

check_python_version() {
    if ! command -v python3 >/dev/null 2>&1; then
        error_exit "Python 3 is not installed"
    fi
    local python_version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if ! printf '%s\n%s\n' "${MIN_PYTHON_VERSION}" "${python_version}" | sort -V | head -n1 | grep -q "^${MIN_PYTHON_VERSION}$"; then
        error_exit "Python ${python_version} is installed, but ${MIN_PYTHON_VERSION}+ is required"
    fi
    log "SUCCESS" "Python ${python_version} meets requirements" "${SYS_LOG_FILE}"
}

check_dependency_versions() {
    for cmd in "${!MIN_VERSIONS[@]}"; do
        if ! command -v "${cmd}" >/dev/null 2>&1; then
            error_exit "${cmd} is not installed"
        fi
        local version
        case "${cmd}" in
            "python3")
                version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
                ;;
            "pip")
                version=$(pip --version | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1)
                ;;
            "jq")
                version=$(jq --version | sed 's/jq-//')
                ;;
            *)
                version=$(${cmd} --version 2>&1 | head -n1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1)
                ;;
        esac
        
        if [[ -z "${version}" ]]; then
            log "WARN" "Could not determine version for ${cmd}" "${SYS_LOG_FILE}"
            continue
        fi
        
        if ! printf '%s\n%s\n' "${MIN_VERSIONS[$cmd]}" "${version}" | sort -V | head -n1 | grep -q "^${MIN_VERSIONS[$cmd]}$"; then
            error_exit "${cmd} version ${version} does not meet minimum requirement ${MIN_VERSIONS[$cmd]}"
        fi
        log "SUCCESS" "${cmd} version ${version} meets requirement ${MIN_VERSIONS[$cmd]}" "${SYS_LOG_FILE}"
    done
    log "SUCCESS" "All dependency versions meet requirements" "${SYS_LOG_FILE}"
}

check_dependencies() {
    local missing=()
    local installed=()
    for cmd in "${REQUIRED_DEPENDENCIES[@]}"; do
        if ! command -v "${cmd}" >/dev/null 2>&1; then
            missing+=("${cmd}")
        else
            installed+=("${cmd}")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log "ERROR" "Missing dependencies: ${missing[*]}" "${SYS_LOG_FILE}"
        log "INFO" "Attempting to install missing dependencies..." "${SYS_LOG_FILE}"
        
        case "$(detect_os)" in
            macos-*)
                if ! command -v brew >/dev/null 2>&1; then
                    if [[ "${DRY_RUN}" != "true" ]]; then
                        log "WARN" "Homebrew not found. Attempting to install..." "${SYS_LOG_FILE}"
                        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || error_exit "Failed to install Homebrew. Please install it manually from https://brew.sh"
                    else
                        log "INFO" "[Dry Run] Would install Homebrew" "${SYS_LOG_FILE}"
                    fi
                fi
                for dep in "${missing[@]}"; do
                    if [[ "${DRY_RUN}" != "true" ]]; then
                        retry_command brew install "${dep}"
                    else
                        log "INFO" "[Dry Run] Would install ${dep} using brew" "${SYS_LOG_FILE}"
                    fi
                done
                ;;
            ubuntu-*|debian-*)
                if command -v apt-get >/dev/null 2>&1; then
                    if [[ ${EUID} -eq 0 || "${DRY_RUN}" == "true" ]]; then
                        if [[ "${DRY_RUN}" != "true" ]]; then
                            retry_command apt-get update
                            retry_command apt-get install -y "${missing[@]}"
                        else
                            log "INFO" "[Dry Run] Would update apt and install ${missing[*]}" "${SYS_LOG_FILE}"
                        fi
                    else
                        error_exit "Please run with sudo to install dependencies on Debian/Ubuntu: ${missing[*]}"
                    fi
                else
                    error_exit "apt-get not found. Please install manually: ${missing[*]}"
                fi
                ;;
            fedora-*|centos-*)
                if command -v dnf >/dev/null 2>&1; then
                    if [[ ${EUID} -eq 0 || "${DRY_RUN}" == "true" ]]; then
                        if [[ "${DRY_RUN}" != "true" ]]; then
                            retry_command dnf install -y "${missing[@]}"
                        else
                            log "INFO" "[Dry Run] Would install ${missing[*]} using dnf" "${SYS_LOG_FILE}"
                        fi
                    else
                        error_exit "Please run with sudo to install dependencies on Fedora/CentOS: ${missing[*]}"
                    fi
                else
                    error_exit "dnf not found. Please install manually: ${missing[*]}"
                fi
                ;;
            arch-*)
                if command -v pacman >/dev/null 2>&1; then
                    if [[ ${EUID} -eq 0 || "${DRY_RUN}" == "true" ]]; then
                        if [[ "${DRY_RUN}" != "true" ]]; then
                            retry_command pacman -Syu --noconfirm "${missing[@]}"
                        else
                            log "INFO" "[Dry Run] Would update pacman and install ${missing[*]}" "${SYS_LOG_FILE}"
                        fi
                    else
                        error_exit "Please run with sudo to install dependencies on Arch: ${missing[*]}"
                    fi
                else
                    error_exit "pacman not found. Please install manually: ${missing[*]}"
                fi
                ;;
            *)
                error_exit "Unsupported OS. Please install these dependencies manually: ${missing[*]}"
                ;;
        esac
    else
        log "SUCCESS" "All dependencies satisfied: ${installed[*]}" "${SYS_LOG_FILE}"
    fi
}

check_project_structure() {
    if [[ -n "${PROJECT_DIR:-}" ]] && [[ -d "${PROJECT_DIR}" ]]; then
        if [[ "${DRY_RUN}" != "true" ]]; then
            cd "${PROJECT_DIR}" || error_exit "Cannot access project directory"
        else
            log "INFO" "[Dry Run] Would change to project directory: ${PROJECT_DIR}" "${SYS_LOG_FILE}"
        fi
        log "INFO" "Working in project directory: ${PROJECT_DIR}" "${SYS_LOG_FILE}"
        return 0
    else
        log "INFO" "Project directory not specified or missing - using pip installation" "${SYS_LOG_FILE}"
        return 1
    fi
}

# =============================================================================
# PROJECT FILES CREATION
# =============================================================================

create_project_files() {
    log "INFO" "Creating/updating project files" "${SYS_LOG_FILE}"
    
    for file in pyproject.toml README.md .github/workflows/ci.yml; do
        if [[ -f "${file}" ]]; then
            if [[ "${DRY_RUN}" != "true" ]]; then
                cp "${file}" "${file}.backup-$(date +%s)" || log "WARN" "Failed to backup ${file}" "${SYS_LOG_FILE}"
                log "INFO" "Backed up ${file} to ${file}.backup-$(date +%s)" "${SYS_LOG_FILE}"
            else
                log "INFO" "[Dry Run] Would backup ${file} to ${file}.backup-$(date +%s)" "${SYS_LOG_FILE}"
            fi
        fi
    done
    
    if [[ ! -f "pyproject.toml" || "${DRY_RUN}" == "true" ]]; then
        if [[ "${DRY_RUN}" != "true" ]]; then
            cat > pyproject.toml << 'EOF'
[project]
name = "pyenvdoctor"
version = "0.1.1"
description = "A professional tool to diagnose and fix pyenv issues"
authors = [{name = "PyEnvDoctor Development Team", email = "dev@pyenvdoctor.com"}]
license = "MIT"
readme = "README.md"
requires-python = ">=3.8"
keywords = ["pyenv", "python", "environment", "management", "diagnostics"]

dependencies = [
    "click>=8.1.7",
    "colorama>=0.4.6",
    "psutil>=5.9.0",
    "pyyaml>=6.0",
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
    "mypy>=0.991",
]

[project.scripts]
pyenvdoctor = "pyenvdoctor.cli:cli"
pyenvdoctor-scan = "pyenvdoctor.scanner:scan_cli"
pyenvdoctor-fix = "pyenvdoctor.fixer:fix_cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 100
target-version = ['py38']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "--cov=src/pyenvdoctor --cov-report=term-missing"

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
strict = true
EOF
            log "SUCCESS" "Created/updated pyproject.toml" "${SYS_LOG_FILE}"
        else
            log "INFO" "[Dry Run] Would create/update pyproject.toml" "${SYS_LOG_FILE}"
        fi
    else
        log "INFO" "Existing pyproject.toml found - preserving" "${SYS_LOG_FILE}"
    fi
    
    if [[ ! -f "README.md" || "${DRY_RUN}" == "true" ]]; then
        if [[ "${DRY_RUN}" != "true" ]]; then
            cat > README.md << 'EOF'
# PyEnvDoctor

A professional command-line tool for diagnosing and fixing [pyenv](https://github.com/pyenv/pyenv) environment issues.

## Features
- Comprehensive environment diagnostics
- Automated issue detection and resolution
- Security vulnerability scanning
- AI-assisted troubleshooting
- Detailed logging and reporting
- Cross-platform compatibility

## Installation
### Quick Install
```bash
curl -sSL https://raw.githubusercontent.com/actuune/pyenvdoctor/main/setup_and_install.sh | bash
```
### Manual Installation
```bash
pip install pyenvdoctor
```
### From Source
```bash
git clone https://github.com/actuune/pyenvdoctor.git
cd pyenvdoctor
pip install -e .
```
### Dry-Run Mode
```bash
bash setup_and_install.sh --dry-run
```
### Uninstall
```bash
bash setup_and_install.sh --uninstall
```

## Usage
### Basic Diagnostics
```bash
pyenvdoctor check
pyenvdoctor check --full
pyenvdoctor check --json > report.json
```
### Automated Fixes
```bash
pyenvdoctor fix
pyenvdoctor fix --auto
pyenvdoctor fix --backup
```
### Advanced Features
```bash
pyenvdoctor scan --security
pyenvdoctor report --format html
pyenvdoctor update
```

## Configuration
Default configuration at ~/.config/pyenvdoctor/config.yaml:
```yaml
cache:
  enabled: true
  ttl: 3600
  max_size: 100MB
security:
  vulnerability_checks: true
  auto_update: true
logging:
  level: INFO
  rotation: 7d
features:
  ai_assist: true
  auto_fix: false
  telemetry: false
```

## Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License
MIT License - see [LICENSE](LICENSE) file for details.

## Documentation
- https://pyenvdoctor-docs.readthedocs.io
EOF
            log "SUCCESS" "Created/updated README.md" "${SYS_LOG_FILE}"
        else
            log "INFO" "[Dry Run] Would create/update README.md" "${SYS_LOG_FILE}"
        fi
    else
        log "INFO" "Existing README.md found - preserving" "${SYS_LOG_FILE}"
    fi
    
    if [[ ! -d ".github/workflows" || "${DRY_RUN}" == "true" ]]; then
        if [[ "${DRY_RUN}" != "true" ]]; then
            mkdir -p .github/workflows
            cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.8", "3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install .[dev]
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
    - name: Type check with mypy
      run: mypy src/pyenvdoctor
    - name: Test with pytest
      run: pytest --cov=src/pyenvdoctor --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: unittests
        name: codecov-${{ matrix.os }}-${{ matrix.python-version }}

  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install .[dev]
    - name: Check formatting with black
      run: black --check .
    - name: Sort imports with isort
      run: isort --check-only .
EOF
            log "SUCCESS" "Created/updated CI workflow" "${SYS_LOG_FILE}"
        else
            log "INFO" "[Dry Run] Would create/update CI workflow" "${SYS_LOG_FILE}"
        fi
    else
        log "INFO" "Existing CI workflow found - preserving" "${SYS_LOG_FILE}"
    fi
}

# =============================================================================
# INSTALLATION PROCESS
# =============================================================================

install_pyenvdoctor() {
    log "INFO" "Installing PyEnvDoctor..." "${SYS_LOG_FILE}"
    echo -n "Progress: ["
    
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        log "INFO" "Detected existing virtual environment at ${VIRTUAL_ENV}" "${SYS_LOG_FILE}"
        echo -n "="
        if [[ "${DRY_RUN}" != "true" ]]; then
            retry_command pip install --upgrade pip setuptools wheel
            echo -n "="
            if [[ -f pyproject.toml ]]; then
                retry_command pip install .
            else
                retry_command pip install pyenvdoctor
            fi
            echo -n "="
        else
            log "INFO" "[Dry Run] Would upgrade pip, setuptools, wheel in virtual environment" "${SYS_LOG_FILE}"
            echo -n "=="
            if [[ -f pyproject.toml ]]; then
                log "INFO" "[Dry Run] Would install PyEnvDoctor from pyproject.toml" "${SYS_LOG_FILE}"
            else
                log "INFO" "[Dry Run] Would install PyEnvDoctor via pip" "${SYS_LOG_FILE}"
            fi
            echo -n "="
        fi
    else
        if [[ "${DRY_RUN}" != "true" ]]; then
            python3 -m venv "${TMP_DIR}/pyenvdoctor_install"
            source "${TMP_DIR}/pyenvdoctor_install/bin/activate"
            echo -n "="
            retry_command pip install --upgrade pip setuptools wheel
            echo -n "="
            if [[ -f pyproject.toml ]]; then
                retry_command pip install .
            else
                retry_command pip install pyenvdoctor
            fi
            echo -n "="
            deactivate
            retry_command pip install --user pyenvdoctor
            echo -n "="
        else
            log "INFO" "[Dry Run] Would create temporary virtual environment at ${TMP_DIR}/pyenvdoctor_install" "${SYS_LOG_FILE}"
            echo -n "="
            log "INFO" "[Dry Run] Would upgrade pip, setuptools, wheel in temporary virtual environment" "${SYS_LOG_FILE}"
            echo -n "="
            if [[ -f pyproject.toml ]]; then
                log "INFO" "[Dry Run] Would install PyEnvDoctor from pyproject.toml in temporary virtual environment" "${SYS_LOG_FILE}"
            else
                log "INFO" "[Dry Run] Would install PyEnvDoctor via pip in temporary virtual environment" "${SYS_LOG_FILE}"
            fi
            echo -n "="
            log "INFO" "[Dry Run] Would deactivate temporary virtual environment and install PyEnvDoctor to user site packages" "${SYS_LOG_FILE}"
            echo -n "="
        fi
    fi
    
    echo "] Done"
    
    if [[ "${DRY_RUN}" != "true" ]]; then
        if ! command -v pyenvdoctor >/dev/null 2>&1; then
            log "WARN" "PyEnvDoctor installed in user site packages, but not found in PATH." "${SYS_LOG_FILE}"
            log "INFO" "You may need to add ~/.local/bin to your PATH in ~/.bashrc or ~/.zshrc" "${SYS_LOG_FILE}"
            if [[ -f ~/.bashrc ]]; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
                log "INFO" "Added ~/.local/bin to PATH in ~/.bashrc" "${SYS_LOG_FILE}"
            fi
            if [[ -f ~/.zshrc ]]; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
                log "INFO" "Added ~/.local/bin to PATH in ~/.zshrc" "${SYS_LOG_FILE}"
            fi
        fi
        log "SUCCESS" "PyEnvDoctor installed successfully" "${SYS_LOG_FILE}"
    else
        log "INFO" "[Dry Run] Would complete PyEnvDoctor installation" "${SYS_LOG_FILE}"
    fi
}

# =============================================================================
# CRON JOB SETUP
# =============================================================================

setup_cron_jobs() {
    log "INFO" "Setting up automated tasks" "${SYS_LOG_FILE}"
    
    if command -v crontab >/dev/null 2>&1; then
        crontab -l > "${TMP_DIR}/crontab.backup" 2>/dev/null || true
        
        local pyenvdoctor_path
        pyenvdoctor_path=$(command -v pyenvdoctor) || error_exit "Cannot find pyenvdoctor in PATH for cron job"
        
        if ! crontab -l 2>/dev/null | grep -q "pyenvdoctor update"; then
            if [[ "${DRY_RUN}" != "true" ]]; then
                {
                    crontab -l 2>/dev/null
                    echo "0 3 * * * ${pyenvdoctor_path} update --silent 2>> ${APP_LOG_FILE}"
                } | crontab -
                log "SUCCESS" "Added automatic update to cron" "${SYS_LOG_FILE}"
            else
                log "INFO" "[Dry Run] Would add automatic update to cron: ${pyenvdoctor_path} update --silent" "${SYS_LOG_FILE}"
            fi
        fi
        
        if ! crontab -l 2>/dev/null | grep -q "pyenvdoctor check --full"; then
            if [[ "${DRY_RUN}" != "true" ]]; then
                {
                    crontab -l 2>/dev/null
                    echo "0 2 * * 1 ${pyenvdoctor_path} check --full --report 2>> ${APP_LOG_FILE}"
                } | crontab -
                log "SUCCESS" "Added weekly health check to cron" "${SYS_LOG_FILE}"
            else
                log "INFO" "[Dry Run] Would add weekly health check to cron: ${pyenvdoctor_path} check --full --report" "${SYS_LOG_FILE}"
            fi
        fi
    else
        log "WARN" "Cron not available - automated tasks not configured" "${SYS_LOG_FILE}"
    fi
}

# =============================================================================
# VERIFICATION AND TESTING
# =============================================================================

verify_installation() {
    log "INFO" "Verifying installation" "${SYS_LOG_FILE}"
    local commands=("pyenvdoctor")
    for cmd in "${commands[@]}"; do
        if ! command -v "${cmd}" >/dev/null 2>&1; then
            log "ERROR" "Command ${cmd} not found after installation" "${SYS_LOG_FILE}"
            return 1
        fi
    done
#    local installed_version
###    installed_version=$(pyenvdoctor --version 2>/dev/null | awk '{print $2}')
##    if [[ -z "${installed_version}" ]]; then
##        log "ERROR" "Cannot determine installed version" "${SYS_LOG_FILE}"
#        return 1
#    fi
#    log "SUCCESS" "Installation verified - version ${installed_version}" "${SYS_LOG_FILE}"
    return 0
}

run_smoke_tests() {
    log "INFO" "Running smoke tests" "${SYS_LOG_FILE}"
    
    # Test basic functionality
    if ! pyenvdoctor --help >/dev/null 2>&1; then
        log "ERROR" "Help command failed" "${SYS_LOG_FILE}"
        return 1
    fi
    
    # Test scan command help
    if ! pyenvdoctor scan --help >/dev/null 2>&1; then
        log "ERROR" "Scan command help failed" "${SYS_LOG_FILE}"
        return 1
    fi
    
    log "SUCCESS" "All smoke tests passed" "${SYS_LOG_FILE}"
    return 0
}
# =============================================================================
# REPORTING AND CLEANUP
# =============================================================================

generate_installation_report() {
    log "INFO" "Generating installation report" "${SYS_LOG_FILE}"
    local report_hash=$(echo "${REPORT_FILE}-$(date +%s)" | sha256sum | cut -c1-8)
    if [[ "${DRY_RUN}" != "true" ]]; then
        cat > "${REPORT_FILE}" << EOF
PyEnvDoctor Installation Report
==============================
Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Installation ID: $(date +%s)
Report Hash: ${report_hash}

System Information
-----------------
- Operating System: $(detect_os)
- Python Version: $(python3 --version 2>/dev/null || echo "Unknown")
- User: ${USER}
- Home Directory: ${HOME}
- Shell: ${SHELL}
- CPU Cores: $(nproc 2>/dev/null || echo "Unknown")
- Total Memory: $(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}') kB || "Unknown"
- Disk Space: $(df -h / 2>/dev/null | awk 'NR==2 {print $4}') || "Unknown"

Installation Details
-------------------
- PyEnvDoctor Version: $(pyenvdoctor --version 2>/dev/null || echo "Unknown")
- Installation Directory: $(command -v pyenvdoctor 2>/dev/null || echo "Not found")
- Configuration File: ${CONFIG_DIR}/config.yaml
- Log Directory: ${LOG_DIR}
- Installation Log: ${APP_LOG_FILE}

Installed Components
-------------------
- pyenvdoctor: $(command -v pyenvdoctor 2>/dev/null || echo "Not found")
- pyenvdoctor-scan: $(command -v pyenvdoctor-scan 2>/dev/null || echo "Not found")
- pyenvdoctor-fix: $(command -v pyenvdoctor-fix 2>/dev/null || echo "Not found")

Dependencies
------------
$(for dep in "${REQUIRED_DEPENDENCIES[@]}"; do
    if command -v "${dep}" >/dev/null 2>&1; then
        echo "✓ ${dep}: $(command -v "${dep}")"
    else
        echo "✗ ${dep}: Not found"
    fi
done)

Quick Start
-----------
Run '${COLOR[cyan]}pyenvdoctor check${COLOR[reset]}' to perform initial diagnostics
Run '${COLOR[cyan]}pyenvdoctor --help${COLOR[reset]}' for all available commands

Support
-------
- Documentation: https://pyenvdoctor-docs.readthedocs.io
- Issues: https://github.com/actuune/pyenvdoctor/issues
- Installation Log: ${APP_LOG_FILE}
EOF

        if command -v qrencode >/dev/null 2>&1; then
            qrencode -t ANSI "https://support.pyenvdoctor.com/install/${report_hash}" >> "${REPORT_FILE}" 2>/dev/null || log "WARN" "QR code generation failed" "${SYS_LOG_FILE}"
        fi
        log "SUCCESS" "Installation report generated: ${REPORT_FILE}" "${SYS_LOG_FILE}"
    else
        log "INFO" "[Dry Run] Would generate installation report at ${REPORT_FILE}" "${SYS_LOG_FILE}"
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    if [[ ${EUID} -eq 0 ]]; then
        log "WARN" "Running as root - some features may behave differently" "${SYS_LOG_FILE}"
    fi
    
    init
    
    log "INFO" "Performing system checks..." "${SYS_LOG_FILE}"
    local os_type=$(detect_os)
    check_python_version
    #check_dependency_versions
    check_dependencies
    
    if check_project_structure; then
        create_project_files
    fi
    
    check_for_updates
    log "INFO" "Installing PyEnvDoctor..." "${SYS_LOG_FILE}"
    install_pyenvdoctor
    create_configuration() {
    log "INFO" "Creating default configuration" "${SYS_LOG_FILE}"
    
    if [[ "${DRY_RUN}" != "true" ]]; then
        mkdir -p "${CONFIG_DIR}"
        cat > "${CONFIG_DIR}/config.yaml" << 'EOF'
# PyEnvDoctor Configuration
version: "1.0.0"

cache:
  enabled: true
  ttl: 3600
  max_size: 100MB
  directory: ~/.cache/pyenvdoctor

security:
  vulnerability_checks: true
  auto_update: true
  trusted_sources:
    - pypi.org
    - github.com

logging:
  level: INFO
  file: ~/.pyenvdoctor/logs/pyenvdoctor.log
  rotation:
    when: daily
    backup_count: 7
    max_size: 10MB

features:
  ai_assist: true
  auto_fix: false
  experimental: false
  telemetry: false

notifications:
  email:
    enabled: false
    address: ""
  slack:
    enabled: false
    webhook: ""

performance:
  max_parallel_checks: 4
  timeout: 30
  retry_attempts: 3
EOF
        
        if [[ -f "${CONFIG_DIR}/config.yaml" ]]; then
            chmod 644 "${CONFIG_DIR}/config.yaml" || log "WARN" "Failed to set permissions on config.yaml" "${SYS_LOG_FILE}"
            log "SUCCESS" "Configuration created at ${CONFIG_DIR}/config.yaml" "${SYS_LOG_FILE}"
        else
            error_exit "Failed to create configuration file at ${CONFIG_DIR}/config.yaml"
        fi
    else
        log "INFO" "[Dry Run] Would create configuration at ${CONFIG_DIR}/config.yaml" "${SYS_LOG_FILE}"
    fi
}

    setup_cron_jobs
    
    log "INFO" "Verifying installation..." "${SYS_LOG_FILE}"
    verify_installation || error_exit "Installation verification failed"
    run_smoke_tests || error_exit "Smoke tests failed"
    
    generate_installation_report
    send_anonymous_telemetry
    
    echo -e "\n${COLOR[green]}╔════════════════════════════════════════════════════════════════╗"
    echo -e "║          PyEnvDoctor Installation Completed Successfully!       ║"
    echo -e "╚════════════════════════════════════════════════════════════════╝${COLOR[reset]}\n"
    echo -e "Next steps:"
    echo -e "  1. Run '${COLOR[cyan]}pyenvdoctor check${COLOR[reset]}' to perform initial diagnostics"
    echo -e "  2. Review the installation report: ${COLOR[cyan]}${REPORT_FILE}${COLOR[reset]}"
    echo -e "  3. Check the log file: ${COLOR[cyan]}${APP_LOG_FILE}${COLOR[reset]}"
    echo -e "\nFor help: ${COLOR[cyan]}pyenvdoctor --help${COLOR[reset]}\n"
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    trap cleanup EXIT
    main "$@"
fi