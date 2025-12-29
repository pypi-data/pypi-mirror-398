"""
Specialized MCP (Model Context Protocol) logger using loguru.
Provides structured logging for MCP messages and related operations.
"""

import sys
from loguru import logger
from typing import Optional


class MCPLogger:
    """
    Specialized logger for MCP (Model Context Protocol) operations.
    Uses loguru for structured, configurable logging.
    """
    
    def __init__(self, level: str = "INFO", sink=None):
        """
        Initialize the MCP Logger.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, TRACE)
            sink: Output destination (default: sys.stdout). Use StringIO for testing.
        """
        # Remove default logger configuration
        logger.remove()

        # Add custom configuration for MCP logs
        if sink is None:
            sink = sys.stdout

        logger.add(
            sink,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
            level=level,
            colorize=True
        )

        self._logger = logger
    
    @property
    def logger(self):
        """Return the underlying loguru logger instance."""
        return self._logger
    
    def log_request(self, method: str, params: dict, client_info: Optional[str] = None):
        """
        Log an incoming MCP request.
        
        Args:
            method: The MCP method name
            params: Request parameters
            client_info: Information about the client making the request
        """
        client_str = f" from {client_info}" if client_info else ""
        self._logger.info(f"MCP REQUEST: {method}{client_str} | Params: {params}")
    
    def log_response(self, method: str, response: dict, client_info: Optional[str] = None):
        """
        Log an outgoing MCP response.
        
        Args:
            method: The MCP method name
            response: Response data
            client_info: Information about the client receiving the response
        """
        client_str = f" to {client_info}" if client_info else ""
        self._logger.info(f"MCP RESPONSE: {method}{client_str} | Response: {response}")
    
    def log_error(self, method: str, error: Exception, client_info: Optional[str] = None):
        """
        Log an MCP error.
        
        Args:
            method: The MCP method name
            error: The exception that occurred
            client_info: Information about the client involved
        """
        client_str = f" for {client_info}" if client_info else ""
        self._logger.error(f"MCP ERROR: {method}{client_str} | Error: {str(error)} | Type: {type(error).__name__}")
    
    def debug_mcp(self, message: str, **kwargs):
        """
        Log a debug message related to MCP operations.
        
        Args:
            message: Debug message
            **kwargs: Additional context data
        """
        if kwargs:
            self._logger.debug(f"MCP DEBUG: {message} | Context: {kwargs}")
        else:
            self._logger.debug(f"MCP DEBUG: {message}")
    
    def info_mcp(self, message: str, **kwargs):
        """
        Log an info message related to MCP operations.
        
        Args:
            message: Info message
            **kwargs: Additional context data
        """
        if kwargs:
            self._logger.info(f"MCP INFO: {message} | Context: {kwargs}")
        else:
            self._logger.info(f"MCP INFO: {message}")
    
    def warning_mcp(self, message: str, **kwargs):
        """
        Log a warning message related to MCP operations.
        
        Args:
            message: Warning message
            **kwargs: Additional context data
        """
        if kwargs:
            self._logger.warning(f"MCP WARNING: {message} | Context: {kwargs}")
        else:
            self._logger.warning(f"MCP WARNING: {message}")


# Global instance of MCPLogger
mcp_logger = MCPLogger()

# Convenience functions that use the global logger instance
def log_request(method: str, params: dict, client_info: Optional[str] = None):
    mcp_logger.log_request(method, params, client_info)

def log_response(method: str, response: dict, client_info: Optional[str] = None):
    mcp_logger.log_response(method, response, client_info)

def log_error(method: str, error: Exception, client_info: Optional[str] = None):
    mcp_logger.log_error(method, error, client_info)

def debug_mcp(message: str, **kwargs):
    mcp_logger.debug_mcp(message, **kwargs)

def info_mcp(message: str, **kwargs):
    mcp_logger.info_mcp(message, **kwargs)

def warning_mcp(message: str, **kwargs):
    mcp_logger.warning_mcp(message, **kwargs)


__all__ = [
    'MCPLogger',
    'mcp_logger',
    'log_request',
    'log_response',
    'log_error',
    'debug_mcp',
    'info_mcp',
    'warning_mcp'
]