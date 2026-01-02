"""
Legacy setup.py for restricted environments without wheel package.

This setup file:
- Builds source distributions (sdist) for restricted environments
- Generates setup.cfg from pyproject.toml during sdist build
- Removes pyproject.toml from sdist to force legacy mode
- Uses built_bins/ directory for platform binaries
- Works without wheel package installed

Binary source:
  - built_bins/ directory containing all platform binaries
  - Makefile prepares this directory before building

Usage:
    make core_universal/prepare_binaries  # Prepare binaries first
    python setup-legacy.py sdist           # Build legacy sdist

For modern wheel builds, use setup.py with `make core_universal/dist`.
"""
import os
import sys
from shutil import rmtree
from sys import platform

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.sdist import sdist as _sdist

PKG_BIN_DIR = "applitools/core_universal/bin"
PKG_BUILT_BINS_DIR = "applitools/core_universal/built_bins"

PLAT_EXECUTABLE = {
    "macosx_10_7_x86_64": "core-macos",
    "macosx_11_0_arm64": "core-macos-arm64",
    "manylinux1_x86_64": "core-linux",
    "manylinux2014_aarch64": "core-linux-arm64",
    "musllinux_1_2_x86_64": "core-alpine",
    "win_amd64": "core-win.exe",
}


def get_included_platforms():
    """Get the list of platforms to include in source distribution.

    Can be specified via:
    - INCLUDE_PLATFORMS environment variable (comma-separated)
    - --include-platforms command-line argument (comma-separated)

    If not specified, all platforms are included.
    """
    # Check environment variable first
    if "INCLUDE_PLATFORMS" in os.environ:
        platforms = os.environ["INCLUDE_PLATFORMS"].split(",")
        return [p.strip() for p in platforms if p.strip()]

    # Check command-line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--include-platforms" and i + 1 < len(sys.argv):
            platforms = sys.argv[i + 1].split(",")
            return [p.strip() for p in platforms if p.strip()]
        elif arg.startswith("--include-platforms="):
            platforms = arg.split("=", 1)[1].split(",")
            return [p.strip() for p in platforms if p.strip()]

    # Default: include all platforms
    return list(PLAT_EXECUTABLE.keys())


def current_plat():
    """Detect current platform."""
    if platform == "darwin":
        if os.uname().machine == "arm64":
            return "macosx_11_0_arm64"
        return "macosx_10_7_x86_64"
    elif platform == "win32":
        return "win_amd64"
    elif platform in ("linux", "linux2"):
        if os.uname().machine == "aarch64":
            return "manylinux2014_aarch64"
        if os.path.exists("/etc/alpine-release"):
            return "musllinux_1_2_x86_64"
        else:
            return "manylinux1_x86_64"
    else:
        raise Exception("Platform is not supported", platform)


def get_target_platform():
    """Get the target platform from environment variable or detect current."""
    # Check if PLAT_NAME is specified in environment variable
    if "PLAT_NAME" in os.environ:
        return os.environ["PLAT_NAME"]

    # Check if --plat-name is specified in command line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--plat-name" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        elif arg.startswith("--plat-name="):
            return arg.split("=", 1)[1]

    # Fall back to current platform
    return current_plat()


# Select executable based on target platform
target_platform = get_target_platform()
selected_executable = PLAT_EXECUTABLE.get(
    target_platform, PLAT_EXECUTABLE[current_plat()]
)


class build_py(_build_py):
    """Build command that copies platform binary from built_bins/ directory."""

    def get_data_files(self):
        # Legacy builds always use built_bins/ directory (from sdist)
        source_dir = PKG_BUILT_BINS_DIR

        if not os.path.isdir(source_dir):
            raise RuntimeError(
                f"Binary source directory not found: {source_dir}\n"
                f"Legacy builds require built_bins/ directory with pre-built binaries.\n"
                f"This directory should be present in the source distribution."
            )

        if not self.dry_run and os.path.isdir(PKG_BIN_DIR):
            rmtree(PKG_BIN_DIR)

        os.makedirs(PKG_BIN_DIR, exist_ok=True)

        _, ext = os.path.splitext(selected_executable)
        target_name = os.path.join(PKG_BIN_DIR, "core" + ext)
        built_file_name = os.path.join(source_dir, selected_executable)

        # Verify the source file exists
        if not os.path.isfile(built_file_name):
            available_files = (
                ", ".join(os.listdir(source_dir))
                if os.path.isdir(source_dir)
                else "N/A"
            )
            raise RuntimeError(
                f"Binary not found: {built_file_name}\n"
                f"Platform: {target_platform}\n"
                f"Expected: {selected_executable}\n"
                f"Available in {source_dir}: {available_files}"
            )

        self.copy_file(built_file_name, target_name)
        os.chmod(target_name, 0o755)
        return _build_py.get_data_files(self)

    def run(self):
        """Run build_py and remove built_bins from build directory."""
        _build_py.run(self)
        # Remove built_bins from build directory after build completes
        built_bins_in_build = os.path.join(
            self.build_lib, "applitools", "core_universal", "built_bins"
        )
        if os.path.isdir(built_bins_in_build):
            self.announce(f"Removing {built_bins_in_build} from build", 2)
            rmtree(built_bins_in_build)


class sdist(_sdist):
    """Sdist command that generates setup.cfg and removes pyproject.toml."""

    def make_release_tree(self, base_dir, files):
        # Create the source tree
        super().make_release_tree(base_dir, files)

        # Generate setup.cfg from pyproject.toml (required for legacy mode)
        try:
            if sys.version_info >= (3, 11):
                import tomllib
            else:
                import tomli as tomllib
        except ImportError:
            raise RuntimeError(
                "Building legacy sdist requires tomllib (Python 3.11+) or tomli package.\n"
                "Install with: pip install tomli"
            )

        with open("pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        project = pyproject["project"]

        # Generate minimal setup.cfg with all metadata
        setup_cfg_content = f"""[metadata]
name = {project["name"]}
version = {project["version"]}
description = {project["description"]}
long_description = file: README.rst
long_description_content_type = text/x-rst
author = {project["authors"][0]["name"]}
author_email = {project["authors"][0]["email"]}
license_files = LICENSE
url = {project["urls"]["Homepage"]}
classifiers =
{chr(10).join('    ' + c for c in project["classifiers"])}
python_requires = {project["requires-python"]}

[options]
packages = applitools.core_universal
zip_safe = False
install_requires =
{chr(10).join('    ' + dep for dep in project.get("dependencies", []))}

[options.package_data]
applitools.core_universal = bin/*

[egg_info]
tag_build =
tag_date = 0
"""

        # Write setup.cfg to sdist
        setup_cfg_path = os.path.join(base_dir, "setup.cfg")
        with open(setup_cfg_path, "w") as f:
            f.write(setup_cfg_content)

        self.announce(
            f"Generated {setup_cfg_path} from pyproject.toml for legacy installation",
            2,
        )

        # Remove pyproject.toml from source distribution to force legacy mode
        pyproject_toml = os.path.join(base_dir, "pyproject.toml")
        if os.path.isfile(pyproject_toml):
            self.announce(
                f"Removing {pyproject_toml} from source distribution "
                "(forces legacy setup.py mode for restricted environments)",
                2,
            )
            os.remove(pyproject_toml)

        # Remove bin/ directory from source distribution
        bin_dir_in_sdist = os.path.join(base_dir, "applitools", "core_universal", "bin")
        if os.path.isdir(bin_dir_in_sdist):
            self.announce(f"Removing {bin_dir_in_sdist} from source distribution", 2)
            rmtree(bin_dir_in_sdist)

        # Filter built_bins based on included platforms
        included_platforms = get_included_platforms()
        built_bins_dir = os.path.join(
            base_dir, "applitools", "core_universal", "built_bins"
        )

        if os.path.isdir(built_bins_dir):
            # Get list of executables to keep
            executables_to_keep = [
                PLAT_EXECUTABLE[plat]
                for plat in included_platforms
                if plat in PLAT_EXECUTABLE
            ]

            # Remove executables not in the included list
            for filename in os.listdir(built_bins_dir):
                filepath = os.path.join(built_bins_dir, filename)
                if os.path.isfile(filepath) and filename not in executables_to_keep:
                    self.announce(
                        f"Removing {filename} from source distribution (not in included platforms)",
                        2,
                    )
                    os.remove(filepath)

            # Log which platforms are included
            self.announce(
                f"Including binaries for platforms: {', '.join(included_platforms)}",
                2,
            )

        # Replace modern setup.py with setup-legacy.py for restricted environment compatibility
        # The modern setup.py imports wheel directly and will fail in restricted environments
        modern_setup_py = os.path.join(base_dir, "setup.py")
        legacy_setup_py = os.path.join(base_dir, "setup-legacy.py")

        if os.path.isfile(modern_setup_py) and os.path.isfile(legacy_setup_py):
            self.announce(
                f"Replacing {modern_setup_py} with {legacy_setup_py} "
                "(modern setup.py requires wheel package)",
                2,
            )
            # Copy setup-legacy.py content to setup.py
            import shutil

            shutil.copy2(legacy_setup_py, modern_setup_py)

            # Remove setup-legacy.py from sdist (setup.py now contains the legacy code)
            self.announce(
                f"Removing {legacy_setup_py} from source distribution "
                "(setup.py already contains legacy implementation)",
                2,
            )
            os.remove(legacy_setup_py)


setup(cmdclass={"build_py": build_py, "sdist": sdist})
