"""Tests for pipeline logger module."""

import json
from pathlib import Path

from app.logger import PipelineReport


class TestPipelineLogger:
    """Test PipelineLogger class."""

    def test_init_creates_log_dir(self, pipeline_logger):
        """PipelineLogger creates log directory."""
        assert pipeline_logger.log_dir.exists()

    def test_log_dir_is_pathlib_path(self, pipeline_logger):
        """Log directory should be Path object."""
        assert isinstance(pipeline_logger.log_dir, Path)

    def test_logger_name(self, pipeline_logger):
        """Logger should have correct name."""
        assert pipeline_logger.logger.name == "creative_pipeline"

    def test_info_log(self, pipeline_logger):
        """Log info message."""
        pipeline_logger.info("Test info message")
        # Should not raise exception

    def test_warning_log(self, pipeline_logger):
        """Log warning message."""
        pipeline_logger.warning("Test warning message")
        # Should not raise exception

    def test_error_log(self, pipeline_logger):
        """Log error message."""
        pipeline_logger.error("Test error message")
        # Should not raise exception

    def test_debug_log(self, pipeline_logger):
        """Log debug message."""
        pipeline_logger.debug("Test debug message")
        # Should not raise exception


class TestPipelineReport:
    """Test PipelineReport class."""

    def test_init(self, temp_dir):
        """Initialize PipelineReport."""
        report = PipelineReport(output_dir=str(temp_dir))

        assert report.output_dir.exists()
        assert isinstance(report.results, dict)

    def test_output_dir_creation(self, temp_dir):
        """PipelineReport creates output directory."""
        output_path = temp_dir / "report_test"
        PipelineReport(output_dir=str(output_path))

        assert output_path.exists()

    def test_start_time_recorded(self, temp_dir):
        """Report should record start time."""
        report = PipelineReport(output_dir=str(temp_dir))

        assert "timestamp" in report.results
        assert report.results["status"] == "in_progress"

    def test_finalize_report_creates_file(self, temp_dir):
        """Finalize report creates JSON and HTML files."""
        report = PipelineReport(output_dir=str(temp_dir))

        json_path, html_path = report.finalize("completed")

        assert Path(json_path).exists()
        assert str(json_path).endswith(".json")
        assert Path(html_path).exists()
        assert str(html_path).endswith(".html")

    def test_finalize_report_valid_json(self, temp_dir):
        """Finalized report should be valid JSON."""
        report = PipelineReport(output_dir=str(temp_dir))

        json_path, _ = report.finalize("completed")

        with open(json_path) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert "timestamp" in data


class TestPipelineReportStructure:
    """Test PipelineReport data structure."""

    def test_results_dict_structure(self, temp_dir):
        """Results dict should have expected structure."""
        report = PipelineReport(output_dir=str(temp_dir))

        assert "timestamp" in report.results
        assert "status" in report.results
        assert "products" in report.results

    def test_results_default_status(self, temp_dir):
        """Default status should be 'in_progress'."""
        report = PipelineReport(output_dir=str(temp_dir))

        assert report.results["status"] == "in_progress"

    def test_products_tracking(self, temp_dir):
        """Products should be trackable."""
        report = PipelineReport(output_dir=str(temp_dir))

        assert isinstance(report.results["products"], dict)
