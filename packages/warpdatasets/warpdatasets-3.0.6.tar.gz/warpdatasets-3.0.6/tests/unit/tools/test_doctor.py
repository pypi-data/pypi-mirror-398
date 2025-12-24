"""Tests for doctor checks."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from warpdatasets.config.settings import Settings
from warpdatasets.tools.doctor import (
    CheckResult,
    CheckStatus,
    check_settings,
    check_duckdb,
    check_pyarrow,
    check_connectivity,
    check_credentials,
    run_all_checks,
    format_result,
    format_report,
    format_json,
    has_failures,
)


# Fixtures


@pytest.fixture
def settings() -> Settings:
    """Create default settings."""
    return Settings()


@pytest.fixture
def settings_with_manifest_base() -> Settings:
    """Create settings with manifest_base."""
    return Settings(manifest_base="https://example.com/warp")


@pytest.fixture
def settings_with_s3() -> Settings:
    """Create settings with S3 manifest_base."""
    return Settings(manifest_base="s3://bucket/warp")


# CheckResult tests


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_check_result_pass(self):
        """Test CheckResult for passing check."""
        result = CheckResult(
            name="test",
            status=CheckStatus.PASS,
            message="Test passed",
        )

        assert result.name == "test"
        assert result.status == CheckStatus.PASS
        assert result.message == "Test passed"
        assert result.details is None
        assert result.suggestion is None

    def test_check_result_fail_with_details(self):
        """Test CheckResult for failing check with details."""
        result = CheckResult(
            name="connectivity",
            status=CheckStatus.FAIL,
            message="Cannot reach server",
            details="Connection timeout",
            suggestion="Check your network connection",
        )

        assert result.status == CheckStatus.FAIL
        assert result.details == "Connection timeout"
        assert result.suggestion == "Check your network connection"


class TestCheckStatus:
    """Tests for CheckStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert CheckStatus.PASS.value == "pass"
        assert CheckStatus.FAIL.value == "fail"
        assert CheckStatus.WARN.value == "warn"
        assert CheckStatus.SKIP.value == "skip"


# Check function tests


class TestCheckSettings:
    """Tests for check_settings function."""

    def test_settings_valid(self, settings):
        """Test valid settings pass."""
        result = check_settings(settings)

        assert result.status == CheckStatus.PASS
        assert "valid" in result.message.lower()

    def test_settings_invalid_mode(self):
        """Test invalid mode is detected."""
        settings = Settings()
        # Manually set invalid mode to bypass validation
        object.__setattr__(settings, "mode", "invalid_mode")

        result = check_settings(settings)

        assert result.status == CheckStatus.FAIL
        assert "mode" in result.message.lower()

    def test_settings_non_existent_workspace(self, tmp_path):
        """Test non-existent workspace root shows warning."""
        settings = Settings(workspace_root=tmp_path / "nonexistent")

        result = check_settings(settings)

        # Non-existent workspace is a warning, not failure
        assert result.status in (CheckStatus.PASS, CheckStatus.WARN)


class TestCheckDuckDB:
    """Tests for check_duckdb function."""

    def test_duckdb_available(self):
        """Test DuckDB is available."""
        result = check_duckdb()

        assert result.status == CheckStatus.PASS
        assert "duckdb" in result.name.lower()

    def test_duckdb_version_in_message(self):
        """Test DuckDB version is in message."""
        result = check_duckdb()

        # Should include version number
        assert result.status == CheckStatus.PASS
        # Version should be in format X.Y.Z
        import duckdb
        assert duckdb.__version__ in result.message


class TestCheckPyArrow:
    """Tests for check_pyarrow function."""

    def test_pyarrow_available(self):
        """Test PyArrow is available."""
        result = check_pyarrow()

        assert result.status == CheckStatus.PASS
        assert "pyarrow" in result.name.lower()

    def test_pyarrow_version_in_message(self):
        """Test PyArrow version is in message."""
        result = check_pyarrow()

        import pyarrow
        assert pyarrow.__version__ in result.message


class TestCheckConnectivity:
    """Tests for check_connectivity function."""

    def test_connectivity_no_manifest_base(self, settings):
        """Test connectivity skipped when no manifest_base."""
        result = check_connectivity(settings)

        assert result.status == CheckStatus.SKIP
        assert "no manifest_base" in result.message.lower()

    def test_connectivity_http_success(self, settings_with_manifest_base):
        """Test HTTP connectivity success."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = MagicMock()
            mock_urlopen.return_value.__exit__ = MagicMock()

            result = check_connectivity(settings_with_manifest_base)

            assert result.status == CheckStatus.PASS

    def test_connectivity_http_failure(self, settings_with_manifest_base):
        """Test HTTP connectivity failure."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Connection refused")

            result = check_connectivity(settings_with_manifest_base)

            assert result.status == CheckStatus.FAIL


class TestCheckCredentials:
    """Tests for check_credentials function."""

    def test_credentials_none(self):
        """Test no credentials detected."""
        with patch.dict(os.environ, {}, clear=True):
            # Also need to mock out the file checks
            with patch.object(Path, "exists", return_value=False):
                result = check_credentials()

                assert result.status == CheckStatus.WARN

    def test_credentials_aws_env(self):
        """Test AWS credentials in environment."""
        with patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "test_key"}):
            result = check_credentials()

            assert result.status == CheckStatus.PASS
            assert "AWS" in result.message


# Report formatting tests


class TestFormatResult:
    """Tests for format_result function."""

    def test_format_pass(self):
        """Test formatting a passing result."""
        result = CheckResult(
            name="test",
            status=CheckStatus.PASS,
            message="All good",
        )

        formatted = format_result(result, use_color=False)

        assert "✓" in formatted
        assert "test" in formatted
        assert "All good" in formatted

    def test_format_fail(self):
        """Test formatting a failing result."""
        result = CheckResult(
            name="test",
            status=CheckStatus.FAIL,
            message="Something wrong",
            suggestion="Fix it",
        )

        formatted = format_result(result, use_color=False)

        assert "✗" in formatted
        assert "Something wrong" in formatted
        assert "Fix it" in formatted

    def test_format_with_details_verbose(self):
        """Test details are shown in verbose mode."""
        result = CheckResult(
            name="test",
            status=CheckStatus.PASS,
            message="Good",
            details="Extra info",
        )

        formatted = format_result(result, use_color=False, verbose=True)

        assert "Extra info" in formatted


class TestFormatReport:
    """Tests for format_report function."""

    def test_format_report_header(self):
        """Test report has header."""
        results = [
            CheckResult(name="test", status=CheckStatus.PASS, message="OK"),
        ]

        report = format_report(results, use_color=False)

        assert "warpdatasets doctor" in report

    def test_format_report_summary(self):
        """Test report has summary."""
        results = [
            CheckResult(name="test1", status=CheckStatus.PASS, message="OK"),
            CheckResult(name="test2", status=CheckStatus.FAIL, message="Bad"),
        ]

        report = format_report(results, use_color=False)

        assert "1 passed" in report
        assert "1 failed" in report


class TestFormatJson:
    """Tests for format_json function."""

    def test_format_json_valid(self):
        """Test JSON output is valid."""
        results = [
            CheckResult(name="test", status=CheckStatus.PASS, message="OK"),
        ]

        json_str = format_json(results)
        data = json.loads(json_str)

        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["status"] == "pass"

    def test_format_json_summary(self):
        """Test JSON summary counts."""
        results = [
            CheckResult(name="test1", status=CheckStatus.PASS, message="OK"),
            CheckResult(name="test2", status=CheckStatus.FAIL, message="Bad"),
            CheckResult(name="test3", status=CheckStatus.WARN, message="Maybe"),
        ]

        json_str = format_json(results)
        data = json.loads(json_str)

        assert data["summary"]["passed"] == 1
        assert data["summary"]["failed"] == 1
        assert data["summary"]["warned"] == 1


class TestHasFailures:
    """Tests for has_failures function."""

    def test_no_failures(self):
        """Test no failures."""
        results = [
            CheckResult(name="test", status=CheckStatus.PASS, message="OK"),
            CheckResult(name="test2", status=CheckStatus.WARN, message="Warn"),
        ]

        assert not has_failures(results)

    def test_has_failure(self):
        """Test with failure."""
        results = [
            CheckResult(name="test", status=CheckStatus.PASS, message="OK"),
            CheckResult(name="test2", status=CheckStatus.FAIL, message="Bad"),
        ]

        assert has_failures(results)


# Integration tests


class TestRunAllChecks:
    """Tests for run_all_checks function."""

    def test_run_all_checks_basic(self, settings):
        """Test running all basic checks."""
        results = run_all_checks(settings)

        # Should have at least settings, duckdb, pyarrow, connectivity, credentials
        assert len(results) >= 5

        # Check names
        names = [r.name for r in results]
        assert "settings" in names
        assert "duckdb" in names
        assert "pyarrow" in names
        assert "connectivity" in names
        assert "credentials" in names

    def test_run_all_checks_with_dataset(self, settings):
        """Test running checks with dataset."""
        # This test may fail if the dataset doesn't exist
        # We just check that it doesn't crash
        results = run_all_checks(settings, dataset_id="nonexistent/dataset")

        # Should include dataset check
        names = [r.name for r in results]
        assert any("dataset" in name for name in names)
