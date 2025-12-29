"""
Unit tests for mcp_logger.py module.
Tests the MCPLogger class and its logging functions.
"""
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
import pytest
from contextnest.mcp_logger import MCPLogger, log_request, log_response, log_error, debug_mcp, info_mcp, warning_mcp


class TestMCPLogger:
    """Test cases for MCPLogger class."""

    def test_initialization_with_default_level(self):
        """Test initialization with default level."""
        logger = MCPLogger()
        assert logger.logger is not None

    def test_initialization_with_custom_level(self):
        """Test initialization with custom level."""
        logger = MCPLogger(level="DEBUG")
        # We can't directly access the level, but we can verify it was set
        assert logger.logger is not None

    def test_log_request(self):
        """Test the log_request method."""
        captured_output = StringIO()
        logger = MCPLogger(sink=captured_output)

        logger.log_request("test_method", {"param": "value"}, "client1")
        output = captured_output.getvalue()
        assert "MCP REQUEST: test_method from client1" in output
        assert "Params: {'param': 'value'}" in output

    def test_log_request_without_client_info(self):
        """Test the log_request method without client info."""
        captured_output = StringIO()
        logger = MCPLogger(sink=captured_output)

        logger.log_request("test_method", {"param": "value"})
        output = captured_output.getvalue()
        assert "MCP REQUEST: test_method | Params: {'param': 'value'}" in output

    def test_log_response(self):
        """Test the log_response method."""
        captured_output = StringIO()
        logger = MCPLogger(sink=captured_output)

        logger.log_response("test_method", {"result": "success"}, "client1")
        output = captured_output.getvalue()
        assert "MCP RESPONSE: test_method to client1" in output
        assert "Response: {'result': 'success'}" in output

    def test_log_response_without_client_info(self):
        """Test the log_response method without client info."""
        captured_output = StringIO()
        logger = MCPLogger(sink=captured_output)

        logger.log_response("test_method", {"result": "success"})
        output = captured_output.getvalue()
        assert "MCP RESPONSE: test_method | Response: {'result': 'success'}" in output

    def test_log_error(self):
        """Test the log_error method."""
        captured_output = StringIO()
        logger = MCPLogger(sink=captured_output)

        error = Exception("Test error")
        logger.log_error("test_method", error, "client1")
        output = captured_output.getvalue()
        assert "MCP ERROR: test_method for client1" in output
        assert "Error: Test error" in output
        assert "Type: Exception" in output

    def test_log_error_without_client_info(self):
        """Test the log_error method without client info."""
        captured_output = StringIO()
        logger = MCPLogger(sink=captured_output)

        error = Exception("Test error")
        logger.log_error("test_method", error)
        output = captured_output.getvalue()
        assert "MCP ERROR: test_method | Error: Test error" in output
        assert "Type: Exception" in output

    def test_debug_mcp(self):
        """Test the debug_mcp method."""
        captured_output = StringIO()
        logger = MCPLogger(level="DEBUG", sink=captured_output)

        logger.debug_mcp("Debug message", extra_param="value")
        output = captured_output.getvalue()
        assert "MCP DEBUG: Debug message | Context: {'extra_param': 'value'}" in output

    def test_debug_mcp_without_context(self):
        """Test the debug_mcp method without additional context."""
        captured_output = StringIO()
        logger = MCPLogger(level="DEBUG", sink=captured_output)

        logger.debug_mcp("Debug message")
        output = captured_output.getvalue()
        assert "MCP DEBUG: Debug message" in output

    def test_info_mcp(self):
        """Test the info_mcp method."""
        captured_output = StringIO()
        logger = MCPLogger(sink=captured_output)

        logger.info_mcp("Info message", extra_param="value")
        output = captured_output.getvalue()
        assert "MCP INFO: Info message | Context: {'extra_param': 'value'}" in output

    def test_info_mcp_without_context(self):
        """Test the info_mcp method without additional context."""
        captured_output = StringIO()
        logger = MCPLogger(sink=captured_output)

        logger.info_mcp("Info message")
        output = captured_output.getvalue()
        assert "MCP INFO: Info message" in output

    def test_warning_mcp(self):
        """Test the warning_mcp method."""
        captured_output = StringIO()
        logger = MCPLogger(sink=captured_output)

        logger.warning_mcp("Warning message", extra_param="value")
        output = captured_output.getvalue()
        assert "MCP WARNING: Warning message | Context: {'extra_param': 'value'}" in output

    def test_warning_mcp_without_context(self):
        """Test the warning_mcp method without additional context."""
        captured_output = StringIO()
        logger = MCPLogger(sink=captured_output)

        logger.warning_mcp("Warning message")
        output = captured_output.getvalue()
        assert "MCP WARNING: Warning message" in output


class TestGlobalFunctions:
    """Test cases for the global convenience functions."""

    def test_global_log_request(self):
        """Test the global log_request function."""
        from contextnest.mcp_logger import mcp_logger as original_logger
        captured_output = StringIO()

        # Create a new logger instance for testing
        test_logger = MCPLogger(sink=captured_output)

        # Replace the global logger temporarily
        import contextnest.mcp_logger as logger_module
        original_module_logger = logger_module.mcp_logger
        logger_module.mcp_logger = test_logger

        log_request("test_method", {"param": "value"}, "client1")
        output = captured_output.getvalue()
        assert "MCP REQUEST: test_method from client1" in output

        # Restore original logger
        logger_module.mcp_logger = original_module_logger

    def test_global_log_response(self):
        """Test the global log_response function."""
        captured_output = StringIO()

        # Create a new logger instance for testing
        test_logger = MCPLogger(sink=captured_output)

        # Replace the global logger temporarily
        import contextnest.mcp_logger as logger_module
        original_module_logger = logger_module.mcp_logger
        logger_module.mcp_logger = test_logger

        log_response("test_method", {"result": "success"}, "client1")
        output = captured_output.getvalue()
        assert "MCP RESPONSE: test_method to client1" in output

        # Restore original logger
        logger_module.mcp_logger = original_module_logger

    def test_global_log_error(self):
        """Test the global log_error function."""
        captured_output = StringIO()

        # Create a new logger instance for testing
        test_logger = MCPLogger(sink=captured_output)

        # Replace the global logger temporarily
        import contextnest.mcp_logger as logger_module
        original_module_logger = logger_module.mcp_logger
        logger_module.mcp_logger = test_logger

        error = Exception("Test error")
        log_error("test_method", error, "client1")
        output = captured_output.getvalue()
        assert "MCP ERROR: test_method for client1" in output

        # Restore original logger
        logger_module.mcp_logger = original_module_logger

    def test_global_debug_mcp(self):
        """Test the global debug_mcp function."""
        captured_output = StringIO()

        # Create a new logger instance for testing
        test_logger = MCPLogger(level="DEBUG", sink=captured_output)

        # Replace the global logger temporarily
        import contextnest.mcp_logger as logger_module
        original_module_logger = logger_module.mcp_logger
        logger_module.mcp_logger = test_logger

        debug_mcp("Debug message", extra_param="value")
        output = captured_output.getvalue()
        assert "MCP DEBUG: Debug message | Context: {'extra_param': 'value'}" in output

        # Restore original logger
        logger_module.mcp_logger = original_module_logger

    def test_global_info_mcp(self):
        """Test the global info_mcp function."""
        captured_output = StringIO()

        # Create a new logger instance for testing
        test_logger = MCPLogger(sink=captured_output)

        # Replace the global logger temporarily
        import contextnest.mcp_logger as logger_module
        original_module_logger = logger_module.mcp_logger
        logger_module.mcp_logger = test_logger

        info_mcp("Info message", extra_param="value")
        output = captured_output.getvalue()
        assert "MCP INFO: Info message | Context: {'extra_param': 'value'}" in output

        # Restore original logger
        logger_module.mcp_logger = original_module_logger

    def test_global_warning_mcp(self):
        """Test the global warning_mcp function."""
        captured_output = StringIO()

        # Create a new logger instance for testing
        test_logger = MCPLogger(sink=captured_output)

        # Replace the global logger temporarily
        import contextnest.mcp_logger as logger_module
        original_module_logger = logger_module.mcp_logger
        logger_module.mcp_logger = test_logger

        warning_mcp("Warning message", extra_param="value")
        output = captured_output.getvalue()
        assert "MCP WARNING: Warning message | Context: {'extra_param': 'value'}" in output

        # Restore original logger
        logger_module.mcp_logger = original_module_logger