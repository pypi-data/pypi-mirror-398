import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

import click

try:
    from .logger import logger
except ImportError:
    from logger import logger

try:
    from .gitignore_utils import get_tool_specific_exclusions
except ImportError:
    from gitignore_utils import get_tool_specific_exclusions

# Cache folder for downloaded JRE
CACHE_DIR = Path.home() / ".audit_scan"
JRE_DIR = CACHE_DIR / "jre"
JRE_DIR.mkdir(parents=True, exist_ok=True)


def find_java():
    """Check system java or JAVA_HOME"""
    logger.debug("Looking for Java installation")
    system = platform.system()

    def _is_working_java(java_binary: Path) -> bool:
        if not java_binary or not java_binary.exists():
            return False
        try:
            result = subprocess.run(
                [str(java_binary), "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Failed to execute Java binary {java_binary}: {exc}")
            return False

        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0 or "Unable to locate a Java Runtime" in output:
            logger.debug(
                f"Java binary at {java_binary} is not usable "
                f"(returncode={result.returncode})."
            )
            if output:
                logger.debug(output.strip())
            return False
        return True

    def _validate_java_home(java_home_dir: Path) -> str | None:
        java_bin_name = "java.exe" if os.name == "nt" else "java"
        java_candidate = java_home_dir / "bin" / java_bin_name
        if _is_working_java(java_candidate):
            logger.debug(f"Found Java in JAVA_HOME: {java_candidate}")
            return str(java_candidate)
        return None

    java_path = shutil.which("java")
    if java_path and _is_working_java(Path(java_path)):
        logger.debug(f"Found Java on PATH: {java_path}")
        return java_path
    if java_path and system == "Darwin":
        logger.debug(f"Ignoring non-functional macOS stub at {java_path}")

    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        validated = _validate_java_home(Path(java_home))
        if validated:
            return validated

    if system == "Darwin":
        java_home_tool = Path("/usr/libexec/java_home")
        if java_home_tool.exists():
            try:
                result = subprocess.run(
                    [str(java_home_tool)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                java_home_path = result.stdout.strip()
                if result.returncode == 0 and java_home_path:
                    validated = _validate_java_home(Path(java_home_path))
                    if validated:
                        return validated
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    f"Failed to resolve JAVA_HOME via /usr/libexec/java_home: {exc}"
                )

        brew_prefixes = [Path("/opt/homebrew"), Path("/usr/local")]
        brew_formula_globs = ("openjdk*", "temurin*")
        for prefix in brew_prefixes:
            opt_dir = prefix / "opt"
            if not opt_dir.exists():
                continue
            for pattern in brew_formula_globs:
                for candidate_dir in sorted(
                    opt_dir.glob(pattern), key=lambda p: p.name, reverse=True
                ):
                    java_bins = [
                        candidate_dir / "bin" / "java",
                        candidate_dir
                        / "libexec"
                        / "openjdk.jdk"
                        / "Contents"
                        / "Home"
                        / "bin"
                        / "java",
                    ]
                    for java_candidate in java_bins:
                        if _is_working_java(java_candidate):
                            logger.debug(
                                f"Found Java via Homebrew at: {java_candidate}"
                            )
                            return str(java_candidate)

        jvm_dir = Path("/Library/Java/JavaVirtualMachines")
        if jvm_dir.exists():
            for jdk_dir in sorted(
                jvm_dir.iterdir(), key=lambda p: p.name, reverse=True
            ):
                java_candidate = (
                    jdk_dir
                    / "Contents"
                    / "Home"
                    / "bin"
                    / ("java.exe" if os.name == "nt" else "java")
                )
                if _is_working_java(java_candidate):
                    logger.debug(f"Found Java in JVM directory: {java_candidate}")
                    return str(java_candidate)

    if platform.system() == "Darwin":
        try:
            ensure_openjdk17()
            # After installation, try finding Java again
            java_path = shutil.which("java")
            if java_path and _is_working_java(Path(java_path)):
                logger.debug(f"Found Java after installation: {java_path}")
                return java_path
        except Exception as e:
            logger.warning(f"Failed to install OpenJDK 17: {e}")

    logger.warning("Java not found in PATH or JAVA_HOME")
    return None


def ensure_openjdk17():
    """Ensure OpenJDK 17 is installed, symlinked, and environment variables set on macOS."""
    logger.info("Checking for OpenJDK 17 installation...")

    brew_path = shutil.which("brew")
    if not brew_path:
        raise RuntimeError(
            "Homebrew not found. Please install Homebrew first from https://brew.sh/"
        )

    try:
        # Check if java is already available
        subprocess.run(
            ["java", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info("✅ Java is already available.")
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.info("Java not found or misconfigured. Installing OpenJDK 17...")

    # Install openjdk@17 using Homebrew
    try:
        click.echo("Installing OpenJDK 17... might ask for sudo privileges...")
        subprocess.run(["brew", "install", "--quiet", "openjdk@17"], check=True)
        logger.info("✅ Installed openjdk@17 via Homebrew.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to install openjdk@17: {e}")

    # Create system symlink (macOS specific)
    if platform.system() == "Darwin":
        jdk_symlink = Path("/Library/Java/JavaVirtualMachines/openjdk-17.jdk")
        jdk_target = Path("/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk")

        try:
            subprocess.run(
                ["sudo", "ln", "-sfn", str(jdk_target), str(jdk_symlink)], check=True
            )
            logger.info(f"🔗 Symlinked {jdk_target} → {jdk_symlink}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(
                f"⚠️  Could not create symlink: {e}\n"
                "Please run manually with admin privileges:\n"
                f"sudo ln -sfn {jdk_target} {jdk_symlink}"
            )

    # Update environment variables
    if platform.system() == "Darwin":
        java_home = "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
        java_bin = "/opt/homebrew/opt/openjdk@17/bin"
    else:
        java_home = "/usr/lib/jvm/java-17-openjdk"
        java_bin = f"{java_home}/bin"

    path_line = f'export PATH="{java_bin}:$PATH"'
    java_home_line = f'export JAVA_HOME="{java_home}"'

    # Update shell config
    shell_configs = [
        Path.home() / ".zshrc",
        Path.home() / ".bash_profile",
        Path.home() / ".bashrc",
    ]

    # If none of the config files exist, create .zshrc
    if not any(config.exists() for config in shell_configs):
        zshrc = Path.home() / ".zshrc"
        zshrc.touch()  # Create empty .zshrc if it doesn't exist
        logger.info(f"ℹ️  Created {zshrc} as no shell config files were found.")

    config_updated = False
    for config in shell_configs:
        try:
            if not config.exists():
                continue

            content = config.read_text()
            lines = content.splitlines()
            new_lines = []

            if path_line not in content:
                new_lines.append(path_line)
            if java_home_line not in content:
                new_lines.append(java_home_line)

            if new_lines:
                with config.open("a") as f:
                    for line in new_lines:
                        f.write(f"\n{line}")
                logger.info(f"🔧 Updated {config} with JAVA_HOME and PATH settings.")
                config_updated = True

        except (IOError, OSError) as e:
            logger.warning(f"⚠️  Could not update {config}: {e}")

    # Source the configuration if it was updated
    if config_updated:
        try:
            # Try to source the most common shell config file that exists
            for config in shell_configs:
                if config.exists():
                    subprocess.run(
                        ["sh", "-c", f"source {config} 2>/dev/null || true"],
                        check=False,
                    )
                    logger.info(
                        f"🔄 Sourced {config} to update current shell environment"
                    )
                    break
        except Exception as e:
            logger.warning(f"⚠️  Could not source shell config: {e}")
            logger.info(
                "   Please restart your shell or run 'source ~/.zshrc' (or your shell's config file) for changes to take effect."
            )

    # Set environment for current process
    os.environ["JAVA_HOME"] = java_home
    os.environ["PATH"] = f"{java_bin}:{os.environ.get('PATH', '')}"

    # Verify Java is available in current session
    try:
        subprocess.run(
            ["java", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info("✅ OpenJDK 17 installation and setup completed successfully!")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning(
            "⚠️  Java installation may not be immediately available in the current shell.\n"
            "   Please restart your shell or run: source ~/.zshrc (or your shell's config file)"
        )


def download_jre():
    """Download minimal JRE into cache folder"""
    system = platform.system().lower()
    dest = None

    # Get the machine architecture (e.g., 'x86_64', 'arm64')
    arch = platform.machine()
    os = (
        "macos"
        if system == "darwin"
        else ("windows" if system == "windows" else "linux")
    )
    ext = "zip" if system != "linux" else "tar.gz"
    zulu_url = f"https://api.azul.com/zulu/download/community/v1.0/bundles/latest?os={os}&arch={arch}&ext={ext}&bundle_type=jre&java_version=17"
    try:
        with urllib.request.urlopen(zulu_url) as r:
            data = json.load(r)
            url = data["url"]
    except Exception as exc:
        error_msg = f"Failed to fetch JRE metadata: {exc}"
        logger.exception(error_msg)
        raise RuntimeError(error_msg) from exc

    if "windows" in system:
        dest = CACHE_DIR / "jre.zip"
    elif "darwin" in system:
        dest = CACHE_DIR / "jre.zip"
    else:  # linux
        dest = CACHE_DIR / "jre.tar.gz"

    try:
        print(f"🌐 Downloading JRE from {url} ...")
        urllib.request.urlretrieve(url, dest)
    except Exception as exc:
        error_msg = f"Failed to download JRE archive: {exc}"
        logger.exception(error_msg)
        raise RuntimeError(error_msg) from exc

    try:
        # Extract
        if dest.suffix == ".zip":
            with zipfile.ZipFile(dest, "r") as zip_ref:
                zip_ref.extractall(JRE_DIR)
        else:
            with tarfile.open(dest, "r:gz") as tar_ref:
                tar_ref.extractall(JRE_DIR)
    except Exception as exc:
        error_msg = f"Failed to extract JRE archive: {exc}"
        logger.exception(error_msg)
        raise RuntimeError(error_msg) from exc
    finally:
        if dest.exists():
            try:
                dest.unlink()
            except Exception as unlink_exc:
                logger.warning(
                    f"Could not remove temporary JRE archive {dest}: {unlink_exc}"
                )

    # Ensure the extracted java binaries are executable (particularly for zip archives)
    try:
        for jre_root in sorted([d for d in JRE_DIR.iterdir() if d.is_dir()]):
            bin_dir = jre_root / "bin"
            if bin_dir.exists():
                for binary in bin_dir.iterdir():
                    if binary.is_file():
                        current_mode = binary.stat().st_mode
                        binary.chmod(
                            current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                        )
    except Exception as exc:
        error_msg = f"Failed to set executable permissions on JRE binaries: {exc}"
        logger.exception(error_msg)
        raise RuntimeError(error_msg) from exc

    print(f"✅ JRE installed to {JRE_DIR}")


def get_jre_bin():
    """Return path to java binary"""
    java_bin = find_java()
    if java_bin:
        return java_bin

    # Download and find inside extracted folder
    java_filename = "java.exe" if os.name == "nt" else "java"
    subdirs = [
        d
        for d in JRE_DIR.iterdir()
        if d.is_dir() and (d / "bin" / java_filename).exists()
    ]
    if not subdirs:
        download_jre()
        subdirs = [
            d
            for d in JRE_DIR.iterdir()
            if d.is_dir() and (d / "bin" / java_filename).exists()
        ]
    if not subdirs:
        raise RuntimeError("JRE download failed or empty.")
    java_bin = subdirs[0] / "bin" / java_filename
    if not java_bin.exists():
        raise RuntimeError(f"Java binary not found in {java_bin}")
    return str(java_bin)


def get_java_home(java_bin: str) -> str:
    """Get JAVA_HOME from Java binary path, handling symlinks and redirects on all platforms."""
    # First, check if JAVA_HOME is already set
    java_home_env = os.environ.get("JAVA_HOME")
    if java_home_env:
        java_home_path = Path(java_home_env)
        java_exe = java_home_path / "bin" / ("java.exe" if os.name == "nt" else "java")
        if java_exe.exists():
            logger.debug(f"Using JAVA_HOME from environment: {java_home_env}")
            return java_home_env

    java_bin_path = Path(java_bin)

    # Resolve symlinks/redirects on all platforms
    try:
        # Use resolve() which handles symlinks on Unix and Windows
        real_java_bin = java_bin_path.resolve()
        if real_java_bin != java_bin_path:
            logger.debug(f"Resolved Java path: {java_bin_path} -> {real_java_bin}")
            java_bin_path = real_java_bin
    except (OSError, ValueError) as e:
        logger.debug(f"Could not resolve real path: {e}")

    # Try to query Java for its home directory (works on all platforms)
    try:
        result = subprocess.run(
            [str(java_bin_path), "-XshowSettings:properties", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            timeout=10,
        )
        # Parse java.home from output (stderr is redirected to stdout)
        output = result.stdout or ""
        for line in output.splitlines():
            if "java.home" in line.lower():
                # Format: "    java.home = /path/to/java/home" or "java.home = C:\path\to\java\home"
                parts = line.split("=", 1)
                if len(parts) == 2:
                    java_home = parts[1].strip()
                    java_home_path = Path(java_home)
                    if java_home_path.exists():
                        logger.debug(
                            f"Found JAVA_HOME from Java properties: {java_home}"
                        )
                        return str(java_home_path)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception) as e:
        logger.debug(f"Could not query Java for home directory: {e}")

    # Platform-specific common installation locations
    if os.name == "nt":
        # Windows common paths
        common_paths = [
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Java",
            Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"))
            / "Java",
        ]
        java_exe_name = "java.exe"
    else:
        # Unix-like systems (Linux, macOS)
        common_paths = [
            Path("/usr/lib/jvm"),
            Path("/usr/java"),
            Path("/Library/Java/JavaVirtualMachines"),  # macOS
            Path("/opt/java"),
            Path.home() / ".sdkman" / "candidates" / "java",  # SDKMAN
        ]
        java_exe_name = "java"

    for java_dir in common_paths:
        if java_dir.exists():
            # Look for JDK/JRE directories
            for jdk_dir in sorted(
                java_dir.iterdir(), key=lambda p: p.name, reverse=True
            ):
                if jdk_dir.is_dir():
                    # Check various possible bin locations
                    possible_bins = [
                        jdk_dir / "bin" / java_exe_name,
                        jdk_dir / "Contents" / "Home" / "bin" / java_exe_name,  # macOS
                        jdk_dir / "jre" / "bin" / java_exe_name,
                    ]
                    for java_exe in possible_bins:
                        if java_exe.exists():
                            try:
                                if java_exe.resolve() == java_bin_path.resolve():
                                    # For macOS, return Contents/Home if it exists
                                    if (jdk_dir / "Contents" / "Home").exists():
                                        java_home = jdk_dir / "Contents" / "Home"
                                    else:
                                        java_home = jdk_dir
                                    logger.debug(
                                        f"Found JAVA_HOME in common location: {java_home}"
                                    )
                                    return str(java_home)
                            except (OSError, ValueError):
                                continue

    # Fallback: assume standard structure (bin/java -> JAVA_HOME/bin/java)
    java_home = java_bin_path.parent.parent
    logger.debug(f"Using fallback JAVA_HOME: {java_home}")
    return str(java_home)


def get_scanner_path():
    """Return path to sonar-scanner bundled folder"""
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent

    # Assume a 'sonar-scanner' folder is next to CLI
    scanner_bin = (
        base_path
        / "sonar-scanner"
        / "bin"
        / ("sonar-scanner.bat" if os.name == "nt" else "sonar-scanner")
    )
    if not scanner_bin.exists():
        raise FileNotFoundError(f"SonarScanner binary not found: {scanner_bin}")
    return scanner_bin


def detect_project_type(project_dir: Path) -> Optional[str]:
    """Detect project type based on build files."""
    project_dir = Path(project_dir)
    if (project_dir / "pom.xml").exists():
        return "maven"
    elif any((project_dir / f).exists() for f in ["build.gradle", "build.gradle.kts"]):
        return "gradle"
    elif any(project_dir.glob("*.sln")) or any(project_dir.glob("*.csproj")):
        return "dotnet"
    elif any(
        f.suffix == ".java"
        for f in project_dir.rglob("*.java")
        if not any(
            p.startswith(".") or p.startswith("target") or p.startswith("build")
            for p in f.parts
        )
    ):
        return "java"  # Plain Java project
    return None


def discover_sln_files(root_dir: Path, max_depth: int = 3) -> List[Path]:
    """Discover .sln files with exclusions and depth limit."""
    sln_files = []
    root_dir = Path(root_dir)

    # Common directories to exclude
    exclude_dirs = {
        ".git",
        "bin",
        "obj",
        "node_modules",
        "dist",
        "build",
        "target",
        ".vs",
        ".vscode",
        ".idea",
        "venv",
        ".venv",
    }

    def _walk(current_dir: Path, depth: int):
        if depth > max_depth:
            return

        try:
            # Check for .sln files in current directory
            for f in current_dir.glob("*.sln"):
                if f.is_file():
                    sln_files.append(f)

            # Recurse into subdirectories
            for d in current_dir.iterdir():
                if d.is_dir() and d.name not in exclude_dirs and not d.name.startswith("."):
                    _walk(d, depth + 1)
        except PermissionError:
            logger.warning(f"Permission denied: {current_dir}")
        except Exception as e:
            logger.error(f"Error walking {current_dir}: {e}")

    _walk(root_dir, 0)
    # Sort for stable ordering and return as relative paths
    return sorted(sln_files)


def find_maven_command() -> Optional[str]:
    """Find Maven command, handling Windows-specific cases."""
    # On Windows, try mvn.cmd first, then mvn
    if os.name == "nt":
        mvn_cmd = shutil.which("mvn.cmd")
        if mvn_cmd:
            return "mvn.cmd"
        mvn = shutil.which("mvn")
        if mvn:
            return "mvn"
    else:
        mvn = shutil.which("mvn")
        if mvn:
            return "mvn"
    return None


def normalize_sonar_path(path: str | Path) -> str:
    """Normalize a path for SonarQube properties files.

    SonarQube properties files expect forward slashes as path separators
    on all platforms (Windows, Linux, macOS), regardless of the OS convention.

    Args:
        path: Path as string or Path object

    Returns:
        Path string with forward slashes
    """
    path_str = str(path)
    # Convert to forward slashes (works on all platforms)
    return path_str.replace("\\", "/")


def get_java_build_command(
    project_type: str, project_dir: Path
) -> Tuple[List[str], str]:
    """Return the appropriate build command and compiled classes path."""
    if project_type == "maven":
        mvn_cmd = find_maven_command()
        if not mvn_cmd:
            mvn_cmd = "mvn"  # Fallback
        return [mvn_cmd, "clean", "compile"], "target/classes"
    elif project_type == "gradle":
        # Use gradlew if available, otherwise try global gradle
        gradle_script = "gradlew.bat" if os.name == "nt" else "./gradlew"
        if (project_dir / gradle_script.lstrip("./")).exists():
            return [gradle_script, "compileJava"], "build/classes"
        return ["gradle", "compileJava"], "build/classes"
    else:  # Plain Java project
        # Create bin directory if it doesn't exist
        bin_dir = project_dir / "bin"
        bin_dir.mkdir(exist_ok=True)
        return ["javac", "-d", "bin"] + [
            str(p) for p in project_dir.rglob("*.java")
        ], "bin"


def get_key_from_props(props_file: Path) -> Optional[str]:
    """Extract sonar.projectKey from properties file if it exists."""
    if not props_file.exists():
        return None
    try:
        content = props_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("sonar.projectKey="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def run_sonarqube_scan(sonar_url, token, project_key, sources):
    project_root = Path(sources).resolve()
    if not project_root.exists():
        click.echo("❌ Source directory not found.")
        sys.exit(1)

    props_file = project_root / "sonar-project.properties"

    # Priority 1: Use from sonar-project.properties if it exists
    if props_file.exists():
        key_from_file = get_key_from_props(props_file)
        if key_from_file:
            project_key = key_from_file
            logger.debug(f"Using project key from {props_file}: {project_key}")
        else:
            # File exists but key is missing, we might still need a key for the CLI arg or result URL
            project_key = project_key or project_root.name

    # Priority 2: If no key yet (file missing or key missing in file), use CLI arg or prompt
    if not project_key:
        project_key = click.prompt(
            f"❓ sonar-project.properties not found. Enter project key",
            default=project_root.name,
            show_default=True,
        )

    click.echo(f"🔍 Starting SonarQube scan for project: {project_key}")

    # Get gitignore patterns for SonarQube
    sonar_patterns = []
    try:
        sonar_patterns = get_tool_specific_exclusions(str(project_root), "sonarqube")
        if sonar_patterns:
            logger.debug(
                f"Using {len(sonar_patterns)} .gitignore patterns for SonarQube exclusions"
            )
    except Exception as e:
        logger.warning(f"Could not process .gitignore files: {e}")

    # Add default exclusions
    default_exclusions = [
        "**/*.sarif",
        "**/*.log",
        "**/node_modules/**",
        "**/bower_components/**",
        "**/*.min.*",
        "**/dist/**",
        "**/build/**",
        "**/target/**",
        "**/*.iml",
        "**/.idea/**",
        "**/.vscode/**",
        "**/venv/**",
        "**/.venv/**",
        "**/env/**",
        "**/.env*",
        "**/*.bak",
        "**/*.tmp",
        "**/tmp/**",
        "**/*~",
        "**/.git/**",
        "**/.github/**",
        "**/.gitlab-ci.yml",
        "**/sonar-project.properties",
    ]

    # Combine all exclusions
    all_exclusions = list(set(default_exclusions + sonar_patterns))
    exclusions_str = ",".join(all_exclusions)

    # Detect project type and handle Java projects
    project_type = detect_project_type(project_root)
    java_binaries = None
    properties = ""

    if project_type in ("maven", "gradle", "java"):
        click.echo(f"🔍 Detected {project_type.upper()} project")

        try:
            # Get build command with project directory
            build_cmd, java_binaries = get_java_build_command(
                project_type, project_root
            )

            # Check for build tools
            if project_type == "maven":
                mvn_cmd = find_maven_command()
                if not mvn_cmd:
                    raise FileNotFoundError("Maven (mvn or mvn.cmd) not found in PATH")
            elif (
                project_type == "gradle"
                and not (project_root / "gradlew").exists()
                and not shutil.which("gradle")
            ):
                raise FileNotFoundError("Gradle (gradle or gradlew) not found")

            # Compile the project
            click.echo(f"🛠️  Compiling {project_type.upper()} project...")
            # On Windows, we need shell=True for .bat files and Maven commands
            use_shell = os.name == "nt" and (
                any(cmd.endswith(".bat") for cmd in build_cmd)
                or project_type == "maven"
            )
            try:
                result = subprocess.run(
                    build_cmd,
                    cwd=str(
                        project_root
                    ),  # Convert to string for older Python versions
                    check=True,
                    capture_output=True,
                    text=True,
                    shell=use_shell,
                )
                if result.stderr:
                    click.echo(f"ℹ️  Compiler warnings: {result.stderr}")
            except subprocess.CalledProcessError as e:
                click.echo(f"❌ Compilation failed with error: {e.stderr}")
                raise
            click.echo("✅ Project compiled successfully")

            # For Maven projects, copy dependencies for SonarQube analysis
            if project_type == "maven":
                try:
                    click.echo("📦 Copying Maven dependencies...")
                    mvn_cmd = find_maven_command() or "mvn"
                    dep_result = subprocess.run(
                        [
                            mvn_cmd,
                            "dependency:copy-dependencies",
                            "-DoutputDirectory=target/dependency",
                        ],
                        cwd=str(project_root),
                        check=True,
                        capture_output=True,
                        text=True,
                        shell=use_shell,
                    )
                    if dep_result.stderr and "ERROR" in dep_result.stderr:
                        click.echo(f"ℹ️  Dependency copy warnings: {dep_result.stderr}")
                    click.echo("✅ Dependencies copied successfully")
                except subprocess.CalledProcessError as e:
                    click.echo(f"⚠️  Could not copy dependencies: {e.stderr}")
                    logger.warning(f"Failed to copy Maven dependencies: {e}")

            # Set up properties for Java projects
            # Normalize sources path for SonarQube (uses forward slashes on all platforms)
            sources_normalized = normalize_sonar_path(sources)
            properties = f"""
sonar.projectKey={project_key}
sonar.projectName={project_key}
sonar.sources={sources_normalized}
sonar.exclusions={exclusions_str}
sonar.sourceEncoding=UTF-8
""".strip()

            # Add Java-specific properties if compilation was successful
            java_binaries_path = project_root / java_binaries
            if java_binaries_path.exists():
                # Normalize path for SonarQube (uses forward slashes on all platforms)
                java_binaries_normalized = normalize_sonar_path(java_binaries)
                properties += f"\nsonar.java.binaries={java_binaries_normalized}"
                if project_type in ("maven", "gradle"):
                    # For Maven: use dependency directory, fallback to target/*.jar if dependencies weren't copied
                    if project_type == "maven":
                        dep_dir = project_root / "target" / "dependency"
                        target_jar_dir = project_root / "target"
                        # Check if dependency directory has JARs
                        if dep_dir.exists() and any(dep_dir.glob("*.jar")):
                            lib_path = "target/dependency/*.jar"
                            # Also include any packaged JARs in target/ if they exist
                            if any(target_jar_dir.glob("*.jar")):
                                lib_path += ",target/*.jar"
                            properties += f"\nsonar.java.libraries={lib_path}"
                        # Fallback: check if any JARs exist in target/ (from packaging)
                        elif any(target_jar_dir.glob("*.jar")):
                            properties += f"\nsonar.java.libraries=target/*.jar"
                        # If no JARs found, don't set the property (SonarQube will try to auto-detect)
                    else:  # Gradle
                        lib_dir = project_root / "build" / "libs"
                        if lib_dir.exists() and any(lib_dir.glob("*.jar")):
                            properties += f"\nsonar.java.libraries=build/libs/*.jar"

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            click.echo(f"⚠️  Could not compile project: {str(e)}")
            if project_type == "maven":
                click.echo(
                    "⚠️  Please install Maven (mvn) or compile the project manually"
                )
            elif project_type == "gradle":
                click.echo(
                    "⚠️  Please install Gradle or use the Gradle wrapper (gradlew)"
                )
            else:
                click.echo("⚠️  Please compile the Java files manually")

            if not click.confirm(
                "Continue with limited analysis (Java files will be excluded)?",
                default=True,
            ):
                return False

            # Fall back to excluding Java files
            sources_normalized = normalize_sonar_path(sources)
            properties = f"""
sonar.projectKey={project_key}
sonar.projectName={project_key}
sonar.sources={sources_normalized}
sonar.exclusions=**/*.java,**/*.sarif,**/*.log
sonar.sourceEncoding=UTF-8
""".strip()
    else:
        # For non-Java projects, use basic configuration
        sources_normalized = normalize_sonar_path(sources)
        properties = f"""
sonar.projectKey={project_key}
sonar.projectName={project_key}
sonar.sources={sources_normalized}
sonar.exclusions=**/*.sarif,**/*.log
sonar.sourceEncoding=UTF-8
""".strip()

    # Get scanner and Java paths
    scanner_bin = get_scanner_path()
    java_bin = get_jre_bin()
    java_bin_path = Path(java_bin)
    java_home = get_java_home(java_bin)

    # Validate JAVA_HOME
    java_home_path = Path(java_home)
    java_exe_in_home = (
        java_home_path / "bin" / ("java.exe" if os.name == "nt" else "java")
    )
    if not java_exe_in_home.exists():
        # If JAVA_HOME doesn't have java.exe, try to use the java_bin's parent directory structure
        logger.warning(
            f"JAVA_HOME {java_home} does not contain java.exe. "
            f"Trying alternative detection..."
        )
        # Try parent.parent as fallback
        fallback_home = java_bin_path.parent.parent
        fallback_exe = (
            fallback_home / "bin" / ("java.exe" if os.name == "nt" else "java")
        )
        if fallback_exe.exists():
            java_home = str(fallback_home)
            logger.debug(f"Using fallback JAVA_HOME: {java_home}")
        else:
            # Last resort: just use the directory containing java.exe
            java_home = str(java_bin_path.parent)
            logger.warning(
                f"Could not find valid JAVA_HOME. Using java.exe directory: {java_home}"
            )

    env = os.environ.copy()
    env["JAVA_HOME"] = java_home

    # Handle PATH updates in a cross-platform way
    path_sep = ";" if os.name == "nt" else ":"
    path_parts = [str(java_bin_path.parent), env.get("PATH", "")]
    env["PATH"] = path_sep.join(filter(None, path_parts))

    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "PYTHONIOENCODING": "utf-8",
            "LANG": "C.UTF-8" if platform.system() != "Darwin" else "en_US.UTF-8",
            "LC_ALL": "C.UTF-8" if platform.system() != "Darwin" else "en_US.UTF-8",
        }
    )

    # # Ensure URL and token are properly formatted
    # sonar_url = sonar_url or SONAR_HOST_URL
    # token = token or SONAR_LOGIN

    # if not sonar_url or sonar_url == SONAR_HOST_URL:
    #     click.echo(f"⚠️  Using default SonarQube URL: {SONAR_HOST_URL}")
    if not token:
        error_msg = "No SonarQube token provided. Please set SONAR_LOGIN in your .env file or use --token"
        logger.error(error_msg)
        click.echo(f"❌ {error_msg}")
        sys.exit(1)

    env["SONAR_HOST_URL"] = sonar_url.rstrip("/")
    env["SONAR_TOKEN"] = token.strip()
    logger.debug("SonarQube configuration verified")

    # Handle .NET projects specifically
    if project_type == "dotnet":
        # Ensure conflicting properties file is removed
        props_file = project_root / "sonar-project.properties"
        if props_file.exists():
            try:
                props_file.unlink()
                click.echo(
                    "🧹 Removed conflicting sonar-project.properties for .NET scan"
                )
            except Exception as e:
                click.echo(f"⚠️  Failed to remove sonar-project.properties: {e}")

        click.echo("🚀 Starting .NET SonarScanner...")
        return run_dotnet_scan(project_key, sonar_url, token, project_root, env)

    # Create sonar-project.properties if not exists
    props_file = project_root / "sonar-project.properties"
    if not props_file.exists():
        try:
            props_file.write_text(properties, encoding="utf-8")
            click.echo("📝 Created sonar-project.properties for future use")
        except Exception as e:
            click.echo(f"⚠️  Failed to create sonar-project.properties: {e}")
            return False

    # Prepare SARIF report paths
    reports_dir = project_root / "code-audit-23" / "reports"

    # Check which report files exist
    report_files = [
        "gitleaks.sarif",
        "semgrep.sarif",
        "trivy.sarif",
        "bandit.sarif",
        "eslint.sarif",
        "checkov.sarif",
    ]

    # Find existing report files
    existing_reports = [f for f in report_files if (reports_dir / f).exists()]

    # Build sonar-scanner command
    scanner_cmd = [str(scanner_bin), "-Dsonar.verbose=false"]
    # scanner_cmd = [str(scanner_bin)]

    # Add SARIF reports if any exist
    if existing_reports:
        sarif_paths = [
            normalize_sonar_path(f"code-audit-23/reports/{report}")
            for report in existing_reports
        ]
        sarif_arg = "-Dsonar.sarifReportPaths=" + ",".join(sarif_paths)
        scanner_cmd.append(sarif_arg)
        click.echo(f"📊 Including SARIF reports: {', '.join(existing_reports)}")

    click.echo("🚀 Starting SonarScanner...")
    try:
        # Start the subprocess and stream logs in real-time
        process = subprocess.Popen(
            scanner_cmd,
            cwd=project_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        click.echo("🔍 Scanning code (streaming Sonar logs)...")
        streamed_output = []
        assert process.stdout is not None
        for line in process.stdout:
            streamed_output.append(line)
            click.echo(line.rstrip())

        process.wait()

        # No cleanup of sonar-project.properties (making it persistent)

        # Check the return code
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, process.args, output="".join(streamed_output)
            )

        click.echo("✅ Sonar scan completed successfully!")
        click.echo(f"👉 View results: {sonar_url}/dashboard?id={project_key}")
        return True

    except subprocess.CalledProcessError as e:
        # No cleanup of sonar-project.properties (making it persistent)

        error_msg = f"Sonar scan failed with exit code {e.returncode}"
        logger.error(error_msg)
        click.echo("❌ Sonar scan failed!")
        click.echo(f"Exit code: {e.returncode}")
        # sys.exit(1)
        return False

    except Exception as e:
        # No cleanup of sonar-project.properties (making it persistent)

        error_msg = f"Unexpected error during Sonar scan: {str(e)}"
        logger.exception(error_msg)
        click.echo(f"❌ {error_msg}")
        # sys.exit(1)
        return False


def check_dotnet_prerequisites():
    """Check if dotnet and dotnet-sonarscanner are installed."""
    if not shutil.which("dotnet"):
        click.echo("❌ .NET SDK not found. Please install .NET SDK first.")
        return False

    try:
        # Check if dotnet-sonarscanner is installed
        result = subprocess.run(
            ["dotnet", "tool", "list", "-g"], capture_output=True, text=True, check=True
        )
        if "dotnet-sonarscanner" not in result.stdout:
            click.echo("⚠️  dotnet-sonarscanner tool not found.")
            if click.confirm(
                "Do you want to install dotnet-sonarscanner globally?", default=True
            ):
                subprocess.run(
                    ["dotnet", "tool", "install", "--global", "dotnet-sonarscanner"],
                    check=True,
                )
                click.echo("✅ dotnet-sonarscanner installed successfully.")
            else:
                return False
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check/install dotnet tools: {e}")
        return False


def run_dotnet_scan(project_key, sonar_url, token, project_root, env):
    """Run SonarQube scan for .NET projects using dotnet sonarscanner."""
    if not check_dotnet_prerequisites():
        return False

    # Ensure conflicting properties file is removed for .NET projects
    props_file = project_root / "sonar-project.properties"
    if props_file.exists():
        try:
            props_file.unlink()
            click.echo("🧹 Removed conflicting sonar-project.properties for .NET scan")
        except Exception as e:
            click.echo(f"⚠️  Failed to remove sonar-project.properties: {e}")

    # Discover .sln files
    sln_files = discover_sln_files(project_root)
    selected_sln = None

    if not sln_files:
        click.echo("⚠️  No .sln files found. Skipping SonarQube scan for .NET.")
        click.echo("ℹ️  To scan .NET projects, ensure you have a .sln file within 3 levels of the root.")
        # Cleanup even if skipped
        _cleanup_dotnet_temp_files(project_root)
        return True # Continue execution

    if len(sln_files) == 1:
        selected_sln = sln_files[0]
        relative_path = selected_sln.relative_to(project_root)
        click.echo(f"🔍 Found solution: {relative_path}")
        click.echo(f"📝 Using this solution: {relative_path}")
    else:
        click.echo("🔍 Multiple solution files detected:\n")
        for idx, sln in enumerate(sln_files, 1):
            relative_path = sln.relative_to(project_root)
            click.echo(f"[{idx}] {relative_path}")
        
        click.echo("") # New line
        choice = click.prompt(
            f"Select solution to scan (1-{len(sln_files)})",
            type=click.IntRange(1, len(sln_files))
        )
        selected_sln = sln_files[choice - 1]

    relative_sln_path = selected_sln.relative_to(project_root)

    try:
        # Step 1: Begin
        click.echo(f"\n1️⃣  Beginning .NET SonarScanner for project: {project_key}...")
        begin_cmd = [
            "dotnet",
            "sonarscanner",
            "begin",
            f"/k:{project_key}",
            f"/d:sonar.host.url={sonar_url}",
            f"/d:sonar.login={token}",
        ]
        subprocess.run(begin_cmd, cwd=project_root, env=env, check=True)

        # Step 2: Build
        click.echo(f"2️⃣  Building .NET project: {relative_sln_path}...")
        # Use --no-incremental as requested
        build_cmd = ["dotnet", "build", str(selected_sln), "--no-incremental"]
        subprocess.run(build_cmd, cwd=project_root, env=env, check=True)

        # Step 3: End
        click.echo("3️⃣  Ending .NET SonarScanner (uploading results)...")
        end_cmd = ["dotnet", "sonarscanner", "end", f"/d:sonar.login={token}"]
        subprocess.run(end_cmd, cwd=project_root, env=env, check=True)

        click.echo("✅ .NET Sonar scan completed successfully!")
        click.echo(f"👉 View results: {sonar_url}/dashboard?id={project_key}")
        return True

    except subprocess.CalledProcessError as e:
        click.echo(f"❌ .NET scan failed at step: {e.cmd}")
        return False
    finally:
        _cleanup_dotnet_temp_files(project_root)


def _cleanup_dotnet_temp_files(project_root: Path):
    """Remove .sonarqube and .scannerwork directories."""
    temp_dirs = ["code-audit-23", ".sonarqube", ".scannerwork"]
    for d_name in temp_dirs:
        d_path = project_root / d_name
        if d_path.exists() and d_path.is_dir():
            try:
                shutil.rmtree(d_path)
                logger.debug(f"Removed temporary directory: {d_path}")
            except Exception as e:
                logger.warning(f"Could not remove temporary directory {d_path}: {e}")
