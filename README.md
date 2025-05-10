
PyEnvDoctor created by SAMY is your intelligent Python environment health diagnostic tool. Like a doctor for your Python environments, it examines, diagnoses, and provides actionable recommendations to keep your Python development environments healthy and secure.

Installation
bash# Install via pip
pip install pyenvdoctor

# Install with extra features
pip install pyenvdoctor[all]

# Install via pipx (recommended)
pipx install pyenvdoctor
Basic Usage
bash# Scan current environment
pyenvdoctor scan

# Run security analysis
pyenvdoctor security

# Generate HTML report
pyenvdoctor report --format html --output report.html

# Quick health check
pyenvdoctor check
