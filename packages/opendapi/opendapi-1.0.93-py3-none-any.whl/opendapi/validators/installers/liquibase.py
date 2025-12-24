"""Liquibase Installer module"""

import os
import platform
import shlex
import shutil
import subprocess  # nosec: B404
import tarfile
import tempfile
import zipfile
from typing import Dict, List, Optional, Tuple

LIQUIBASE_VERSION = "4.29.2"
JDK_VERSION_MAJOR = 21
JDK_FLAVOR = "amazon-corretto"
JDK_BASE_URL = "https://corretto.aws/downloads"


def get_cache_dir() -> str:
    """Get the cache directory for Liquibase and Java"""
    home_cache = os.path.join(tempfile.gettempdir(), ".cache")
    cache_dir = os.path.join(home_cache, "opendapi", f"liquibase_{LIQUIBASE_VERSION}")
    return cache_dir


def get_platform_info():
    """Get platform-specific information for downloads"""
    system = platform.system().lower()
    arch = platform.machine().lower()
    return {
        "system": system,
        "arch": arch,
        "plat_suffix": "macos" if system == "darwin" else system,
        "arch_suffix": "x64" if arch in ("x86_64", "amd64") else "aarch64",
        "ext_suffix": "zip" if system == "windows" else "tar.gz",
    }


def get_install_dirs() -> dict[str, str]:
    """Get the install directories for Liquibase and Java"""
    platform_info = get_platform_info()
    cache_dir = get_cache_dir()
    java_dir = os.path.join(cache_dir, f"jdk-{JDK_VERSION_MAJOR}")
    java_bin = (
        os.path.join(java_dir, "Contents", "Home", "bin", "java")
        if platform_info["system"] == "darwin"
        else (
            os.path.join(java_dir, "bin", "java.exe")
            if platform_info["system"] == "windows"
            else os.path.join(java_dir, "bin", "java")
        )
    )
    liquibase_dir = os.path.join(cache_dir, f"liquibase-{LIQUIBASE_VERSION}")
    liquibase_bin = os.path.join(liquibase_dir, "liquibase")

    return {
        "cache_dir": cache_dir,
        "java_dir": java_dir,
        "java_bin": java_bin,
        "liquibase_dir": liquibase_dir,
        "liquibase_bin": liquibase_bin,
    }


def get_jdk_download_url() -> str:
    """Get the download URL for the JDK"""
    platform_info = get_platform_info()
    filename = (
        f"{JDK_FLAVOR}-{JDK_VERSION_MAJOR}-{platform_info['arch_suffix']}-"
        f"{platform_info['plat_suffix']}-jdk.{platform_info['ext_suffix']}"
    )
    return f"{JDK_BASE_URL}/latest/{filename}"


def get_liquibase_download_url() -> str:
    """Get the download URL for Liquibase"""
    platform_info = get_platform_info()
    return (
        "https://github.com/liquibase/liquibase/releases/"
        f"download/v{LIQUIBASE_VERSION}/liquibase-{LIQUIBASE_VERSION}.{platform_info['ext_suffix']}"
    )


def download_and_extract(url: str, extract_dir: str) -> str:
    """Download a file and extract it to the cache directory"""
    os.makedirs(extract_dir, exist_ok=True)
    cache_path = os.path.join(extract_dir, os.path.basename(url))

    # Download if file doesn't exist
    if not os.path.exists(cache_path):
        # Atomic download
        tmp_path = cache_path + ".partial"
        curl_cmd = [
            "curl",
            "-fL",
            "--retry",
            "3",
            "--retry-delay",
            "2",
            "--connect-timeout",
            "15",
            "--speed-time",
            "30",
            "--speed-limit",
            "10240",
            "-o",
            tmp_path,
            url,
        ]
        subprocess.run(curl_cmd, check=True)  # nosec
        os.replace(tmp_path, cache_path)

    # Safe extraction helpers (avoid path traversal)
    def _safe_members_tar(tar):
        for m in tar.getmembers():
            m_path = os.path.join(extract_dir, m.name)
            if not os.path.realpath(m_path).startswith(
                os.path.realpath(extract_dir) + os.sep
            ):
                raise RuntimeError(f"Unsafe path in tar archive: {m.name}")
            yield m

    def _safe_extract_zip(zf):
        for member in zf.namelist():
            m_path = os.path.join(extract_dir, member)
            if not os.path.realpath(m_path).startswith(
                os.path.realpath(extract_dir) + os.sep
            ):
                raise RuntimeError(f"Unsafe path in zip archive: {member}")
        # nosec here because we do verify for unsafe paths
        zf.extractall(extract_dir)  # nosec

    # Extract the file
    if url.endswith(".zip"):
        with zipfile.ZipFile(cache_path, "r") as zf:
            _safe_extract_zip(zf)
    else:
        with tarfile.open(cache_path, "r:gz") as tf:
            # nosec here because we do verify for unsafe paths
            tf.extractall(extract_dir, members=_safe_members_tar(tf))  # nosec

    return cache_path


def _find_extracted_directory_in_dir(prefix: str, extract_dir: str) -> str:
    """Find the extracted directory that starts with the given prefix"""
    for item in os.listdir(extract_dir):
        item_path = os.path.join(extract_dir, item)
        if item.startswith(prefix) and os.path.isdir(item_path):
            return item_path
    return None


def ensure_java_installed() -> str:
    """Ensure Java is installed"""
    # Check if java is available globally
    global_java_bin = shutil.which("java")
    if global_java_bin:
        # check if java really works because there maybe just shims
        try:
            subprocess.run(
                [global_java_bin, "--version"], capture_output=True, check=True
            )  # nosec
        except subprocess.CalledProcessError:
            pass
        else:
            return global_java_bin

    # If cached Java exists, return it
    install_dirs = get_install_dirs()
    if os.path.exists(install_dirs["java_bin"]):
        return install_dirs["java_bin"]

    # Install OpenJDK in the cache directory
    download_and_extract(get_jdk_download_url(), install_dirs["cache_dir"])

    # Find and rename the extracted directory to a predictable name
    # extracted directory is named after the JDK flavor
    extracted_dir = _find_extracted_directory_in_dir(
        JDK_FLAVOR, install_dirs["cache_dir"]
    )

    if not extracted_dir:
        raise RuntimeError("Failed to find extracted JDK directory")

    os.rename(extracted_dir, install_dirs["java_dir"])
    # check if the Java binary exists - it should be in the bin directory
    if not os.path.exists(install_dirs["java_bin"]):
        raise RuntimeError("Failed to find Java binary in extracted JDK")

    # Set execute permissions on the Java binary
    os.chmod(install_dirs["java_bin"], 0o755)  # nosec

    return install_dirs["java_bin"]


def ensure_liquibase_installed() -> str:
    """Ensure Liquibase is installed"""
    # First check global installation
    global_path = shutil.which("liquibase")
    if global_path:
        return global_path

    # If cached Liquibase exists, return it
    install_dirs = get_install_dirs()
    if os.path.exists(install_dirs["liquibase_bin"]):
        return install_dirs["liquibase_bin"]

    # Install Liquibase in the liquibase directory
    # as it doesnt extract to a subdirectory
    download_and_extract(get_liquibase_download_url(), install_dirs["liquibase_dir"])
    # Find and rename the extracted directory to a predictable name
    # extracted directory is named after the Liquibase version
    extracted_dir = install_dirs["liquibase_dir"]

    if not os.path.exists(extracted_dir):
        raise RuntimeError("Failed to find extracted Liquibase directory")

    # check if the Liquibase binary exists - it should be in the bin directory
    if not os.path.exists(install_dirs["liquibase_bin"]):
        raise RuntimeError("Failed to find Liquibase binary in extracted Liquibase")

    # Set execute permissions on the Liquibase binary
    os.chmod(install_dirs["liquibase_bin"], 0o755)  # nosec

    return install_dirs["liquibase_bin"]


def get_update_sql_gradle_command() -> Optional[str]:
    """Get the Gradle command to run updateSQL"""
    return os.environ.get("LIQUIBASE_UPDATESQL_GRADLE_COMMAND")


def build_update_sql_command(
    changelog_file_fullpath: str,
    search_dir_fullpath: str,
    offline_url: str,
    output_file_fullpath: str,
) -> Tuple[List[str], Dict[str, str]]:
    """Build the Liquibase command to run updateSQL"""
    env = os.environ.copy()

    if search_dir_fullpath and not changelog_file_fullpath.startswith(
        search_dir_fullpath
    ):
        raise ValueError(
            f"Changelog file {changelog_file_fullpath} must be in search directory {search_dir_fullpath}"
        )
    changelog_file_relative_path = changelog_file_fullpath.replace(
        search_dir_fullpath, ""
    ).lstrip("/")

    args = {
        "--changelog-file": changelog_file_relative_path,
        "--search-path": search_dir_fullpath,
        "--output-file": output_file_fullpath,
        "--url": offline_url,
    }

    # If gradle command is set, let's use it
    if gradle_command := get_update_sql_gradle_command():
        # split in case the passed in command has multiple parts
        # we need the first arg in the command to be an executable for subprocess.run
        command = [
            *shlex.split(gradle_command),
            *[f"{key}={value}" for key, value in args.items()],
        ]
        return (command, env)

    # fallback to CLI approach
    java_bin = ensure_java_installed()
    liquibase_bin = ensure_liquibase_installed()

    # Liquibase CLI expects the changelog file to be relative to search paths
    command = [
        liquibase_bin,
        *[f"{key}={value}" for key, value in args.items()],
        "updateSQL",
    ]
    env["JAVA_HOME"] = java_bin.replace("/bin/java", "")
    env["PATH"] = os.path.dirname(java_bin) + os.pathsep + env["PATH"]
    return (command, env)


def precache_installs_for_liquibase_if_necessary() -> None:
    """Install Java and Liquibase if necessary"""
    build_update_sql_command(
        changelog_file_fullpath="",
        search_dir_fullpath="",
        offline_url="",
        output_file_fullpath="",
    )
