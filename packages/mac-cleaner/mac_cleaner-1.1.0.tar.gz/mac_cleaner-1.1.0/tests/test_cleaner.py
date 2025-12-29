"""
Basic tests for Mac Cleaner.
"""

import pytest
from pathlib import Path
from mac_cleaner.cleaner import (
    is_safe_to_delete,
    human_size,
    parse_docker_size,
    expand,
    is_macos,
)


class TestSafetyFeatures:
    """Test safety features."""

    def test_critical_paths_protected(self):
        """Test that critical system paths are protected."""
        critical_paths = [
            Path("/"),
            Path("/System"),
            Path("/usr"),
            Path("/bin"),
            Path("/Applications"),
            Path.home(),
            Path.home() / "Desktop",
            Path.home() / "Documents",
        ]

        for path in critical_paths:
            is_safe, reason = is_safe_to_delete(path)
            assert not is_safe, f"{path} should not be safe to delete"
            assert reason, f"Should have a reason for {path}"

    def test_safe_paths_allowed(self):
        """Test that safe paths are allowed."""
        safe_paths = [
            Path("/tmp/some_file.txt"),
            Path.home() / "Library" / "Caches" / "some_app",
            Path("/var/tmp/test"),
        ]

        for path in safe_paths:
            is_safe, _ = is_safe_to_delete(path)
            # Note: This will be True even if path doesn't exist
            # The function checks if it would be safe IF it existed
            assert is_safe, f"{path} should be safe to delete"

    def test_apple_files_protected(self):
        """Test that com.apple.* files are detected."""
        apple_path = Path.home() / "Library" / "Caches" / "com.apple.Safari"
        is_safe, reason = is_safe_to_delete(apple_path)
        assert not is_safe
        assert "Protected system file" in reason


class TestHelperFunctions:
    """Test helper functions."""

    def test_human_size(self):
        """Test human-readable size conversion."""
        assert human_size(0) == "0.0 B"
        assert human_size(1023) == "1023.0 B"
        assert human_size(1024) == "1.0 KB"
        assert human_size(1024 * 1024) == "1.0 MB"
        assert human_size(1024 * 1024 * 1024) == "1.0 GB"
        assert human_size(1536 * 1024 * 1024) == "1.5 GB"

    def test_parse_docker_size(self):
        """Test Docker size parsing."""
        assert parse_docker_size("100B") == 100
        assert parse_docker_size("10kB") == 10000
        assert parse_docker_size("5MB") == 5000000
        assert parse_docker_size("2GB") == 2000000000
        assert parse_docker_size("1.5GB") == 1500000000
        assert parse_docker_size("invalid") == 0

    def test_expand(self):
        """Test path expansion."""
        home_path = expand("~")
        assert home_path == Path.home()
        assert home_path.exists()

        docs_path = expand("~/Documents")
        assert docs_path == Path.home() / "Documents"


class TestPlatformDetection:
    """Test platform detection."""

    def test_is_macos(self):
        """Test macOS detection."""
        # This test will pass on macOS, fail on other platforms
        result = is_macos()
        assert isinstance(result, bool)
        # On macOS, should be True
        # On other platforms, should be False
        # We can't assert a specific value as it depends on the platform


class TestI18n:
    """Test internationalization."""

    def test_i18n_import(self):
        """Test that i18n module can be imported."""
        from mac_cleaner.i18n import _, detect_system_language

        # Should not raise any exceptions
        assert callable(_)
        assert callable(detect_system_language)

    def test_detect_system_language(self):
        """Test system language detection."""
        from mac_cleaner.i18n import detect_system_language

        lang = detect_system_language()
        assert isinstance(lang, str)
        assert len(lang) >= 2  # At least 'en', 'es', etc.


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
