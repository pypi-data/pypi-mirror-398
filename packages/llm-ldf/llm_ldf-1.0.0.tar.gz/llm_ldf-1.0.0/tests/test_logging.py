"""Tests for ldf.utils.logging module."""

import logging

from ldf.utils.logging import configure_logging, get_logger


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)

    def test_logger_name_prefixed(self):
        """Test that logger name is prefixed with ldf."""
        logger = get_logger("mymodule")

        assert logger.name == "ldf.mymodule"

    def test_strips_ldf_prefix(self):
        """Test that existing ldf prefix is stripped to avoid duplication."""
        logger = get_logger("ldf.submodule")

        assert logger.name == "ldf.submodule"
        # Should not be ldf.ldf.submodule

    def test_different_loggers_for_different_modules(self):
        """Test that different modules get different loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name != logger2.name


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_verbose_sets_debug_level(self):
        """Test that verbose=True sets DEBUG level."""
        configure_logging(verbose=True)

        root_logger = logging.getLogger("ldf")
        assert root_logger.level == logging.DEBUG

    def test_explicit_level(self):
        """Test setting explicit log level."""
        configure_logging(level="ERROR")

        root_logger = logging.getLogger("ldf")
        assert root_logger.level == logging.ERROR

    def test_info_level(self):
        """Test setting INFO level."""
        configure_logging(level="INFO")

        root_logger = logging.getLogger("ldf")
        assert root_logger.level == logging.INFO

    def test_case_insensitive_level(self):
        """Test that level is case insensitive."""
        configure_logging(level="warning")

        root_logger = logging.getLogger("ldf")
        assert root_logger.level == logging.WARNING

    def test_adds_handler(self):
        """Test that a handler is added to the logger."""
        configure_logging(level="INFO")

        root_logger = logging.getLogger("ldf")
        assert len(root_logger.handlers) > 0


class TestLoggerIntegration:
    """Integration tests for logging."""

    def test_logger_can_log(self, caplog):
        """Test that logger can actually log messages."""
        configure_logging(level="DEBUG")
        logger = get_logger("integration_test")

        with caplog.at_level(logging.DEBUG, logger="ldf"):
            logger.debug("test debug message")
            logger.info("test info message")

        assert "test debug message" in caplog.text
        assert "test info message" in caplog.text

    def test_child_loggers_inherit_level(self):
        """Test that child loggers inherit parent level."""
        configure_logging(level="WARNING")

        _parent = logging.getLogger("ldf")  # noqa: F841 - establishes parent logger
        child = get_logger("child_module")

        assert child.getEffectiveLevel() == logging.WARNING
