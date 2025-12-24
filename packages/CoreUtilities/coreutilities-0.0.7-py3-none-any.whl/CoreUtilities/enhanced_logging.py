"""
Comprehensive Logging Package

This module provides advanced logging capabilities including:
- Configurable log levels and message formatting
- Timestamp management with timezone support
- Performance metric tracking and profiling
- Automatic traceback capture for errors
- Error handling and exception wrapping
- Context managers for performance tracking
- Structured logging with metadata
- Multiple output destinations (file, console, custom handlers)

Author: Ruppert20
"""

import logging
import sys
import time
import traceback
import functools
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, TextIO, Type, Tuple, Iterator, Iterable
from contextlib import contextmanager
from enum import Enum
import json
import inspect

# Optional tqdm support
try:
    from tqdm import tqdm # type: ignore
    from tqdm.auto import tqdm as tqdm_auto # type: ignore
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    # Create dummy tqdm for when not available
    class tqdm:
        def __init__(self, iterable=None, **kwargs):
            self.iterable = iterable or []
            self.kwargs = kwargs
        def __iter__(self):
            return iter(self.iterable)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def update(self, n=1):
            pass
        def set_description(self, desc=None):
            pass
        def set_postfix(self, **kwargs):
            pass
        def close(self):
            pass


class LogLevel(Enum):
    """Extended log levels with performance and metrics support."""
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    TRACE = 5
    PERFORMANCE = 15
    METRICS = 25
    
    def __str__(self) -> str:
        return self.name
    
    @property
    def standard_level(self) -> int:
        """Map custom levels to standard logging levels."""
        mapping = {
            LogLevel.TRACE: logging.DEBUG,
            LogLevel.PERFORMANCE: logging.INFO,
            LogLevel.METRICS: logging.INFO
        }
        return mapping.get(self, self.value)


class PerformanceMetrics:
    """Performance metrics tracking and reporting."""
    
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def start_timer(self, operation: str) -> float:
        """Start timing an operation."""
        start_time = time.perf_counter()
        with self._lock:
            if operation not in self.metrics:
                self.metrics[operation] = {
                    'count': 0,
                    'total_time': 0.0,
                    'min_time': float('inf'),
                    'max_time': 0.0,
                    'start_times': {}
                }
            self.metrics[operation]['start_times'][threading.get_ident()] = start_time
        return start_time
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and record metrics."""
        end_time = time.perf_counter()
        thread_id = threading.get_ident()
        
        with self._lock:
            if operation not in self.metrics:
                return 0.0
            
            start_times = self.metrics[operation]['start_times']
            if thread_id not in start_times:
                return 0.0
            
            start_time = start_times.pop(thread_id)
            duration = end_time - start_time
            
            metrics = self.metrics[operation]
            metrics['count'] += 1
            metrics['total_time'] += duration
            metrics['min_time'] = min(metrics['min_time'], duration)
            metrics['max_time'] = max(metrics['max_time'], duration)
            
            return duration
    
    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for an operation or all operations."""
        with self._lock:
            if operation:
                return self.metrics.get(operation, {}).copy()
            
            result = {}
            for op, metrics in self.metrics.items():
                clean_metrics = metrics.copy()
                clean_metrics.pop('start_times', None)  # Remove internal state
                if clean_metrics['count'] > 0:
                    clean_metrics['avg_time'] = clean_metrics['total_time'] / clean_metrics['count']
                else:
                    clean_metrics['avg_time'] = 0.0
                result[op] = clean_metrics
            return result
    
    def reset(self, operation: Optional[str] = None):
        """Reset metrics for an operation or all operations."""
        with self._lock:
            if operation:
                if operation in self.metrics:
                    del self.metrics[operation]
            else:
                self.metrics.clear()


class LogFormatter(logging.Formatter):
    """Enhanced formatter with performance metrics, structured data support, and emoji formatting."""
    
    def __init__(self, 
                 include_performance: bool = True,
                 include_thread_id: bool = False,
                 structured: bool = False,
                 include_emoji: bool = True,
                 emoji_position: str = 'prefix'):  # 'prefix', 'suffix', or 'none'
        self.include_performance = include_performance
        self.include_thread_id = include_thread_id
        self.structured = structured
        self.include_emoji = include_emoji
        self.emoji_position = emoji_position
        
        if structured:
            super().__init__()
        else:
            format_parts = [
                '%(asctime)s',
                '%(levelname)-8s',
                '%(name)s'
            ]
            
            if include_thread_id:
                format_parts.append('[%(thread)d]')
            
            format_parts.extend([
                '%(funcName)s:%(lineno)d',
                '%(message)s'
            ])
            
            format_string = ' | '.join(format_parts)
            super().__init__(format_string, datefmt='%Y-%m-%d %H:%M:%S.%f %Z')
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with enhanced information."""
        # Add timezone info if not present
        if not hasattr(record, 'created_tz'):
            record.created_tz = datetime.now(timezone.utc).isoformat()
        
        # Handle emoji formatting
        if self.include_emoji and hasattr(record, 'emoji'):
            emoji = getattr(record, 'emoji', '')
            if emoji and self.emoji_position == 'prefix':
                original_msg = record.getMessage()
                record.msg = f"{emoji} {original_msg}"
            elif emoji and self.emoji_position == 'suffix':
                original_msg = record.getMessage()
                record.msg = f"{original_msg} {emoji}"
        
        # Add performance info if available
        if self.include_performance and hasattr(record, 'duration'):
            if not self.structured:
                # Only modify the message if it doesn't already contain timing info
                original_msg = record.getMessage()
                duration_val = getattr(record, 'duration', 0.0)
                if "[took " not in original_msg:
                    record.msg = f"{original_msg} [took {duration_val:.4f}s]"
        
        if self.structured:
            return self._format_structured(record)
        else:
            return super().format(record)
    
    def _format_structured(self, record: logging.LogRecord) -> str:
        """Format as structured JSON log."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        if self.include_thread_id:
            log_entry['thread_id'] = record.thread
        
        if hasattr(record, 'duration'):
            log_entry['duration'] = getattr(record, 'duration')
        
        if hasattr(record, 'metadata'):
            log_entry['metadata'] = getattr(record, 'metadata')
        
        if hasattr(record, 'emoji'):
            log_entry['emoji'] = getattr(record, 'emoji')
        
        if hasattr(record, 'exc_info') and record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info) if record.exc_info[0] else None
            }
        
        return json.dumps(log_entry, default=str)


class EnhancedLogger:
    """Enhanced logger with performance tracking, error handling, and emoji support."""
    
    def __init__(self, 
                 name: str,
                 level: Union[LogLevel, int, str] = LogLevel.INFO,
                 console_output: bool = True,
                 file_output: Optional[Union[str, Path]] = None,
                 structured_logging: bool = False,
                 include_performance: bool = True,
                 include_thread_id: bool = False,
                 include_emoji: bool = True,
                 emoji_position: str = 'prefix',
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        
        self.name = name
        self.performance_metrics = PerformanceMetrics()
        self.structured_logging = structured_logging
        self.include_performance = include_performance
        self.include_emoji = include_emoji
        self.emoji_position = emoji_position
        
        # Default emoji mappings for different log levels
        self.level_emojis = {
            logging.DEBUG: '🔍',
            logging.INFO: 'ℹ️',
            logging.WARNING: '⚠️',
            logging.ERROR: '❌',
            logging.CRITICAL: '🚨',
            LogLevel.TRACE.standard_level: '🔬',
            LogLevel.PERFORMANCE.standard_level: '⚡',
            LogLevel.METRICS.standard_level: '📊'
        }
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._convert_level(level))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup formatter
        formatter = LogFormatter(
            include_performance=include_performance,
            include_thread_id=include_thread_id,
            structured=structured_logging,
            include_emoji=include_emoji,
            emoji_position=emoji_position
        )
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if file_output:
            from logging.handlers import RotatingFileHandler
            file_path = Path(file_output)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=max_file_size,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _convert_level(self, level: Union[LogLevel, int, str]) -> int:
        """Convert various level formats to logging level."""
        if isinstance(level, LogLevel):
            return level.standard_level
        elif isinstance(level, str):
            try:
                return getattr(logging, level.upper())
            except AttributeError:
                return logging.INFO
        else:
            return level
    
    def _log_with_context(self, 
                         level: int, 
                         message: str, 
                         *args, 
                         duration: Optional[float] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         exc_info: Optional[tuple] = None,
                         emoji: Optional[str] = None,
                         **kwargs):
        """Internal logging method with context information."""
        extra = kwargs.copy()
        
        if duration is not None:
            extra['duration'] = duration
        
        if metadata:
            extra['metadata'] = metadata
        
        # Handle emoji - use custom emoji or default for log level
        if self.include_emoji:
            if emoji:
                extra['emoji'] = emoji
            elif level in self.level_emojis:
                extra['emoji'] = self.level_emojis[level]
        
        # Handle exc_info separately as it's a special parameter for logging
        self.logger.log(level, message, *args, exc_info=exc_info, extra=extra)
    
    # Standard logging methods
    def debug(self, message: str, *args, metadata: Optional[Dict[str, Any]] = None, emoji: Optional[str] = None, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, *args, metadata=metadata, emoji=emoji, **kwargs)
    
    def info(self, message: str, *args, metadata: Optional[Dict[str, Any]] = None, emoji: Optional[str] = None, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, *args, metadata=metadata, emoji=emoji, **kwargs)
    
    def warning(self, message: str, *args, metadata: Optional[Dict[str, Any]] = None, emoji: Optional[str] = None, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, *args, metadata=metadata, emoji=emoji, **kwargs)
    
    def error(self, message: str, *args, 
              metadata: Optional[Dict[str, Any]] = None, 
              capture_exception: bool = True,
              emoji: Optional[str] = None,
              **kwargs):
        """Log error message with optional exception capture."""
        exc_info = sys.exc_info() if capture_exception and sys.exc_info()[0] else None
        self._log_with_context(logging.ERROR, message, *args, 
                             metadata=metadata, exc_info=exc_info, emoji=emoji, **kwargs)
    
    def critical(self, message: str, *args, 
                 metadata: Optional[Dict[str, Any]] = None, 
                 capture_exception: bool = True,
                 emoji: Optional[str] = None,
                 **kwargs):
        """Log critical message with optional exception capture."""
        exc_info = sys.exc_info() if capture_exception and sys.exc_info()[0] else None
        self._log_with_context(logging.CRITICAL, message, *args, 
                             metadata=metadata, exc_info=exc_info, emoji=emoji, **kwargs)
    
    def exception(self, message: str, *args, metadata: Optional[Dict[str, Any]] = None, emoji: Optional[str] = None, **kwargs):
        """Log exception with full traceback."""
        exc_info = sys.exc_info()
        self._log_with_context(logging.ERROR, message, *args, 
                             metadata=metadata, exc_info=exc_info, emoji=emoji, **kwargs)
    
    def trace(self, message: str, *args, metadata: Optional[Dict[str, Any]] = None, emoji: Optional[str] = None, **kwargs):
        """Log trace message (more detailed than debug)."""
        self._log_with_context(LogLevel.TRACE.standard_level, message, *args, 
                             metadata=metadata, emoji=emoji, **kwargs)
    
    def performance(self, message: str, duration: float, 
                   operation: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None,
                   emoji: Optional[str] = None,
                   **kwargs):
        """Log performance message with timing information."""
        perf_metadata = metadata or {}
        perf_metadata.update({
            'operation': operation,
            'duration_ms': duration * 1000
        })
        
        self._log_with_context(LogLevel.PERFORMANCE.standard_level, 
                             message, duration=duration, metadata=perf_metadata, emoji=emoji, **kwargs)
    
    def metrics(self, message: str, metrics_data: Dict[str, Any], emoji: Optional[str] = None, **kwargs):
        """Log metrics information."""
        self._log_with_context(LogLevel.METRICS.standard_level, 
                             message, metadata=metrics_data, emoji=emoji, **kwargs)
    
    # Emoji customization methods
    def set_level_emoji(self, level: Union[LogLevel, int], emoji: str):
        """Set custom emoji for a specific log level."""
        if isinstance(level, LogLevel):
            level = level.standard_level
        self.level_emojis[level] = emoji
    
    def get_level_emoji(self, level: Union[LogLevel, int]) -> Optional[str]:
        """Get emoji for a specific log level."""
        if isinstance(level, LogLevel):
            level = level.standard_level
        return self.level_emojis.get(level)
    
    def disable_emoji(self):
        """Disable emoji output for this logger."""
        self.include_emoji = False
    
    def enable_emoji(self, position: str = 'prefix'):
        """Enable emoji output for this logger."""
        self.include_emoji = True
        self.emoji_position = position
    
    # Level management methods
    def set_level(self, level: Union[LogLevel, int, str]) -> None:
        """
        Set the logging level for this logger.
        
        Args:
            level: The logging level to set. Can be:
                - LogLevel enum value (LogLevel.DEBUG, LogLevel.INFO, etc.)
                - Standard logging level integer (logging.DEBUG, logging.INFO, etc.)
                - String level name ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        
        Examples:
            >>> logger.set_level('DEBUG')
            >>> logger.set_level(logging.WARNING)
            >>> logger.set_level(LogLevel.ERROR)
        """
        converted_level = self._convert_level(level)
        self.logger.setLevel(converted_level)
    
    def get_level(self) -> int:
        """
        Get the current logging level.
        
        Returns:
            Current logging level as integer
        """
        return self.logger.level
    
    def get_level_name(self) -> str:
        """
        Get the current logging level as a string name.
        
        Returns:
            Current logging level name (e.g., 'DEBUG', 'INFO', etc.)
        """
        return logging.getLevelName(self.logger.level)
    
    # Performance tracking methods
    @contextmanager
    def timer(self, operation: str, log_result: bool = True):
        """Context manager for timing operations."""
        start_time = self.performance_metrics.start_timer(operation)
        try:
            yield
        finally:
            duration = self.performance_metrics.end_timer(operation)
            if log_result and duration > 0:
                self.performance(f"Completed operation: {operation}", duration, operation)
    
    def time_function(self, func: Optional[Callable] = None, *, operation: Optional[str] = None):
        """Decorator for timing function execution."""
        def decorator(f: Callable) -> Callable:
            op_name = operation or f"{f.__module__}.{f.__name__}"
            
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                with self.timer(op_name):
                    return f(*args, **kwargs)
            return wrapper
        
        if func is None:
            return decorator
        else:
            return decorator(func)
    
    def get_performance_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.performance_metrics.get_metrics(operation)
    
    def reset_performance_metrics(self, operation: Optional[str] = None):
        """Reset performance metrics."""
        self.performance_metrics.reset(operation)
    
    # Error handling and wrapping
    def wrap_exceptions(self, 
                       exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
                       message: Optional[str] = None,
                       reraise: bool = True,
                       log_level: int = logging.ERROR):
        """Decorator for wrapping and logging exceptions."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    error_msg = message or f"Exception in {func.__name__}: {str(e)}"
                    self._log_with_context(log_level, error_msg, 
                                         exc_info=sys.exc_info(),
                                         metadata={'function': func.__name__, 'args_count': len(args), 'kwargs_keys': list(kwargs.keys())})
                    if reraise:
                        raise
                    return None
            return wrapper
        return decorator
    
    def safe_execute(self, 
                    func: Callable, 
                    *args, 
                    default: Any = None,
                    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
                    log_errors: bool = True,
                    **kwargs) -> Any:
        """Safely execute a function with error handling."""
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            if log_errors:
                self.error(f"Error executing {func.__name__}: {str(e)}", 
                         metadata={'function': func.__name__, 'exception_type': type(e).__name__})
            return default
    
    # Progress tracking methods using tqdm
    def progress_iter(self, 
                     iterable: Iterable,
                     desc: Optional[str] = None,
                     total: Optional[int] = None,
                     disable: bool = False,
                     unit: str = 'it',
                     unit_scale: bool = False,
                     ncols: Optional[int] = None,
                     leave: bool = True,
                     log_completion: bool = True,
                     auto_desc: bool = True,
                     **tqdm_kwargs) -> Iterator:
        """
        Create a progress bar for iterables with automatic logging.
        
        Args:
            iterable: The iterable to wrap
            desc: Description for the progress bar (auto-extracted if None and auto_desc=True)
            total: Total number of items (auto-detected if None)
            disable: Disable the progress bar display
            unit: Unit of measurement
            unit_scale: Scale the unit
            ncols: Progress bar width
            leave: Leave progress bar after completion
            log_completion: Log completion message
            auto_desc: Auto-extract description from calling function
            **tqdm_kwargs: Additional tqdm arguments
        """
        # Auto-extract description from calling function if requested
        if desc is None and auto_desc:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_name = frame.f_back.f_code.co_name
                caller_locals = frame.f_back.f_locals
                
                # Try to get a meaningful description
                if caller_name != '<module>':
                    desc = f"Processing in {caller_name}"
                else:
                    desc = "Processing items"
                
                # Check if there's a docstring or variable name we can use
                if 'self' in caller_locals:
                    obj = caller_locals['self']
                    if hasattr(obj, '__class__'):
                        desc = f"Processing in {obj.__class__.__name__}.{caller_name}"
        
        desc = desc or "Processing"
        
        # Prepare tqdm arguments
        tqdm_args = {
            'desc': desc,
            'total': total,
            'disable': disable or not TQDM_AVAILABLE,
            'unit': unit,
            'unit_scale': unit_scale,
            'ncols': ncols,
            'leave': leave,
            **tqdm_kwargs
        }
        
        start_time = time.perf_counter()
        processed_count = 0
        
        try:
            with tqdm(iterable, **tqdm_args) as pbar:
                for item in pbar:
                    processed_count += 1
                    yield item
                    
            if log_completion:
                end_time = time.perf_counter()
                duration = end_time - start_time
                self.info(f"Completed processing {processed_count} items", 
                         duration=duration,
                         metadata={
                             'operation': desc,
                             'items_processed': processed_count,
                             'rate': processed_count / duration if duration > 0 else 0
                         },
                         emoji="✅")
                         
        except Exception as e:
            end_time = time.perf_counter()
            duration = end_time - start_time
            self.error(f"Error during processing: {str(e)}", 
                      metadata={
                          'operation': desc,
                          'items_processed': processed_count,
                          'duration': duration
                      },
                      emoji="❌")
            raise
    
    def progress_wrapper(self, 
                        desc: Optional[str] = None,
                        disable: bool = False,
                        log_completion: bool = True,
                        auto_desc: bool = True,
                        **tqdm_kwargs):
        """
        Decorator to add progress tracking to functions that work with iterables.
        
        Args:
            desc: Description for the progress bar
            disable: Disable progress bar display
            log_completion: Log completion message
            auto_desc: Auto-extract description from function
            **tqdm_kwargs: Additional tqdm arguments
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract description if needed
                operation_desc = desc
                if operation_desc is None and auto_desc:
                    operation_desc = f"Executing {func.__name__}"
                    if func.__doc__:
                        # Use first line of docstring if available
                        first_line = func.__doc__.strip().split('\n')[0]
                        if len(first_line) < 80:  # Reasonable length
                            operation_desc = first_line
                
                # Check if any args are iterables that we should track
                iterable_args = []
                for i, arg in enumerate(args):
                    if hasattr(arg, '__iter__') and not isinstance(arg, (str, bytes, dict)):
                        try:
                            # Try to get length for progress tracking
                            total = len(arg) if hasattr(arg, '__len__') else None
                            iterable_args.append((i, arg, total))
                        except (TypeError, AttributeError):
                            continue
                
                # If we found iterables, wrap the function execution
                if iterable_args and not disable:
                    start_time = time.perf_counter()
                    try:
                        result = func(*args, **kwargs)
                        if log_completion:
                            end_time = time.perf_counter()
                            duration = end_time - start_time
                            self.info(f"Completed {operation_desc}", 
                                     duration=duration,
                                     metadata={'operation': func.__name__},
                                     emoji="✅")
                        return result
                    except Exception as e:
                        end_time = time.perf_counter()
                        duration = end_time - start_time
                        self.error(f"Error in {operation_desc}: {str(e)}", 
                                  metadata={
                                      'operation': func.__name__,
                                      'duration': duration
                                  },
                                  emoji="❌")
                        raise
                else:
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def progress_context(self, 
                        total: int,
                        desc: Optional[str] = None,
                        disable: bool = False,
                        auto_desc: bool = True,
                        **tqdm_kwargs):
        """
        Context manager for manual progress tracking.
        
        Args:
            total: Total number of items to process
            desc: Description for the progress bar
            disable: Disable progress bar display  
            auto_desc: Auto-extract description from calling context
            **tqdm_kwargs: Additional tqdm arguments
        """
        # Auto-extract description from calling function if requested
        if desc is None and auto_desc:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_name = frame.f_back.f_code.co_name
                if caller_name != '<module>':
                    desc = f"Processing in {caller_name}"
                else:
                    desc = "Manual processing"
        
        desc = desc or "Processing"
        
        return ProgressContext(
            logger=self,
            total=total,
            desc=desc,
            disable=disable or not TQDM_AVAILABLE,
            **tqdm_kwargs
        )


class ProgressContext:
    """Context manager for manual progress tracking with logging integration."""
    
    def __init__(self, 
                 logger: EnhancedLogger,
                 total: int,
                 desc: str = "Processing",
                 disable: bool = False,
                 **tqdm_kwargs):
        self.logger = logger
        self.total = total
        self.desc = desc
        self.disable = disable
        self.tqdm_kwargs = tqdm_kwargs
        self.pbar = None
        self.start_time = None
        self.processed_count = 0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        if not self.disable:
            self.pbar = tqdm(
                total=self.total,
                desc=self.desc,
                **self.tqdm_kwargs
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pbar:
            self.pbar.close()
        
        end_time = time.perf_counter()
        duration = end_time - self.start_time if self.start_time else 0
        
        if exc_type is None:
            # Successful completion
            self.logger.info(f"Completed {self.desc}: {self.processed_count}/{self.total} items", 
                           duration=duration,
                           metadata={
                               'operation': self.desc,
                               'items_processed': self.processed_count,
                               'total_items': self.total,
                               'completion_rate': self.processed_count / self.total if self.total > 0 else 0,
                               'rate': self.processed_count / duration if duration > 0 else 0
                           },
                           emoji="✅")
        else:
            # Error occurred
            self.logger.error(f"Error in {self.desc}: {exc_val}", 
                            metadata={
                                'operation': self.desc,
                                'items_processed': self.processed_count,
                                'total_items': self.total,
                                'duration': duration
                            },
                            emoji="❌")
    
    def update(self, n: int = 1, description: Optional[str] = None):
        """Update progress by n steps."""
        self.processed_count += n
        if self.pbar:
            self.pbar.update(n)
            if description:
                self.pbar.set_description(description)
    
    def set_description(self, desc: str):
        """Update the progress bar description."""
        self.desc = desc
        if self.pbar:
            self.pbar.set_description(desc)
    
    def set_postfix(self, **kwargs):
        """Set postfix information on the progress bar."""
        if self.pbar and hasattr(self.pbar, 'set_postfix'):
            self.pbar.set_postfix(**kwargs)


# Global logger registry
_loggers: Dict[str, EnhancedLogger] = {}
_default_config = {
    'level': LogLevel.INFO,
    'console_output': True,
    'file_output': None,
    'structured_logging': False,
    'include_performance': True,
    'include_thread_id': False,
    'include_emoji': True,
    'emoji_position': 'prefix'
}


def get_logger(name: str, **config) -> EnhancedLogger:
    """Get or create a logger with the specified configuration."""
    if name not in _loggers:
        final_config = _default_config.copy()
        final_config.update(config)
        _loggers[name] = EnhancedLogger(name, **final_config)
    return _loggers[name]


def configure_default_logging(level: Union[LogLevel, int, str] = LogLevel.INFO,
                             console_output: bool = True,
                             file_output: Optional[Union[str, Path]] = None,
                             structured_logging: bool = False,
                             include_performance: bool = True,
                             include_thread_id: bool = False,
                             include_emoji: bool = True,
                             emoji_position: str = 'prefix'):
    """Configure default logging settings for new loggers."""
    global _default_config
    _default_config.update({
        'level': level,
        'console_output': console_output,
        'file_output': file_output,
        'structured_logging': structured_logging,
        'include_performance': include_performance,
        'include_thread_id': include_thread_id,
        'include_emoji': include_emoji,
        'emoji_position': emoji_position
    })


def set_global_log_level(level: Union[LogLevel, int, str]):
    """Set log level for all existing loggers."""
    converted_level = LogLevel(level).standard_level if isinstance(level, LogLevel) else level
    for logger in _loggers.values():
        logger.logger.setLevel(converted_level)


# Convenience functions for quick logging
def debug(message: str, *args, logger_name: str = "default", **kwargs):
    """Quick debug logging."""
    get_logger(logger_name).debug(message, *args, **kwargs)


def info(message: str, *args, logger_name: str = "default", **kwargs):
    """Quick info logging."""
    get_logger(logger_name).info(message, *args, **kwargs)


def warning(message: str, *args, logger_name: str = "default", **kwargs):
    """Quick warning logging."""
    get_logger(logger_name).warning(message, *args, **kwargs)


def error(message: str, *args, logger_name: str = "default", **kwargs):
    """Quick error logging."""
    get_logger(logger_name).error(message, *args, **kwargs)


def critical(message: str, *args, logger_name: str = "default", **kwargs):
    """Quick critical logging."""
    get_logger(logger_name).critical(message, *args, **kwargs)


def exception(message: str, *args, logger_name: str = "default", **kwargs):
    """Quick exception logging."""
    get_logger(logger_name).exception(message, *args, **kwargs)


# Performance tracking shortcuts
def timer(operation: str, logger_name: str = "default"):
    """Context manager for timing operations."""
    return get_logger(logger_name).timer(operation)


def time_function(operation: Optional[str] = None, logger_name: str = "default"):
    """Decorator for timing function execution."""
    return get_logger(logger_name).time_function(operation=operation)


def get_performance_metrics(operation: Optional[str] = None, logger_name: str = "default") -> Dict[str, Any]:
    """Get performance metrics from logger."""
    return get_logger(logger_name).get_performance_metrics(operation)


# Progress tracking shortcuts
def progress_iter(iterable: Iterable, 
                 desc: Optional[str] = None,
                 logger_name: str = "default",
                 **kwargs) -> Iterator:
    """Create a progress bar for iterables with logging."""
    return get_logger(logger_name).progress_iter(iterable, desc=desc, **kwargs)


def progress_wrapper(desc: Optional[str] = None,
                    logger_name: str = "default",
                    **kwargs):
    """Decorator to add progress tracking to functions."""
    return get_logger(logger_name).progress_wrapper(desc=desc, **kwargs)


def progress_context(total: int,
                    desc: Optional[str] = None,
                    logger_name: str = "default",
                    **kwargs):
    """Context manager for manual progress tracking."""
    return get_logger(logger_name).progress_context(total=total, desc=desc, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    configure_default_logging(
        level=LogLevel.DEBUG,
        file_output="logs/app.log",
        include_performance=True
    )
    
    # Get logger
    logger = get_logger("test_app")
    
    # Basic logging
    logger.info("Application started")
    logger.debug("Debug information")
    logger.warning("This is a warning")
    
    # Custom emoji examples
    logger.info("User logged in successfully", emoji="👤")
    logger.error("Database connection failed", emoji="💥")
    logger.info("Processing data", emoji="⚙️")
    
    # Custom emoji for level
    logger.set_level_emoji(logging.INFO, "🎯")
    logger.info("This uses custom emoji for INFO level")
    
    # Performance tracking
    with logger.timer("database_query"):
        time.sleep(0.1)  # Simulate work
    
    # Function decoration
    @logger.time_function(operation="calculation")
    def expensive_calculation(n: int) -> int:
        time.sleep(0.05)  # Simulate work
        return n * n
    
    result = expensive_calculation(10)
    logger.info(f"Calculation result: {result}")
    
    # Progress tracking examples
    print("\n=== Progress Tracking Examples ===")
    
    # 1. Progress iterator
    data_items = list(range(100))
    logger.info("Starting progress iterator example")
    
    processed_items = []
    for item in logger.progress_iter(data_items, desc="Processing data items", unit="items"):
        time.sleep(0.01)  # Simulate processing
        processed_items.append(item * 2)
    
    # 2. Progress wrapper decorator
    @logger.progress_wrapper(desc="Batch processing function", disable=False)
    def process_batch(items: List[int]) -> List[int]:
        """Process a batch of items with some computation."""
        results = []
        for item in items:
            time.sleep(0.005)  # Simulate work
            results.append(item ** 2)
        return results
    
    batch_results = process_batch(list(range(50)))
    
    # 3. Manual progress context
    with logger.progress_context(total=75, desc="Manual processing") as progress:
        for i in range(75):
            time.sleep(0.002)  # Simulate work
            progress.update(1)
            
            if i % 25 == 0:
                progress.set_description(f"Manual processing - Stage {i//25 + 1}")
    
    # 4. Using convenience functions
    logger.info("Using convenience functions for progress")
    
    # Global progress iterator
    global_data = range(30)
    for item in progress_iter(global_data, desc="Global iterator", logger_name="test_app"):
        time.sleep(0.01)
        
    # Global progress wrapper
    @progress_wrapper(desc="Global wrapped function", logger_name="test_app")
    def global_function(data):
        """Global function with progress tracking."""
        return [x * 3 for x in data]
    
    global_results = global_function(list(range(20)))
    
    # Error handling
    @logger.wrap_exceptions(ValueError, message="Custom error message")
    def risky_function():
        raise ValueError("Something went wrong")
    
    try:
        risky_function()
    except ValueError:
        logger.error("Handled the error")
    
    # Get metrics
    metrics = logger.get_performance_metrics()
    logger.metrics("Performance report", metrics)
    
    # Show tqdm availability status
    logger.info(f"TQDM available: {TQDM_AVAILABLE}", emoji="📊")
    
    print("Logging demonstration completed!")
