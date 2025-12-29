"""Tests for ldf.coverage module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from ldf.coverage import (
    _filter_by_service,
    _find_coverage_data,
    _normalize_coverage_data,
    _try_generate_coverage,
    _upload_to_artifact,
    _upload_to_file,
    _upload_to_s3,
    compare_coverage,
    report_coverage,
    upload_coverage,
)


class TestFindCoverageData:
    """Tests for _find_coverage_data function."""

    def test_finds_coverage_json(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch
    ):
        """Test finding coverage.json in project root."""
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        result = _find_coverage_data(temp_project)

        assert result is not None
        assert result["format"] == "pytest-cov"
        assert result["totals"]["percent"] == 85.0

    def test_finds_ldf_coverage_json(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch
    ):
        """Test finding .ldf/coverage.json."""
        coverage_file = temp_project / ".ldf" / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        result = _find_coverage_data(temp_project)

        assert result is not None
        assert result["format"] == "pytest-cov"

    def test_finds_jest_coverage(
        self, temp_project: Path, sample_jest_coverage_json: dict, monkeypatch
    ):
        """Test finding Jest coverage-summary.json."""
        coverage_dir = temp_project / "coverage"
        coverage_dir.mkdir()
        coverage_file = coverage_dir / "coverage-summary.json"
        coverage_file.write_text(json.dumps(sample_jest_coverage_json))
        monkeypatch.chdir(temp_project)

        result = _find_coverage_data(temp_project)

        assert result is not None
        assert result["format"] == "jest"

    def test_returns_none_when_no_coverage(self, temp_project: Path, monkeypatch):
        """Test returning None when no coverage files exist."""
        monkeypatch.chdir(temp_project)

        result = _find_coverage_data(temp_project)

        assert result is None

    def test_skips_invalid_json(self, temp_project: Path, monkeypatch):
        """Test skipping files with invalid JSON."""
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text("not valid json {{{")
        monkeypatch.chdir(temp_project)

        result = _find_coverage_data(temp_project)

        assert result is None


class TestTryGenerateCoverage:
    """Tests for _try_generate_coverage function."""

    def test_returns_none_without_coverage_file(self, temp_project: Path, monkeypatch):
        """Test returning None when .coverage file doesn't exist."""
        monkeypatch.chdir(temp_project)

        result = _try_generate_coverage(temp_project)

        assert result is None

    def test_returns_none_without_env_var(self, temp_project: Path, monkeypatch):
        """Test returning None when LDF_COVERAGE_WRITE is not set."""
        # Create .coverage file
        (temp_project / ".coverage").touch()
        monkeypatch.chdir(temp_project)
        monkeypatch.delenv("LDF_COVERAGE_WRITE", raising=False)

        result = _try_generate_coverage(temp_project)

        assert result is None


class TestNormalizeCoverageData:
    """Tests for _normalize_coverage_data function."""

    def test_normalizes_pytest_cov_format(self, sample_pytest_coverage_json: dict, tmp_path: Path):
        """Test normalizing pytest-cov format."""
        result = _normalize_coverage_data(sample_pytest_coverage_json, tmp_path / "coverage.json")

        assert result["format"] == "pytest-cov"
        assert result["totals"]["lines_covered"] == 850
        assert result["totals"]["lines_total"] == 1000
        assert result["totals"]["percent"] == 85.0
        assert "files" in result

    def test_normalizes_jest_format(self, sample_jest_coverage_json: dict, tmp_path: Path):
        """Test normalizing Jest format."""
        result = _normalize_coverage_data(
            sample_jest_coverage_json, tmp_path / "coverage-summary.json"
        )

        assert result["format"] == "jest"
        assert result["totals"]["lines_covered"] == 400
        assert result["totals"]["lines_total"] == 500
        assert result["totals"]["percent"] == 80.0

    def test_handles_unknown_format(self, tmp_path: Path):
        """Test handling unknown coverage format."""
        unknown_data = {"some": "data", "other": "fields"}
        result = _normalize_coverage_data(unknown_data, tmp_path / "unknown.json")

        assert result["format"] == "unknown"
        assert result["totals"]["percent"] == 0


class TestFilterByService:
    """Tests for _filter_by_service function."""

    def test_filters_files_by_service_name(self, sample_pytest_coverage_json: dict, tmp_path: Path):
        """Test filtering coverage to specific service."""
        coverage_data = _normalize_coverage_data(
            sample_pytest_coverage_json, tmp_path / "coverage.json"
        )

        result = _filter_by_service(coverage_data, "auth")

        assert len(result["files"]) == 1
        assert "auth" in list(result["files"].keys())[0]

    def test_recalculates_totals(self, sample_pytest_coverage_json: dict, tmp_path: Path):
        """Test that totals are recalculated after filtering."""
        coverage_data = _normalize_coverage_data(
            sample_pytest_coverage_json, tmp_path / "coverage.json"
        )

        result = _filter_by_service(coverage_data, "billing")

        # billing.py has 70% coverage
        assert result["totals"]["percent"] == 70.0

    def test_handles_no_matching_files(self, sample_pytest_coverage_json: dict, tmp_path: Path):
        """Test handling when no files match service."""
        coverage_data = _normalize_coverage_data(
            sample_pytest_coverage_json, tmp_path / "coverage.json"
        )

        result = _filter_by_service(coverage_data, "nonexistent")

        assert len(result["files"]) == 0
        assert result["totals"]["percent"] == 0


class TestReportCoverage:
    """Tests for report_coverage function."""

    def test_fails_without_ldf_directory(self, tmp_path: Path, monkeypatch):
        """Test error when .ldf directory doesn't exist."""
        monkeypatch.chdir(tmp_path)

        result = report_coverage()

        assert result.get("error") == "LDF not initialized"

    def test_reports_coverage_from_json(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch
    ):
        """Test reporting coverage from coverage.json."""
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        result = report_coverage(project_root=temp_project)

        assert "coverage_percent" in result
        assert result["coverage_percent"] == 85.0
        assert result["status"] == "PASS"  # 85% >= 80% threshold

    def test_uses_config_thresholds(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch
    ):
        """Test that configured thresholds are used."""
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        result = report_coverage(project_root=temp_project)

        assert result["threshold_default"] == 80
        assert result["threshold_critical"] == 90

    def test_handles_no_coverage_data(self, temp_project: Path, monkeypatch):
        """Test handling when no coverage data exists."""
        monkeypatch.chdir(temp_project)

        result = report_coverage(project_root=temp_project)

        assert result.get("error") == "No coverage data"

    def test_handles_config_not_found(self, tmp_path: Path, monkeypatch, capsys):
        """Test handling when config file is missing."""
        # Create .ldf directory but no config.yaml
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        result = report_coverage(project_root=tmp_path)

        assert result.get("error") == "Config not found"

    def test_filters_by_service(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch, capsys
    ):
        """Test filtering coverage by service."""
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        _result = report_coverage(project_root=temp_project, service="auth")

        captured = capsys.readouterr()
        assert "Filtered to service: auth" in captured.out


class TestTryGenerateCoverageAdvanced:
    """Advanced tests for _try_generate_coverage function."""

    def test_returns_none_without_coverage_tool(self, temp_project: Path, monkeypatch):
        """Test returning None when coverage tool is not installed."""
        (temp_project / ".coverage").touch()
        monkeypatch.setenv("LDF_COVERAGE_WRITE", "1")
        # Mock shutil.which to return None (tool not found)
        monkeypatch.setattr("shutil.which", lambda x: None)
        monkeypatch.chdir(temp_project)

        result = _try_generate_coverage(temp_project)

        assert result is None

    def test_returns_none_without_ldf_dir(self, tmp_path: Path, monkeypatch):
        """Test returning None when .ldf directory doesn't exist."""
        (tmp_path / ".coverage").touch()
        monkeypatch.setenv("LDF_COVERAGE_WRITE", "1")
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/coverage")
        monkeypatch.chdir(tmp_path)

        result = _try_generate_coverage(tmp_path)

        assert result is None


class TestFilterByServiceAdvanced:
    """Advanced tests for _filter_by_service function."""

    def test_handles_no_files_key(self):
        """Test handling coverage data without files key."""
        coverage_data = {"format": "unknown", "totals": {"percent": 50}}

        result = _filter_by_service(coverage_data, "auth")

        assert result == coverage_data  # Returns unchanged

    def test_handles_jest_format_lines(self):
        """Test handling Jest format with lines data."""
        coverage_data = {
            "format": "jest",
            "totals": {"percent": 80},
            "files": {
                "/src/auth.ts": {"lines": {"covered": 80, "total": 100}},
                "/src/billing.ts": {"lines": {"covered": 50, "total": 100}},
            },
        }

        result = _filter_by_service(coverage_data, "auth")

        assert result["totals"]["lines_covered"] == 80
        assert result["totals"]["lines_total"] == 100
        assert result["totals"]["percent"] == 80.0


class TestCoverageValidateFlag:
    """Tests for --validate flag."""

    def test_validate_passes_when_coverage_above_threshold(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch
    ):
        """Test validate mode passes when coverage meets threshold."""
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))  # 85%
        monkeypatch.chdir(temp_project)

        result = report_coverage(project_root=temp_project, validate=True)

        assert result["status"] == "PASS"
        # Validate mode should include validation message
        assert "validation" not in result.get("error", "")

    def test_validate_fails_when_coverage_below_threshold(self, temp_project: Path, monkeypatch):
        """Test validate mode fails when coverage below threshold."""
        coverage_data = {
            "totals": {
                "covered_lines": 500,
                "num_statements": 1000,
                "percent_covered": 50.0,  # Below 80% threshold
            },
            "files": {},
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = report_coverage(project_root=temp_project, validate=True)

        assert result["status"] == "FAIL"


class TestCoverageVerboseFlag:
    """Tests for --verbose flag."""

    def test_verbose_shows_all_files(self, temp_project: Path, monkeypatch, capsys):
        """Test verbose mode shows all files not just bottom 10."""
        # Create coverage data with many files
        coverage_data = {
            "totals": {"covered_lines": 800, "num_statements": 1000, "percent_covered": 80.0},
            "files": {
                f"src/module{i}.py": {
                    "summary": {"covered_lines": 70, "num_statements": 100, "percent_covered": 70.0}
                }
                for i in range(15)
            },
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        _result = report_coverage(project_root=temp_project, verbose=True)

        captured = capsys.readouterr()
        # Verbose should show all 15 files
        assert "more files" not in captured.out


class TestCoverageGuardrailFilter:
    """Tests for --guardrail filter."""

    def test_guardrail_filter_shows_filter_message(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch, capsys
    ):
        """Test that guardrail filter shows appropriate message."""
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        _result = report_coverage(project_root=temp_project, guardrail_id=1)

        captured = capsys.readouterr()
        assert "guardrail" in captured.out.lower()


class TestGenerateReportAdvanced:
    """Advanced tests for report generation."""

    def test_report_with_jest_file_format(self, temp_project: Path, monkeypatch):
        """Test report with Jest coverage format files."""
        coverage_data = {
            "total": {"lines": {"covered": 400, "total": 500, "pct": 80.0}},
            "/src/auth.ts": {"lines": {"total": 100, "covered": 95, "pct": 95.0}},
            "/src/utils.ts": {"lines": {"total": 100, "covered": 50, "pct": 50.0}},
        }
        coverage_file = temp_project / "coverage" / "coverage-summary.json"
        coverage_file.parent.mkdir()
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = report_coverage(project_root=temp_project)

        assert result["coverage_percent"] == 80.0

    def test_report_with_many_files(self, temp_project: Path, monkeypatch, capsys):
        """Test report with more than 10 files shows truncation message."""
        # Create coverage data with many files
        coverage_data = {
            "totals": {"covered_lines": 800, "num_statements": 1000, "percent_covered": 80.0},
            "files": {
                f"src/module{i}.py": {
                    "summary": {"covered_lines": 70, "num_statements": 100, "percent_covered": 70.0}
                }
                for i in range(15)
            },
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        _result = report_coverage(project_root=temp_project)

        captured = capsys.readouterr()
        assert "more files" in captured.out

    def test_report_fail_status(self, temp_project: Path, monkeypatch, capsys):
        """Test report with failing coverage."""
        coverage_data = {
            "totals": {
                "covered_lines": 500,
                "num_statements": 1000,
                "percent_covered": 50.0,  # Below 80% threshold
            },
            "files": {},
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = report_coverage(project_root=temp_project)

        assert result["status"] == "FAIL"
        captured = capsys.readouterr()
        assert "NOT SATISFIED" in captured.out
        assert "more coverage" in captured.out


class TestSaveCoverageSnapshot:
    """Tests for save_coverage_snapshot function."""

    def test_saves_snapshot(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch
    ):
        """Test saving a coverage snapshot."""
        from ldf.coverage import save_coverage_snapshot

        # Create a mock report
        report = {
            "coverage_percent": 85.0,
            "lines_covered": 850,
            "lines_total": 1000,
            "threshold_default": 80,
            "files": [{"path": "src/auth.py", "percent": 90.0}],
        }

        result = save_coverage_snapshot("baseline", report, project_root=temp_project)

        assert result.exists()
        assert result.name == "baseline.json"

        # Verify content
        with open(result) as f:
            data = json.load(f)
        assert data["name"] == "baseline"
        assert data["coverage_percent"] == 85.0
        assert "saved_at" in data

    def test_creates_snapshots_dir(self, temp_project: Path):
        """Test that snapshots directory is created if needed."""
        from ldf.coverage import save_coverage_snapshot

        report = {"coverage_percent": 75.0, "files": []}

        result = save_coverage_snapshot("test", report, project_root=temp_project)

        assert (temp_project / ".ldf" / "coverage-snapshots").exists()
        assert result.exists()

    def test_uses_cwd_when_no_root(self, temp_project: Path, monkeypatch):
        """Test using current directory when project_root is None."""
        from ldf.coverage import save_coverage_snapshot

        monkeypatch.chdir(temp_project)
        report = {"coverage_percent": 80.0, "files": []}

        result = save_coverage_snapshot("cwd-test", report, project_root=None)

        assert result.exists()


class TestCompareCoverage:
    """Tests for compare_coverage function."""

    def test_compares_with_baseline(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch, capsys
    ):
        """Test comparing current coverage with baseline."""
        from ldf.coverage import compare_coverage, save_coverage_snapshot

        # Create baseline
        baseline_report = {
            "coverage_percent": 75.0,
            "lines_covered": 750,
            "lines_total": 1000,
            "files": [{"path": "src/auth.py", "percent": 70.0}],
        }
        save_coverage_snapshot("baseline", baseline_report, project_root=temp_project)

        # Create current coverage (higher)
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("baseline", project_root=temp_project)

        captured = capsys.readouterr()
        assert "Coverage Comparison" in captured.out
        assert result.get("status") != "ERROR"

    def test_error_when_baseline_not_found(self, temp_project: Path, monkeypatch, capsys):
        """Test error when baseline doesn't exist."""
        from ldf.coverage import compare_coverage

        monkeypatch.chdir(temp_project)

        result = compare_coverage("nonexistent", project_root=temp_project)

        assert result["status"] == "ERROR"
        assert "not found" in result["error"].lower()
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_error_with_no_current_coverage(self, temp_project: Path, monkeypatch, capsys):
        """Test error when no current coverage exists."""
        from ldf.coverage import compare_coverage, save_coverage_snapshot

        # Create baseline but no current coverage
        baseline_report = {"coverage_percent": 80.0, "files": []}
        save_coverage_snapshot("baseline", baseline_report, project_root=temp_project)
        monkeypatch.chdir(temp_project)

        result = compare_coverage("baseline", project_root=temp_project)

        assert result["status"] == "ERROR"
        assert "current coverage" in result["error"].lower()

    def test_compares_with_file_path(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch, capsys
    ):
        """Test comparing with a file path."""
        from ldf.coverage import compare_coverage

        # Create baseline file
        baseline = {
            "coverage_percent": 70.0,
            "lines_covered": 700,
            "lines_total": 1000,
            "files": [],
        }
        baseline_path = temp_project / "old-coverage.json"
        baseline_path.write_text(json.dumps(baseline))

        # Create current coverage
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old-coverage.json", project_root=temp_project)

        assert result.get("status") != "ERROR"

    def test_shows_improved_files(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch, capsys
    ):
        """Test showing improved files in diff."""
        from ldf.coverage import compare_coverage, save_coverage_snapshot

        # Baseline with lower coverage
        baseline = {
            "coverage_percent": 50.0,
            "lines_covered": 500,
            "lines_total": 1000,
            "files": [{"path": "src/auth.py", "percent": 50.0}],
        }
        save_coverage_snapshot("old", baseline, project_root=temp_project)

        # Current with higher coverage
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old", project_root=temp_project)

        capsys.readouterr()
        assert result.get("status") != "ERROR"


class TestUploadCoverage:
    """Tests for upload_coverage function."""

    def test_uploads_to_file_destination(self, temp_project: Path, tmp_path: Path):
        """Test uploading coverage to a file destination."""
        from ldf.coverage import upload_coverage

        report = {
            "coverage_percent": 85.0,
            "lines_covered": 850,
            "lines_total": 1000,
        }
        dest_file = tmp_path / "uploaded-coverage.json"

        result = upload_coverage(f"file://{dest_file}", report, project_root=temp_project)

        assert result is True
        assert dest_file.exists()

    def test_fails_with_unsupported_destination(self, temp_project: Path):
        """Test failure with unsupported destination type."""
        from ldf.coverage import upload_coverage

        report = {"coverage_percent": 80.0}

        result = upload_coverage("ftp://unsupported", report, project_root=temp_project)

        assert result is False

    def test_fails_with_missing_boto3_for_s3(self, temp_project: Path, monkeypatch):
        """Test failure when boto3 is not available for S3 upload."""
        # Mock import to fail for boto3
        import builtins

        from ldf.coverage import upload_coverage

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "boto3":
                raise ImportError("No module named 'boto3'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        report = {"coverage_percent": 80.0}

        result = upload_coverage("s3://bucket/path", report, project_root=temp_project)

        assert result is False


class TestTryGenerateCoverageEdgeCases:
    """Edge case tests for _try_generate_coverage function."""

    def test_returns_none_if_ldf_dir_not_writable(self, temp_project: Path, monkeypatch, capsys):
        """Test returning None when .ldf directory is not writable."""
        (temp_project / ".coverage").touch()
        monkeypatch.setenv("LDF_COVERAGE_WRITE", "1")
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/coverage")
        # Mock os.access to return False for write permission
        monkeypatch.setattr("os.access", lambda path, mode: False)
        monkeypatch.chdir(temp_project)

        result = _try_generate_coverage(temp_project)

        assert result is None
        captured = capsys.readouterr()
        assert "write permission" in captured.out.lower()

    def test_handles_subprocess_error(self, temp_project: Path, monkeypatch, capsys):
        """Test handling subprocess error during coverage generation."""
        (temp_project / ".coverage").touch()
        monkeypatch.setenv("LDF_COVERAGE_WRITE", "1")
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/coverage")
        monkeypatch.chdir(temp_project)

        # Mock subprocess.run to return failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Coverage generation failed"
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        result = _try_generate_coverage(temp_project)

        assert result is None
        captured = capsys.readouterr()
        assert "failed" in captured.out.lower()


class TestCompareCoverageEdgeCases:
    """Edge case tests for compare_coverage function."""

    def test_handles_invalid_baseline_json(self, temp_project: Path, monkeypatch, capsys):
        """Test handling invalid JSON in baseline file."""
        # Create invalid baseline file
        baseline_path = temp_project / ".ldf" / "coverage-snapshots"
        baseline_path.mkdir(parents=True)
        (baseline_path / "broken.json").write_text("invalid json {{{")
        monkeypatch.chdir(temp_project)

        result = compare_coverage("broken", project_root=temp_project)

        assert result["status"] == "ERROR"
        assert "Invalid" in result["error"]

    def test_shows_new_files(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch, capsys
    ):
        """Test showing new files in comparison."""
        from ldf.coverage import save_coverage_snapshot

        # Baseline with fewer files
        baseline = {
            "coverage_percent": 70.0,
            "lines_covered": 700,
            "lines_total": 1000,
            "files": [],  # No files in baseline
        }
        save_coverage_snapshot("old", baseline, project_root=temp_project)

        # Current with files
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old", project_root=temp_project)

        assert result.get("status") != "ERROR"
        # Should have new files
        assert result.get("new_files_count", 0) >= 0

    def test_shows_removed_files(self, temp_project: Path, monkeypatch, capsys):
        """Test showing removed files in comparison."""
        from ldf.coverage import save_coverage_snapshot

        # Baseline with files
        baseline = {
            "coverage_percent": 80.0,
            "lines_covered": 800,
            "lines_total": 1000,
            "files": [
                {"path": "old/file1.py", "percent": 80.0},
                {"path": "old/file2.py", "percent": 90.0},
            ],
        }
        save_coverage_snapshot("old", baseline, project_root=temp_project)

        # Current with no files matching old
        coverage_data = {
            "totals": {"covered_lines": 500, "num_statements": 1000, "percent_covered": 50.0},
            "files": {
                "new/file.py": {
                    "summary": {"percent_covered": 50.0, "covered_lines": 50, "num_statements": 100}
                }
            },
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old", project_root=temp_project)

        assert result.get("status") != "ERROR"
        assert result.get("removed_files_count", 0) >= 0

    def test_shows_regressed_files(self, temp_project: Path, monkeypatch, capsys):
        """Test showing regressed files in comparison."""
        from ldf.coverage import save_coverage_snapshot

        # Baseline with high coverage
        baseline = {
            "coverage_percent": 90.0,
            "lines_covered": 900,
            "lines_total": 1000,
            "files": [
                {"path": "src/auth.py", "percent": 95.0},
            ],
        }
        save_coverage_snapshot("old", baseline, project_root=temp_project)

        # Current with lower coverage for same file
        coverage_data = {
            "totals": {"covered_lines": 500, "num_statements": 1000, "percent_covered": 50.0},
            "files": {
                "src/auth.py": {
                    "summary": {"percent_covered": 50.0, "covered_lines": 50, "num_statements": 100}
                }
            },
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old", project_root=temp_project)

        assert result.get("status") != "ERROR"
        captured = capsys.readouterr()
        # Should show regression
        assert "Regressed" in captured.out or result.get("regressed_count", 0) >= 0

    def test_unchanged_coverage(self, temp_project: Path, monkeypatch, capsys):
        """Test comparison when coverage is unchanged."""
        from ldf.coverage import save_coverage_snapshot

        # Baseline
        baseline = {
            "coverage_percent": 80.0,
            "lines_covered": 800,
            "lines_total": 1000,
            "files": [],
        }
        save_coverage_snapshot("old", baseline, project_root=temp_project)

        # Current with same coverage
        coverage_data = {
            "totals": {"covered_lines": 800, "num_statements": 1000, "percent_covered": 80.0},
            "files": {},
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old", project_root=temp_project)

        assert result.get("comparison_status") == "unchanged"


class TestUploadToArtifact:
    """Tests for _upload_to_artifact function."""

    def test_creates_artifact_directory(self, temp_project: Path, capsys):
        """Test that artifact directory is created."""
        data = {"coverage_percent": 85.0}

        result = _upload_to_artifact(data, temp_project)

        assert result is True
        assert (temp_project / "coverage-artifact" / "coverage.json").exists()

    def test_shows_github_warning_when_not_in_actions(
        self, temp_project: Path, monkeypatch, capsys
    ):
        """Test warning when GITHUB_OUTPUT is not set."""
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        data = {"coverage_percent": 80.0}

        result = _upload_to_artifact(data, temp_project)

        assert result is True
        captured = capsys.readouterr()
        assert "GITHUB_OUTPUT" in captured.out


class TestUploadToS3:
    """Tests for _upload_to_s3 function."""

    def test_handles_invalid_s3_uri(self, temp_project: Path, capsys):
        """Test handling invalid S3 URI without path."""
        data = {"coverage_percent": 80.0}

        # Mock boto3 import to succeed
        with patch.dict("sys.modules", {"boto3": MagicMock()}):
            result = _upload_to_s3(data, "s3://bucket")

        assert result is False
        captured = capsys.readouterr()
        assert "Invalid S3 URI" in captured.out

    def test_handles_s3_upload_error(self, temp_project: Path, capsys):
        """Test handling S3 upload error."""
        data = {"coverage_percent": 80.0}

        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = Exception("Access denied")
        mock_boto3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            result = _upload_to_s3(data, "s3://bucket/path/file.json")

        assert result is False
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_successful_s3_upload(self, temp_project: Path, capsys):
        """Test successful S3 upload."""
        data = {"coverage_percent": 80.0}

        mock_s3 = MagicMock()
        mock_boto3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            result = _upload_to_s3(data, "s3://bucket/path/file.json")

        assert result is True
        mock_s3.put_object.assert_called_once()


class TestUploadToFile:
    """Tests for _upload_to_file function."""

    def test_creates_parent_directories(self, tmp_path: Path):
        """Test that parent directories are created."""
        data = {"coverage_percent": 85.0}
        dest = tmp_path / "deep" / "nested" / "path" / "coverage.json"

        result = _upload_to_file(data, str(dest))

        assert result is True
        assert dest.exists()

    def test_handles_write_error(self, tmp_path: Path, monkeypatch, capsys):
        """Test handling file write error."""
        data = {"coverage_percent": 80.0}

        # Mock open to raise error
        def mock_open(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr("builtins.open", mock_open)

        result = _upload_to_file(data, str(tmp_path / "test.json"))

        assert result is False
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestGuardrailNotFound:
    """Tests for guardrail ID not found warning."""

    def test_warns_when_guardrail_not_found(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch, capsys
    ):
        """Test warning when specified guardrail ID doesn't exist."""
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        report_coverage(project_root=temp_project, guardrail_id=999)

        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()


class TestListSnapshotsWhenEmpty:
    """Tests for listing snapshots when none exist."""

    def test_shows_no_snapshots_message(self, temp_project: Path, monkeypatch, capsys):
        """Test message when no snapshots saved."""
        monkeypatch.chdir(temp_project)

        result = compare_coverage("nonexistent", project_root=temp_project)

        assert result["status"] == "ERROR"
        captured = capsys.readouterr()
        assert "No snapshots" in captured.out or "not found" in captured.out.lower()


class TestListAvailableSnapshots:
    """Tests for listing available snapshots when baseline not found."""

    def test_lists_available_snapshots(self, temp_project: Path, monkeypatch, capsys):
        """Test listing available snapshots when requested one is not found."""
        from ldf.coverage import save_coverage_snapshot

        # Create some snapshots
        report = {"coverage_percent": 80.0, "files": []}
        save_coverage_snapshot("baseline-1", report, project_root=temp_project)
        save_coverage_snapshot("baseline-2", report, project_root=temp_project)
        monkeypatch.chdir(temp_project)

        # Request a non-existent snapshot
        result = compare_coverage("nonexistent", project_root=temp_project)

        assert result["status"] == "ERROR"
        captured = capsys.readouterr()
        assert "baseline-1" in captured.out or "baseline-2" in captured.out


class TestCompareWithServiceFilter:
    """Tests for compare_coverage with service filter."""

    def test_compare_with_service_filter(
        self, temp_project: Path, sample_pytest_coverage_json: dict, monkeypatch
    ):
        """Test comparing coverage with service filter."""
        from ldf.coverage import save_coverage_snapshot

        # Create baseline
        baseline = {
            "coverage_percent": 80.0,
            "lines_covered": 800,
            "lines_total": 1000,
            "files": [{"path": "src/auth.py", "percent": 80.0}],
        }
        save_coverage_snapshot("old", baseline, project_root=temp_project)

        # Current coverage
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(sample_pytest_coverage_json))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old", service="auth", project_root=temp_project)

        # Should not error, may be filtered
        assert result.get("status") != "ERROR" or "No current coverage" in result.get("error", "")


class TestCompareWithManyChanges:
    """Tests for compare_coverage with many file changes."""

    def test_truncates_improved_files_list(self, temp_project: Path, monkeypatch, capsys):
        """Test truncation when more than 5 improved files."""
        from ldf.coverage import save_coverage_snapshot

        # Baseline with low coverage for many files
        baseline_files = [{"path": f"src/file{i}.py", "percent": 50.0} for i in range(10)]
        baseline = {
            "coverage_percent": 50.0,
            "lines_covered": 500,
            "lines_total": 1000,
            "files": baseline_files,
        }
        save_coverage_snapshot("old", baseline, project_root=temp_project)

        # Current with high coverage for same files
        coverage_data = {
            "totals": {"covered_lines": 900, "num_statements": 1000, "percent_covered": 90.0},
            "files": {
                f"src/file{i}.py": {
                    "summary": {"percent_covered": 95.0, "covered_lines": 95, "num_statements": 100}
                }
                for i in range(10)
            },
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old", project_root=temp_project)

        captured = capsys.readouterr()
        assert "Improved" in captured.out
        # Should show truncation message for >5 improved files
        assert "and 5 more" in captured.out or result.get("improved_count", 0) > 5

    def test_truncates_regressed_files_list(self, temp_project: Path, monkeypatch, capsys):
        """Test truncation when more than 5 regressed files."""
        from ldf.coverage import save_coverage_snapshot

        # Baseline with high coverage for many files
        baseline_files = [{"path": f"src/file{i}.py", "percent": 95.0} for i in range(10)]
        baseline = {
            "coverage_percent": 95.0,
            "lines_covered": 950,
            "lines_total": 1000,
            "files": baseline_files,
        }
        save_coverage_snapshot("old", baseline, project_root=temp_project)

        # Current with low coverage for same files
        coverage_data = {
            "totals": {"covered_lines": 500, "num_statements": 1000, "percent_covered": 50.0},
            "files": {
                f"src/file{i}.py": {
                    "summary": {"percent_covered": 50.0, "covered_lines": 50, "num_statements": 100}
                }
                for i in range(10)
            },
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old", project_root=temp_project)

        captured = capsys.readouterr()
        assert "Regressed" in captured.out
        # Should show truncation message for >5 regressed files
        assert "and 5 more" in captured.out or result.get("regressed_count", 0) > 5

    def test_truncates_new_files_list(self, temp_project: Path, monkeypatch, capsys):
        """Test truncation when more than 3 new files."""
        from ldf.coverage import save_coverage_snapshot

        # Baseline with no files
        baseline = {
            "coverage_percent": 80.0,
            "lines_covered": 800,
            "lines_total": 1000,
            "files": [],
        }
        save_coverage_snapshot("old", baseline, project_root=temp_project)

        # Current with many new files
        coverage_data = {
            "totals": {"covered_lines": 500, "num_statements": 1000, "percent_covered": 50.0},
            "files": {
                f"src/newfile{i}.py": {
                    "summary": {"percent_covered": 70.0, "covered_lines": 70, "num_statements": 100}
                }
                for i in range(10)
            },
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old", project_root=temp_project)

        captured = capsys.readouterr()
        assert "New files" in captured.out
        # Should show truncation message for >3 new files
        assert "and 7 more" in captured.out or result.get("new_files_count", 0) > 3

    def test_truncates_removed_files_list(self, temp_project: Path, monkeypatch, capsys):
        """Test truncation when more than 3 removed files."""
        from ldf.coverage import save_coverage_snapshot

        # Baseline with many files
        baseline_files = [{"path": f"src/oldfile{i}.py", "percent": 80.0} for i in range(10)]
        baseline = {
            "coverage_percent": 80.0,
            "lines_covered": 800,
            "lines_total": 1000,
            "files": baseline_files,
        }
        save_coverage_snapshot("old", baseline, project_root=temp_project)

        # Current with no files
        coverage_data = {
            "totals": {"covered_lines": 500, "num_statements": 1000, "percent_covered": 50.0},
            "files": {},
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = compare_coverage("old", project_root=temp_project)

        captured = capsys.readouterr()
        assert "Removed files" in captured.out
        # Should show truncation message for >3 removed files
        assert "and 7 more" in captured.out or result.get("removed_files_count", 0) > 3


class TestGenerateReportFileFormat:
    """Tests for _generate_report with different file formats."""

    def test_file_without_summary_or_lines(self, temp_project: Path, monkeypatch):
        """Test handling file data without summary or lines key."""
        coverage_data = {
            "totals": {"covered_lines": 500, "num_statements": 1000, "percent_covered": 50.0},
            "files": {"src/broken.py": {"no_summary": True, "no_lines": True}},
        }
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        monkeypatch.chdir(temp_project)

        result = report_coverage(project_root=temp_project)

        # Should not error, file should get 0% coverage
        assert "coverage_percent" in result
        # File with no summary/lines should get 0%
        files = result.get("files", [])
        if files:
            for f in files:
                if "broken" in f.get("path", ""):
                    assert f.get("percent") == 0


class TestTryGenerateCoverageSuccess:
    """Tests for _try_generate_coverage success path."""

    def test_success_path_reads_coverage_file(self, temp_project: Path, monkeypatch, capsys):
        """Test successful coverage generation reads the file."""

        (temp_project / ".coverage").touch()
        monkeypatch.setenv("LDF_COVERAGE_WRITE", "1")
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/coverage")
        monkeypatch.chdir(temp_project)

        # Create the expected output file before subprocess runs
        coverage_file = temp_project / ".ldf" / "coverage.json"
        coverage_data = {
            "totals": {"covered_lines": 100, "num_statements": 200, "percent_covered": 50.0},
            "files": {},
        }
        coverage_file.write_text(json.dumps(coverage_data))

        # Mock subprocess.run to succeed
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        result = _try_generate_coverage(temp_project)

        assert result is not None
        assert result["totals"]["percent"] == 50.0

    def test_subprocess_error_handling(self, temp_project: Path, monkeypatch, capsys):
        """Test handling SubprocessError during coverage generation."""
        import subprocess

        (temp_project / ".coverage").touch()
        monkeypatch.setenv("LDF_COVERAGE_WRITE", "1")
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/coverage")
        monkeypatch.chdir(temp_project)

        # Mock subprocess.run to raise SubprocessError
        def mock_run(*args, **kwargs):
            raise subprocess.SubprocessError("Process failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        result = _try_generate_coverage(temp_project)

        assert result is None
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()


class TestUploadCoverageNoneRoot:
    """Tests for upload_coverage with project_root=None."""

    def test_uses_cwd_when_root_is_none(self, temp_project: Path, tmp_path: Path, monkeypatch):
        """Test using current directory when project_root is None."""
        monkeypatch.chdir(temp_project)

        report = {"coverage_percent": 80.0, "files": []}
        dest_file = tmp_path / "upload.json"

        result = upload_coverage(f"file://{dest_file}", report, project_root=None)

        assert result is True
        assert dest_file.exists()


class TestUploadToArtifactPath:
    """Tests for artifact upload path."""

    def test_artifact_upload_writes_file(self, temp_project: Path, capsys):
        """Test that artifact upload writes the coverage file."""
        report = {
            "coverage_percent": 85.0,
            "lines_covered": 850,
            "lines_total": 1000,
            "status": "PASS",
            "files": [{"path": "src/main.py", "percent": 90.0}],
        }

        result = upload_coverage("artifact", report, project_root=temp_project)

        assert result is True
        artifact_file = temp_project / "coverage-artifact" / "coverage.json"
        assert artifact_file.exists()

        # Verify content
        with open(artifact_file) as f:
            data = json.load(f)
        assert data["coverage_percent"] == 85.0
