"""
Topaz Agent Kit Logger

A wrapper around Python's standard logging module that provides
a consistent interface for logging throughout the Topaz Agent Kit.
Includes colorful console output for better readability.
"""

import logging
import sys
import warnings
from typing import Optional, Union

# Suppress deprecation warnings from external libraries early
# Suppress SWIG-related deprecation warnings (from MCP/C extensions)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*SwigPy.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*swigvarlink.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*builtin type.*has no __module__ attribute.*")
# Suppress websockets.legacy deprecation warnings (from uvicorn)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets.legacy")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets.websockets_impl")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*websockets.legacy.*deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*websockets.server.WebSocketServerProtocol.*deprecated.*")
# Suppress sqlite3 datetime adapter deprecation warnings (Python 3.12+)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*datetime adapter.*deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlite3")

# Register custom log levels
SUCCESS = 25
INPUT = 26
OUTPUT = 27
EVENT = 28
logging.addLevelName(SUCCESS, 'SUCCESS')
logging.addLevelName(INPUT, 'INPUT')
logging.addLevelName(OUTPUT, 'OUTPUT')
logging.addLevelName(EVENT, 'EVENT')

# Try to import colorlog for colorful output, fallback to standard logging if not available
try:
    import colorlog
    COLOR_AVAILABLE = True
except ImportError:
    COLOR_AVAILABLE = False


class Logger:
    """Enhanced logger with structured logging and color support."""
    
    # Class variable to store global log level
    _global_level = logging.INFO
    
    def __init__(self, name: str, level: Optional[Union[str, int]] = None):
        """
        Initialize logger.
        
        Args:
            name: Logger name (usually __name__ or component name)
            level: Optional log level override (inherits global level if not specified)
        """
        # Use global level if no specific level provided
        if level is None:
            level = self._global_level
        
        # Convert string level to int if needed
        if isinstance(level, str):
            level = getattr(logging, level.upper(), self._global_level)
        
        # Create the underlying Python logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        
        # Don't add handlers - let the root logger handle everything
        # This prevents duplication
        self._logger.propagate = True
    
    def _format_message(self, message: str, *args, **kwargs) -> str:
        """
        Format message by converting {} placeholders to %s for standard logging compatibility.
        This maintains backward compatibility with the old logger interface.
        """
        if args or kwargs:
            # Convert {} placeholders to %s for standard logging
            formatted_message = message.replace('{}', '%s')
            try:
                return formatted_message % args
            except (TypeError, ValueError):
                # Fallback to string formatting if % formatting fails
                try:
                    return message.format(*args, **kwargs)
                except Exception:
                    # Last resort: just concatenate
                    return f"{message} {' '.join(str(arg) for arg in args)}"
        return message
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log a debug message."""
        formatted_message = self._format_message(message, *args, **kwargs)
        self._logger.debug(formatted_message)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log an info message."""
        formatted_message = self._format_message(message, *args, **kwargs)
        self._logger.info(formatted_message)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log a warning message."""
        formatted_message = self._format_message(message, *args, **kwargs)
        self._logger.warning(formatted_message)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log an error message."""
        formatted_message = self._format_message(message, *args, **kwargs)
        self._logger.error(formatted_message)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log a critical message."""
        formatted_message = self._format_message(message, *args, **kwargs)
        self._logger.critical(formatted_message)
    
    def success(self, message: str, *args, **kwargs) -> None:
        """Log a success message (custom level with green color)."""
        formatted_message = self._format_message(message, *args, **kwargs)
        # Use custom SUCCESS level for green coloring
        self._logger.log(SUCCESS, formatted_message)
    
    def input(self, message: str, *args, **kwargs) -> None:
        """Log an input message (custom level with yellow color)."""
        formatted_message = self._format_message(message, *args, **kwargs)
        # Use custom INPUT level for yellow coloring
        self._logger.log(INPUT, formatted_message)
    
    def output(self, message: str, *args, **kwargs) -> None:
        """Log an output message (custom level with purple color)."""
        formatted_message = self._format_message(message, *args, **kwargs)
        # Use custom OUTPUT level for purple coloring
        self._logger.log(OUTPUT, formatted_message)
    
    def event(self, message: str, *args, **kwargs) -> None:
        """Log an event message (custom level with green background and white text)."""
        formatted_message = self._format_message(message, *args, **kwargs)
        # Use custom EVENT level for green background with white text
        self._logger.log(EVENT, formatted_message)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        """Log an exception message with traceback."""
        formatted_message = self._format_message(message, *args, **kwargs)
        self._logger.exception(formatted_message)
    
    def log(self, level: int, message: str, *args, **kwargs) -> None:
        """Log a message at the specified level."""
        formatted_message = self._format_message(message, *args, **kwargs)
        self._logger.log(level, formatted_message)
    
    def setLevel(self, level: Union[str, int]) -> None:
        """Set the logging level."""
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        self._logger.setLevel(level)
    
    def getEffectiveLevel(self) -> int:
        """Get the effective logging level."""
        return self._logger.getEffectiveLevel()
    
    def isEnabledFor(self, level: int) -> bool:
        """Check if logging is enabled for the specified level."""
        return self._logger.isEnabledFor(level)
    
    def addHandler(self, handler: logging.Handler) -> None:
        """Add a handler to the logger."""
        self._logger.addHandler(handler)
    
    def removeHandler(self, handler: logging.Handler) -> None:
        """Remove a handler from the logger."""
        self._logger.removeHandler(handler)
    
    def hasHandlers(self) -> bool:
        """Check if the logger has any handlers."""
        return self._logger.hasHandlers()
    
    def propagate(self, propagate: bool) -> None:
        """Set propagation behavior."""
        self._logger.propagate = propagate
    
    def getChild(self, suffix: str) -> 'Logger':
        """Get a child logger."""
        child_logger = self._logger.getChild(suffix)
        return Logger(child_logger.name)
    
    def disable(self, level: int) -> None:
        """Disable logging at the specified level and below."""
        logging.disable(level)
    
    def enable(self, level: int) -> None:
        """Enable logging at the specified level and above."""
        logging.disable(0)
        if level > 0:
            logging.disable(level - 1)
    
    @classmethod
    def set_global_level_from_string(cls, level: str) -> None:
        """
        Set the global logging level from a string.
        
        Args:
            level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        
        # Store the global level so new Logger instances can inherit it
        cls._global_level = level
        
        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Update root logger handlers to use the new level
        for handler in root_logger.handlers:
            handler.setLevel(level)
        
        # Ensure propagation is enabled for all loggers
        for logger_name in logging.root.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            logger.propagate = True


# Set up root logger configuration
def setup_root_logging(level: Union[str, int] = logging.INFO) -> None:
    """
    Set up root logging configuration.
    
    Args:
        level: Root logging level
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Clear any existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    if COLOR_AVAILABLE:
        # Use colorful root logging if colorlog is available
        handler = colorlog.StreamHandler(sys.stdout)
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s[%(asctime)s] [%(name)s] %(levelname)s: %(message)s%(reset)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'purple',  
                'INFO': 'blue',
                'SUCCESS': 'green',  # Custom SUCCESS level
                'INPUT': 'yellow',   # Custom INPUT level
                'OUTPUT': 'purple',  # Custom OUTPUT level
                'EVENT': 'white,bg_green',  # Custom EVENT level - green background with white text
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(level)
        
        # Ensure propagation is enabled for all loggers
        root_logger.propagate = True
    else:
        # Fallback to standard logging
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(level)


# Suppress noisy external library logs
logging.getLogger("google_adk.google.adk.models.registry").setLevel(logging.WARNING)
logging.getLogger("crewai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
# Suppress verbose Azure SDK HTTP logging (request/response bodies, headers)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

# Suppress agent_framework verbose logs (function execution details)
logging.getLogger("agent_framework").setLevel(logging.WARNING)

# Suppress semantic_kernel verbose logs (function execution details, usage info, etc.)
logging.getLogger("semantic_kernel").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel.functions").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel.connectors").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel.kernel").setLevel(logging.WARNING)

# Suppress OpenTelemetry and only let critical errors through
logging.getLogger("opentelemetry").setLevel(logging.ERROR)
logging.getLogger("opentelemetry.trace").setLevel(logging.ERROR)


def remove_opentelemetry_console_handlers() -> None:
    """
    Remove OpenTelemetry console logging handlers that output JSON logs.
    This prevents duplicate/unwanted JSON log output from OpenTelemetry.
    Also ensures JSON filter is applied to all remaining handlers.
    """
    import os
    import sys
    import warnings
    
    # Disable OpenTelemetry console logging via environment variables
    os.environ.setdefault('OTEL_LOG_LEVEL', 'ERROR')
    os.environ.setdefault('OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED', 'false')
    
    # Suppress OpenTelemetry exception tracebacks
    # These are printed directly to stderr when exports fail
    original_excepthook = sys.excepthook
    
    def filtered_excepthook(exc_type, exc_value, exc_traceback):
        """Suppress OpenTelemetry export exception tracebacks"""
        # Check if this is an OpenTelemetry export exception
        if exc_type and exc_traceback:
            tb_file = exc_traceback.tb_frame.f_code.co_filename if exc_traceback.tb_frame else ""
            # Suppress exceptions from OpenTelemetry exporters
            if 'opentelemetry' in tb_file.lower() or 'opentelemetry' in str(exc_type).lower():
                # Only suppress connection errors and export failures
                if 'ConnectionError' in str(exc_type) or 'MaxRetryError' in str(exc_type):
                    return  # Suppress these exceptions
        # For all other exceptions, use the original handler
        original_excepthook(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = filtered_excepthook
    
    # Suppress warnings from OpenTelemetry
    warnings.filterwarnings("ignore", category=Warning, module="opentelemetry.*")
    
    root_logger = logging.getLogger()
    
    # Remove handlers that output JSON (OpenTelemetry uses JSON formatters)
    handlers_to_remove = []
    for handler in root_logger.handlers[:]:
        # Check if handler outputs JSON by examining its formatter
        formatter = handler.formatter
        if formatter:
            # OpenTelemetry handlers often use JSON formatters or have specific class names
            formatter_str = str(type(formatter).__name__).lower()
            handler_str = str(type(handler).__name__).lower()
            
            # Remove handlers that look like OpenTelemetry JSON exporters
            if 'json' in formatter_str or 'otlp' in handler_str or 'opentelemetry' in handler_str:
                handlers_to_remove.append(handler)
        
        # Also check handler class name directly
        handler_class_name = type(handler).__name__
        if 'OTLP' in handler_class_name or 'OpenTelemetry' in handler_class_name:
            handlers_to_remove.append(handler)
        
        # Check handler module path
        handler_module = getattr(type(handler), '__module__', '')
        if 'opentelemetry' in handler_module.lower():
            handlers_to_remove.append(handler)
    
    # Remove identified handlers
    for handler in handlers_to_remove:
        try:
            root_logger.removeHandler(handler)
        except Exception:
            pass
    
    # Also remove handlers from OpenTelemetry loggers and prevent propagation
    for logger_name in ['opentelemetry', 'opentelemetry.sdk', 'opentelemetry.trace', 
                        'opentelemetry.sdk._logs', 'opentelemetry.sdk._logs._internal']:
        otel_logger = logging.getLogger(logger_name)
        for handler in otel_logger.handlers[:]:
            try:
                otel_logger.removeHandler(handler)
            except Exception:
                pass
        # Prevent propagation to avoid duplicate logs
        otel_logger.propagate = False
        otel_logger.setLevel(logging.ERROR)
    
    # Re-apply JSON filter to all remaining root logger handlers
    # This ensures any handlers added after initial setup also get the filter
    json_filter = JSONLogFilter()
    for handler in root_logger.handlers:
        # Check if filter is already applied
        if not any(isinstance(f, JSONLogFilter) for f in handler.filters):
            handler.addFilter(json_filter)


class JSONLogFilter(logging.Filter):
    """
    Filter to prevent JSON-formatted log records from being output.
    This filters out OpenTelemetry JSON logs that bypass standard logging.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        # Check if the log message looks like JSON (starts with { and contains JSON-like structure)
        message = record.getMessage()
        
        # Filter out OpenTelemetry JSON logs
        if message.strip().startswith('{'):
            # Check for OpenTelemetry JSON log structure (logs, metrics, traces)
            json_indicators = [
                '"body"', '"severity_number"', '"severity_text"',
                '"attributes"', '"resource"', '"trace_id"', '"span_id"',
                '"telemetry.sdk.language"', '"telemetry.sdk.name"',
                '"resource_metrics"', '"scope_metrics"', '"data_points"',
                '"gen_ai.client.token.usage"', '"gen_ai.client.operation.duration"',
                '"aggregation_temporality"', '"explicit_bounds"', '"bucket_counts"'
            ]
            if any(indicator in message for indicator in json_indicators):
                return False
        
        # Also filter based on logger name
        if 'opentelemetry' in record.name.lower():
            return False
        
        # Filter out OpenTelemetry exception tracebacks
        if 'Exception while exporting' in message or 'opentelemetry' in message.lower():
            if 'Traceback' in message or 'ConnectionError' in message or 'MaxRetryError' in message:
                return False
            
        return True


# Initialize root logging when module is imported
setup_root_logging()

# Add JSON log filter to root logger handlers
root_logger = logging.getLogger()
json_filter = JSONLogFilter()
for handler in root_logger.handlers:
    handler.addFilter(json_filter)

# Remove OpenTelemetry console handlers
remove_opentelemetry_console_handlers()


# Intercept stdout/stderr to filter OpenTelemetry JSON metrics
class FilteredStream:
    """
    Wrapper around stdout/stderr that filters out OpenTelemetry JSON metrics
    and exception tracebacks that are printed directly (bypassing logging).
    """
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.buffer = ""
        self.suppressing_json = False
        self.suppressing_traceback = False
    
    def write(self, text):
        """Filter out OpenTelemetry JSON metrics and exception tracebacks"""
        if not text:
            return
        
        text_str = str(text)
        text_lower = text_str.lower()
        
        # Check if this starts an OpenTelemetry JSON metrics block
        if '"resource_metrics"' in text_str or '"scope_metrics"' in text_str:
            self.suppressing_json = True
            return
        
        # Check if we're in the middle of suppressing a JSON block
        if self.suppressing_json:
            # Continue suppressing until we see a closing brace on its own line or end of JSON
            if text_str.strip() == '}' or (text_str.strip().endswith('}') and text_str.count('{') == 0):
                self.suppressing_json = False
            return
        
        # Check if this is an OpenTelemetry exception traceback line
        if 'Exception while exporting' in text_str:
            self.suppressing_traceback = True
            return
        
        if self.suppressing_traceback:
            # Suppress traceback lines until we see something that's not part of the traceback
            if text_str.strip() and not any(x in text_str for x in ['Traceback', 'File "', '  File "', '    ', 'opentelemetry', 'ConnectionError', 'MaxRetryError', 'urllib3', 'requests', 'httpcore']):
                self.suppressing_traceback = False
            else:
                return  # Suppress this traceback line
        
        # Write everything else to the original stream
        self.original_stream.write(text)
        self.original_stream.flush()
    
    def flush(self):
        self.original_stream.flush()
    
    def __getattr__(self, name):
        return getattr(self.original_stream, name)


# Wrap stdout and stderr to filter OpenTelemetry JSON output
# Only do this if not already wrapped (to avoid double-wrapping)
# Store original streams for potential restoration
_original_stdout = sys.__stdout__ if not isinstance(sys.stdout, FilteredStream) else None
_original_stderr = sys.__stderr__ if not isinstance(sys.stderr, FilteredStream) else None

if not isinstance(sys.stdout, FilteredStream):
    sys.stdout = FilteredStream(sys.stdout)
if not isinstance(sys.stderr, FilteredStream):
    sys.stderr = FilteredStream(sys.stderr)
