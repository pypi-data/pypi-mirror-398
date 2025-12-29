# tests/test_version.py
from importlib.metadata import PackageNotFoundError, version

import pytest


def test_package_version():
    """Verify the package version matches pyproject.toml."""
    try:
        pkg_version = version("mail-ops-scripts")
        assert pkg_version == "2.4.0", f"Expected 2.4.0, got {pkg_version}"
    except PackageNotFoundError:
        pytest.skip("mail-ops-scripts not installed in environment")


def test_package_metadata():
    """Verify basic package metadata is accessible."""
    from importlib.metadata import metadata

    pkg_meta = metadata("mail-ops-scripts")
    assert pkg_meta["Name"] == "mail-ops-scripts"
    assert "MIT" in pkg_meta.get("License", "")
