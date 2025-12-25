# Code Audit 23

[![PyPI Version](https://img.shields.io/pypi/v/code-audit-23.svg)](https://pypi.org/project/code-audit-23/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Code Audit 23 is a comprehensive command-line interface (CLI) tool that unifies multiple code quality and security scanning tools into a single, easy-to-use interface. It's designed to help developers maintain high code quality and security standards across their projects.

## 📑 Table of Contents

- [✨ Features](#-features)
- [🚀 Installation](#-installation)
  - [Prerequisites](#prerequisites)
  - [Install from PyPI](#install-from-pypi)
  - [Install from Source](#install-from-source)
- [🔧 Configuration](#-configuration)
- [🛠 Usage](#-usage)
  - [Basic Usage](#basic-usage)
  - [Command Line Options](#command-line-options)
  - [Menu Options](#menu-options)
- [📊 Output](#-output)
- [🧪 Development](#-development)
  - [Project Structure](#project-structure)
  - [Dependencies](#dependencies)
  - [Building & Publishing to PyPI](#building--publishing-to-pypi)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)
- [🔧 Troubleshooting](#-troubleshooting)
  - [Windows: Microsoft Visual C++ 14.0+ Required](#windows-microsoft-visual-c-140-required)
  - [Common Issues](#common-issues)
- [📧 Contact](#-contact)


## ✨ Features

- **Unified Interface**: Single command to run multiple code quality and security scans
- **Multiple Tools Integration**:
  - **SonarQube** - Code quality and security analysis
  - **Semgrep** - Static code analysis for security issues
  - **Trivy** - Vulnerability scanning for dependencies and container images
- **Interactive Menu**: User-friendly command-line interface
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **SARIF Reports**: Standardized output format for all scan results
- **No Installation Required**: Self-contained executable available

## 🚀 Installation

### Prerequisites

- Python 3.10 to 3.13
- Java 11+ (for SonarQube Scanner)
- Microsoft Visual c++ 14 (for Windows). See the [troubleshooting](#troubleshooting) section for more details.

### Install from PyPI

```bash
pip install code-audit-23
```

### Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/BrainStation-23/CodeAudit23.git
   cd CodeAudit23
   ```

2. Create and activate a virtual environment:
   ```bash
   # Linux/macOS
   python -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

## 🔧 Configuration

1. Create a `.env` file in your project root with the following variables:
   ```env
   SONAR_HOST_URL=https://your-sonarqube-instance.com
   SONAR_LOGIN=your_sonarqube_token
   ```

2. The first time you run a scan, the tool will prompt you for SonarQube credentials if they're not in the `.env` file.

## 🛠 Usage

### Basic Usage

Run the interactive menu:
```bash
code-audit-23
```

### Command Line Options

```
Usage: code-audit-23 [OPTIONS]

  Interactive entrypoint for Audit Scanner

Options:
  --help  Show this message and exit.
```

### Menu Options

1. **Quick Scan** - Run all security scans in sequence (Trivy + Semgrep + SonarQube)
2. **Trivy Scan** - Scan for vulnerabilities in dependencies and container images
3. **Semgrep Scan** - Static code analysis for security issues
4. **SonarQube Scan** - Analyze code quality and security issues

## 📊 Output

All scan reports are saved in the `reports/` directory in SARIF format:
- `reports/trivy.sarif` - Results from Trivy scan
- `reports/semgrep.sarif` - Results from Semgrep scan
- SonarQube results are available on your SonarQube server

## 🧪 Development

### Project Structure

```
code_audit_23/
├── __init__.py
├── main.py           # Main CLI entry point
├── sonarqube_cli.py  # SonarQube scanner implementation
└── logger.py         # Logging configuration
```

### Dependencies

- `click` - Command line interface creation
- `requests` - HTTP requests
- `python-dotenv` - Environment variable management

### Building & Publishing to PyPI

1. Update the version in `pyproject.toml` (and optionally `__init__.py` if you mirror it there). Commit the change.
2. Ensure you have the packaging tooling:
   ```bash
   python -m pip install --upgrade build twine
   ```
3. Clean any previous artifacts:
   ```bash
   rm -rf dist build *.egg-info
   ```
4. Build the source distribution and wheel:
   ```bash
   python -m build
   ```
5. (Optional but recommended) Validate the archives locally:
   ```bash
   twine check dist/*
   ```
6. (Optional) Publish to TestPyPI before the main release:
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```
7. Once satisfied, publish to PyPI:
   ```bash
   python -m twine upload dist/*
   ```
8. Tag the release in git, e.g.:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](./CONTRIBUTING.md) for details on how to submit pull requests, report issues, or suggest new features.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [SonarQube](https://www.sonarqube.org/) - For the amazing code quality platform
- [Semgrep](https://semgrep.dev/) - For static code analysis
- [Trivy](https://github.com/aquasecurity/trivy) - For the vulnerability scanning

## 🔧 Troubleshooting

### Windows: Microsoft Visual C++ 14.0+ Required

When installing on Windows, you might encounter the following error:

```
error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools"
```

#### Solution:

1. **Install Microsoft C++ Build Tools**:
   - Download the latest Visual Studio Build Tools installer from: [https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Run the installer and select "Desktop development with C++" workload
   - Ensure the following components are selected:
     - MSVC v143 - VS 2022 C++ x64/x86 build tools (or latest version)
     - Windows 10/11 SDK (latest version)
     - C++ CMake tools for Windows
   - Click "Install" and wait for the installation to complete

2. **Restart your computer** to ensure all environment variables are properly set

3. **Retry the installation**:
   ```bash
   pip install code-audit-23
   ```

4. **If the issue persists**, try installing the specific version of the Microsoft C++ Build Tools:
   ```bash
   pip install --upgrade setuptools
   pip install --upgrade wheel
   pip install --upgrade pip
   ```
### Unicode Encoding Error

On windows, you can get Unicode encoding error like 

```shell
UnicodeEncodeError: 'charmap' codec can't encode character '\u202a' in position 1394761: character maps to <undefined>
Sending pseudonymous metrics since metrics are configured to AUTO, registry usage is True, and login status is False
```

#### Solution

If you want Semgrep and Python always to run **UTF-8** on that system:
* Open **Windows Settings → Time & Language → Language & Region**
* Turn on **“Beta: Use Unicode UTF-8 for worldwide language support”**
* **Reboot**

This will prevent the issue globally for all Python tools (not just yours).

For Example
![Unicode off](./images/language_off.png)
![Unicode on](./images/language_on.png)


### Common Issues

#### Python Version Compatibility
Ensure you're using Python 3.9 or higher, but not above 3.13. Check your Python version with:
```bash
python --version
```

#### Permission Issues
If you encounter permission errors, try running your command prompt as Administrator or use:
```bash
pip install --user code-audit-23
```

## 📧 Contact

For any questions or feedback, please contact [Ahmad Al-Sajid](mailto:ahmad.sajid@brainstation-23.com).