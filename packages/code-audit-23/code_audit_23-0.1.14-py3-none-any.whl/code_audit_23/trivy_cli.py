import os
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import click

try:
    from .logger import logger
except ImportError:
    from logger import logger

try:
    from .gitignore_utils import get_tool_specific_exclusions
except ImportError:
    from gitignore_utils import get_tool_specific_exclusions


def find_trivy():
    """
    Check system for Trivy installation.

    Returns:
        str: Path to trivy executable if found, None otherwise
    """
    logger.debug("Looking for Trivy installation")

    # Check for trivy in PATH first (works on both Windows and Unix-like systems)
    trivy_path = shutil.which("trivy")
    if trivy_path:
        logger.debug(f"Found Trivy in PATH: {trivy_path}")
        return trivy_path

    # Platform-specific checks
    if os.name == "nt":  # Windows
        # Common Windows installation paths
        windows_paths = [
            os.path.expandvars("$ProgramFiles\\Aqua Security\\Trivy\\trivy.exe"),
            os.path.expandvars("$ProgramFiles(x86)\\Aqua Security\\Trivy\\trivy.exe"),
            os.path.expandvars("$LOCALAPPDATA\\aquasec\\trivy\\trivy.exe"),
            os.path.expandvars(
                "$USERPROFILE\\scoop\\shims\\trivy.exe"
            ),  # Scoop package manager
            os.path.expandvars(
                "$USERPROFILE\\AppData\\Local\\Microsoft\\WindowsApps\\trivy.exe"
            ),
        ]

        for path in windows_paths:
            if os.path.isfile(path):
                logger.debug(f"Found Trivy at Windows location: {path}")
                return path
    else:  # Unix-like systems (Linux, macOS)
        # Common Unix installation paths
        unix_paths = [
            "/usr/local/bin/trivy",
            "/usr/bin/trivy",
            "/opt/homebrew/bin/trivy",  # Homebrew on macOS (Apple Silicon)
            "/usr/local/opt/trivy/bin/trivy",  # Homebrew on macOS
            "/snap/bin/trivy",  # Snap package
            os.path.expanduser("~/.local/bin/trivy"),  # Local user installation
            "/opt/trivy/trivy",  # Manual installation
        ]

        for path in unix_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                logger.debug(f"Found Trivy at: {path}")
                return path

    # Check for TRIVY_INSTALL_DIR environment variable as a fallback
    trivy_install_dir = os.environ.get("TRIVY_INSTALL_DIR")
    if trivy_install_dir:
        trivy_bin = Path(trivy_install_dir) / "trivy" + (
            ".exe" if os.name == "nt" else ""
        )
        if trivy_bin.exists() and (os.name == "nt" or os.access(trivy_bin, os.X_OK)):
            logger.debug(f"Found Trivy in TRIVY_INSTALL_DIR: {trivy_bin}")
            return str(trivy_bin)

    logger.warning("Trivy not found in PATH or common installation locations")
    return None


def install_trivy():
    """Install Trivy based on the current operating system.

    Returns:
        str: Path to the installed trivy binary if successful, None otherwise
    """

    system = platform.system().lower()
    machine = platform.machine().lower()

    click.echo("Installing Trivy based on the current operating system...")

    # Map platform to Trivy's release assets
    platform_map = {
        "darwin": {"x86_64": "macOS-64bit.tar.gz", "arm64": "macOS-ARM64.tar.gz"},
        "linux": {
            "x86_64": "Linux-64bit.tar.gz",
            "arm64": "Linux-ARM64.tar.gz",
            "armv6": "Linux-ARM.tar.gz",
            "armv7": "Linux-ARM.tar.gz",
        },
        "windows": {
            "amd64": "Windows-64bit.zip",
            "x86_64": "Windows-64bit.zip",
            "x86": "Windows-32bit.zip",
        },
    }

    # Get the appropriate asset name
    try:
        asset = platform_map.get(system, {}).get(machine)
        if not asset:
            logger.error(f"Unsupported platform: {system} {machine}")
            return None

        trivy_version = "0.68.2"  # You might want to make this configurable
        download_url = f"https://github.com/aquasecurity/trivy/releases/download/v{trivy_version}/trivy_{trivy_version}_{asset}"

        logger.info(f"Downloading Trivy {trivy_version} for {system} {machine}...")
        click.echo(f"Downloading Trivy {trivy_version} for {system} {machine}...")
        logger.debug(f"Download URL: {download_url}")

        # Create temp directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            download_path = temp_dir_path / f"trivy_{asset}"

            # Download the file
            try:
                urllib.request.urlretrieve(download_url, download_path)
                logger.debug(f"Downloaded to: {download_path}")
            except Exception as e:
                logger.error(f"Failed to download Trivy: {e}")
                return None

            # Extract the archive
            extract_dir = temp_dir_path / "extracted"
            extract_dir.mkdir(exist_ok=True)

            try:
                if asset.endswith(".zip"):
                    with zipfile.ZipFile(download_path, "r") as zip_ref:
                        zip_ref.extractall(extract_dir)
                else:  # .tar.gz
                    with tarfile.open(download_path, "r:gz") as tar_ref:
                        tar_ref.extractall(extract_dir)
            except Exception as e:
                logger.error(f"Failed to extract Trivy: {e}")
                return None

            # Find the trivy binary in the extracted files
            trivy_bin = None
            for ext in ("", ".exe"):
                bin_name = f"trivy{ext}"
                bin_path = extract_dir / bin_name
                if bin_path.exists():
                    trivy_bin = bin_path
                    break
                # Check in subdirectories (common in tar.gz)
                for sub_path in extract_dir.rglob(bin_name):
                    trivy_bin = sub_path
                    break

                if trivy_bin:
                    break

            if not trivy_bin or not trivy_bin.exists():
                logger.error("Could not find trivy binary in the downloaded package")
                return None

            # Make the binary executable on Unix-like systems
            if system != "windows":
                trivy_bin.chmod(trivy_bin.stat().st_mode | stat.S_IEXEC)

            # Determine installation directory
            if system == "windows":
                install_dir = Path.home() / "AppData" / "Local" / "aquasec" / "trivy"
                install_dir.mkdir(parents=True, exist_ok=True)
                install_path = install_dir / "trivy.exe"
            else:
                # Try system-wide installation first
                system_bin = Path("/usr/local/bin")
                if os.access(system_bin.parent, os.W_OK):
                    install_dir = system_bin
                    install_path = install_dir / "trivy"
                else:
                    # Fall back to user's local bin
                    install_dir = Path.home() / ".local" / "bin"
                    install_dir.mkdir(parents=True, exist_ok=True)
                    install_path = install_dir / "trivy"

            # Move the binary to the installation directory
            shutil.move(str(trivy_bin), str(install_path))

            # Add to PATH if not already there
            bin_dir = str(install_dir)
            path = os.environ.get("PATH", "")
            if bin_dir not in path.split(os.pathsep):
                logger.info(f"Adding {bin_dir} to PATH")
                os.environ["PATH"] = f"{bin_dir}{os.pathsep}{path}"
                # You might want to add this to the user's shell profile
                # but that's more involved and platform-specific

            logger.info(f"Successfully installed Trivy to {install_path}")
            click.echo(f"Successfully installed Trivy to {install_path}")
            return str(install_path)

    except Exception as e:
        logger.error(f"Error installing Trivy: {e}", exc_info=True)
        return None


def run_trivy_scan(report_path, target_path=".", install_if_missing=True, timeout=900):
    """Run a Trivy security scan on the specified directory.

    Args:
        report_path (str): Path where the SARIF report will be saved
        target_path (str, optional): Path to scan. Defaults to current directory.
        install_if_missing (bool, optional): Whether to install Trivy if not found. Defaults to True.
        timeout (int, optional): Maximum time in seconds to wait for the scan to complete. Defaults to 300s.

    Returns:
        bool: True if scan completed successfully, False otherwise
    """
    trivy_path = find_trivy()

    # If Trivy not found, try to install it if allowed
    if not trivy_path and install_if_missing:
        logger.info("Trivy not found. Attempting to install...")
        trivy_path = install_trivy()
        if not trivy_path:
            logger.error("Failed to install Trivy. Please install it manually.")
            return False
    elif not trivy_path:
        logger.error("Trivy not found and automatic installation is disabled.")
        return False

    # Ensure target path exists
    target_path = Path(target_path).absolute()
    if not target_path.exists():
        logger.error(f"Target path does not exist: {target_path}")
        return False

    # Ensure report directory exists
    report_path = Path(report_path).absolute()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Get gitignore-based exclusions
    file_patterns, dir_patterns = get_tool_specific_exclusions(target_path, "trivy")

    # Build the command
    cmd = [
        trivy_path,
        "repository",
        "--format",
        "sarif",
        "--output",
        str(report_path),
        "--exit-code",
        "0",  # Don't fail on findings
    ]

    # Add file and directory exclusions
    if file_patterns:
        cmd.extend(["--skip-files", ",".join(file_patterns)])
    if dir_patterns:
        cmd.extend(["--skip-dirs", ",".join(dir_patterns)])

    # Add the target path as the last argument
    cmd.append(str(Path(target_path).resolve()))

    try:
        click.echo("Starting Trivy scan... This may take a while...")
        result = subprocess.run(
            cmd,
            check=False,  # We'll handle the return code ourselves
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Log the output
        if result.stdout:
            logger.debug(f"Trivy output:\n{result.stdout}")
        if result.stderr:
            logger.debug(f"Trivy stderr:\n{result.stderr}")

        # Check if the scan completed successfully
        if result.returncode != 0:
            logger.error(f"Trivy scan failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr.strip()}")
            return False

        logger.info(
            f"Trivy scan completed successfully. Report saved to: {report_path}"
        )
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Trivy scan timed out after {timeout} seconds")
        return False
    except Exception as e:
        logger.error(f"Error running Trivy scan: {str(e)}", exc_info=True)
        return False
