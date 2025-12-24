"""
Parallel Processing Utilities with Enhanced Logging

This module provides a flexible framework for executing functions in serial,
thread-based parallel, or process-based parallel modes with comprehensive
error handling, metrics collection, and logging integration.

Author: Ruppert20
"""

import time
import traceback
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Callable, List, Dict, Any, Optional, Literal, Union, Tuple
from dataclasses import dataclass, field
import inspect

# Import enhanced logging module
from .enhanced_logging import get_logger, LogLevel


@dataclass
class ExecutionMetrics:
    """Container for execution metrics."""
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    total_duration: float = 0.0
    successful_executions: int = 0
    failed_executions: int = 0
    execution_times: List[float] = field(default_factory=list)
    min_execution_time: Optional[float] = None
    max_execution_time: Optional[float] = None
    avg_execution_time: Optional[float] = None
    method: str = ""
    total_tasks: int = 0
    worker_count: Optional[int] = None
    
    def finalize(self):
        """Calculate final metrics."""
        self.end_time = time.perf_counter()
        self.total_duration = self.end_time - self.start_time
        
        if self.execution_times:
            self.min_execution_time = min(self.execution_times)
            self.max_execution_time = max(self.execution_times)
            self.avg_execution_time = sum(self.execution_times) / len(self.execution_times)
    
    def to_dict(self, verbose: bool = False) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        if verbose:
            return {
                'start_time': self.start_time,
                'end_time': self.end_time,
                'total_duration': self.total_duration,
                'successful_executions': self.successful_executions,
                'failed_executions': self.failed_executions,
                'total_tasks': self.total_tasks,
                'method': self.method,
                'worker_count': self.worker_count,
                'min_execution_time': self.min_execution_time,
                'max_execution_time': self.max_execution_time,
                'avg_execution_time': self.avg_execution_time,
                'execution_times': self.execution_times,
                'throughput': self.successful_executions / self.total_duration if self.total_duration > 0 else 0
            }
        else:
            # Basic metrics
            return {
                'total_duration': self.total_duration,
                'successful': self.successful_executions,
                'failed': self.failed_executions,
                'total': self.total_tasks,
                'method': self.method,
                'avg_time': self.avg_execution_time
            }


@dataclass
class TaskResult:
    """Container for individual task results."""
    index: int
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    error_traceback: Optional[str] = None
    execution_time: float = 0.0
    args: Optional[Tuple] = None
    kwargs: Optional[Dict] = None


class ParallelProcessor:
    """
    A comprehensive parallel processing utility with logging integration.
    
    Supports serial, thread-based, and process-based execution with
    configurable error handling and metrics collection.
    """
    
    def __init__(self,
                 pp_function: Callable,
                 log_level: Union[str, LogLevel] = 'WARNING',
                 pass_log_level: bool = False,
                 pp_method: Literal['serial', 'threads', 'processes'] = 'threads',
                 pp_errors: Literal['raise', 'ignore'] = 'raise',
                 pp_metrics: Literal['basic', 'verbose', 'none'] = 'basic',
                 pp_max_workers: int = 2,
                 timeout: Optional[float] = None,
                 logger_name: str = "ParallelProcessor"):
        """
        Initialize the parallel processor.
        
        Args:
            pp_function: The function to execute in parallel
            log_level: Logging level for the processor
            pass_log_level: Whether to pass log_level as a parameter to pp_function
            pp_method: Execution method (serial, threads, or processes)
            pp_errors: Error handling strategy (raise or ignore)
            pp_metrics: Metrics collection level (basic, verbose, or none)
            pp_max_workers: Maximum number of workers (default: 2)
            timeout: Timeout for each task execution (seconds)
            logger_name: Name for the logger instance
        """
        self.pp_function = pp_function
        self.log_level = log_level if isinstance(log_level, str) else log_level.name
        self.pass_log_level = pass_log_level
        self.pp_method = pp_method
        self.pp_errors = pp_errors
        self.pp_metrics = pp_metrics
        self.pp_max_workers = pp_max_workers
        self.timeout = timeout
        
        # Initialize logger
        self.logger = get_logger(logger_name, level=self.log_level)
        self.logger.set_level(self.log_level)
        
        # Validate function signature if pass_log_level is True
        if self.pass_log_level:
            self._validate_function_signature()
        
        # Determine worker count
        self._determine_worker_count()
    
    def _validate_function_signature(self):
        """Validate that the function can accept log_level parameter."""
        sig = inspect.signature(self.pp_function)
        params = sig.parameters
        
        # Check if function accepts **kwargs or has log_level parameter
        has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        has_log_level = 'log_level' in params
        
        if not (has_kwargs or has_log_level):
            self.logger.warning(
                f"Function {self.pp_function.__name__} doesn't accept 'log_level' parameter. "
                "pass_log_level will be ignored.",
                emoji="�"
            )
            self.pass_log_level = False
    
    def _determine_worker_count(self):
        """Determine the number of workers to use."""
        if self.pp_method == 'serial':
            self.worker_count = 1
        else:
            # Use the pp_max_workers parameter
            self.worker_count = self.pp_max_workers
    
    def _prepare_kwargs(self, kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare kwargs with log_level if needed."""
        prepared_kwargs = kwargs.copy() if kwargs else {}
        
        if self.pass_log_level and 'log_level' not in prepared_kwargs:
            prepared_kwargs['log_level'] = self.log_level
        
        return prepared_kwargs
    
    def _execute_single_task(self,
                            index: int,
                            args: Optional[Tuple] = None,
                            kwargs: Optional[Dict[str, Any]] = None) -> TaskResult:
        """Execute a single task with error handling and timing."""
        task_start = time.perf_counter()
        result = TaskResult(index=index, success=False, args=args, kwargs=kwargs)
        
        try:
            # Prepare arguments
            task_args = args if args else ()
            task_kwargs = self._prepare_kwargs(kwargs)
            
            # Execute function
            self.logger.trace(f"Executing task {index} with args={task_args}, kwargs={task_kwargs}")
            
            if self.timeout:
                # For timeout support in serial/thread mode, we'd need additional complexity
                # For now, timeout is primarily supported in process mode
                result.result = self.pp_function(*task_args, **task_kwargs)
            else:
                result.result = self.pp_function(*task_args, **task_kwargs)
            
            result.success = True
            self.logger.trace(f"Task {index} completed successfully")
            
        except Exception as e:
            result.error = e
            result.error_traceback = traceback.format_exc()
            self.logger.debug(f"Task {index} failed: {str(e)}")
            
            if self.pp_errors == 'raise':
                raise
        
        finally:
            result.execution_time = time.perf_counter() - task_start
        
        return result
    
    def _execute_serial(self,
                       arg_list: Optional[List[Any]] = None,
                       kwarg_list: Optional[List[Dict[str, Any]]] = None) -> List[TaskResult]:
        """Execute tasks serially."""
        results = []
        total_tasks = max(len(arg_list or []), len(kwarg_list or []), 1)
        
        self.logger.info(f"Starting serial execution of {total_tasks} tasks", emoji="=")
        
        with self.logger.progress_context(total=total_tasks, desc="Serial execution") as progress:
            for i in range(total_tasks):
                args = (arg_list[i],) if arg_list and i < len(arg_list) else ()
                kwargs = kwarg_list[i] if kwarg_list and i < len(kwarg_list) else None
                
                result = self._execute_single_task(i, args, kwargs)
                results.append(result)
                progress.update(1)
                
                if result.success:
                    progress.set_postfix(success=i+1, failed=sum(1 for r in results if not r.success))
        
        return results
    
    def _execute_threads(self,
                        arg_list: Optional[List[Any]] = None,
                        kwarg_list: Optional[List[Dict[str, Any]]] = None) -> List[TaskResult]:
        """Execute tasks using thread pool."""
        results = []
        total_tasks = max(len(arg_list or []), len(kwarg_list or []), 1)
        
        self.logger.info(
            f"Starting thread-based execution of {total_tasks} tasks with {self.worker_count} workers",
            emoji=">�"
        )
        
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            # Submit all tasks
            future_to_index = {}
            
            for i in range(total_tasks):
                args = (arg_list[i],) if arg_list and i < len(arg_list) else ()
                kwargs = kwarg_list[i] if kwarg_list and i < len(kwarg_list) else None
                
                future = executor.submit(self._execute_single_task, i, args, kwargs)
                future_to_index[future] = i
            
            # Collect results with progress tracking
            with self.logger.progress_context(total=total_tasks, desc="Thread execution") as progress:
                for future in as_completed(future_to_index):
                    try:
                        result = future.result(timeout=self.timeout)
                        results.append(result)
                        progress.update(1)
                        
                        success_count = sum(1 for r in results if r.success)
                        failed_count = len(results) - success_count
                        progress.set_postfix(success=success_count, failed=failed_count)
                        
                    except Exception as e:
                        # This handles timeout and other executor-level errors
                        index = future_to_index[future]
                        result = TaskResult(
                            index=index,
                            success=False,
                            error=e,
                            error_traceback=traceback.format_exc()
                        )
                        results.append(result)
                        progress.update(1)
                        
                        if self.pp_errors == 'raise':
                            raise
        
        # Sort results by index to maintain order
        results.sort(key=lambda r: r.index)
        return results
    
    def _execute_processes(self,
                          arg_list: Optional[List[Any]] = None,
                          kwarg_list: Optional[List[Dict[str, Any]]] = None) -> List[TaskResult]:
        """Execute tasks using process pool."""
        results = []
        total_tasks = max(len(arg_list or []), len(kwarg_list or []), 1)
        
        self.logger.info(
            f"Starting process-based execution of {total_tasks} tasks with {self.worker_count} workers",
            emoji="�"
        )
        
        # For process-based execution, we need to handle the function differently
        # since it needs to be pickleable
        with ProcessPoolExecutor(max_workers=self.worker_count) as executor:
            # Submit all tasks
            future_to_index = {}
            
            for i in range(total_tasks):
                args = (arg_list[i],) if arg_list and i < len(arg_list) else ()
                kwargs = self._prepare_kwargs(
                    kwarg_list[i] if kwarg_list and i < len(kwarg_list) else None
                )
                
                # For process pool, we directly submit the function
                future = executor.submit(self._execute_worker_task, self.pp_function, args, kwargs, i)
                future_to_index[future] = i
            
            # Collect results with progress tracking
            with self.logger.progress_context(total=total_tasks, desc="Process execution") as progress:
                for future in as_completed(future_to_index):
                    try:
                        result = future.result(timeout=self.timeout)
                        results.append(result)
                        progress.update(1)
                        
                        success_count = sum(1 for r in results if r.success)
                        failed_count = len(results) - success_count
                        progress.set_postfix(success=success_count, failed=failed_count)
                        
                    except Exception as e:
                        index = future_to_index[future]
                        result = TaskResult(
                            index=index,
                            success=False,
                            error=e,
                            error_traceback=traceback.format_exc()
                        )
                        results.append(result)
                        progress.update(1)
                        
                        if self.pp_errors == 'raise':
                            raise
        
        # Sort results by index to maintain order
        results.sort(key=lambda r: r.index)
        return results
    
    @staticmethod
    def _execute_worker_task(func: Callable, args: Tuple, kwargs: Dict, index: int) -> TaskResult:
        """Static method for process pool execution."""
        task_start = time.perf_counter()
        result = TaskResult(index=index, success=False, args=args, kwargs=kwargs)
        
        try:
            result.result = func(*args, **kwargs)
            result.success = True
        except Exception as e:
            result.error = e
            result.error_traceback = traceback.format_exc()
        finally:
            result.execution_time = time.perf_counter() - task_start
        
        return result
    
    def execute(self,
                arg_list: Optional[List[Any]] = None,
                kwarg_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute the function with the specified parameters.
        
        Args:
            arg_list: List of positional arguments for each execution
            kwarg_list: List of keyword arguments for each execution
        
        Returns:
            Dictionary with keys:
                - 'results': List of results from successful executions
                - 'errors': List of error information from failed executions
                - 'metrics': Execution metrics (if enabled)
        """
        # Validate inputs
        if arg_list is None and kwarg_list is None:
            # Execute once with no arguments
            arg_list = [()]
        
        # Initialize metrics
        metrics = ExecutionMetrics(
            method=self.pp_method,
            total_tasks=max(len(arg_list or []), len(kwarg_list or []), 1),
            worker_count=self.worker_count if self.pp_method != 'serial' else 1
        )
        
        self.logger.info(
            f"Starting parallel processing: method={self.pp_method}, "
            f"tasks={metrics.total_tasks}, workers={metrics.worker_count}",
            emoji="=�"
        )
        
        try:
            # Execute based on method
            if self.pp_method == 'serial':
                task_results = self._execute_serial(arg_list, kwarg_list)
            elif self.pp_method == 'threads':
                task_results = self._execute_threads(arg_list, kwarg_list)
            elif self.pp_method == 'processes':
                task_results = self._execute_processes(arg_list, kwarg_list)
            else:
                raise ValueError(f"Invalid pp_method: {self.pp_method}")
            
            # Process results
            results = []
            errors = []
            
            for task_result in task_results:
                if task_result.success:
                    results.append(task_result.result)
                    metrics.successful_executions += 1
                else:
                    error_info = {
                        'index': task_result.index,
                        'error': str(task_result.error) if task_result.error else 'Unknown error',
                        'error_type': type(task_result.error).__name__ if task_result.error else 'Unknown',
                        'traceback': task_result.error_traceback,
                        'args': task_result.args,
                        'kwargs': task_result.kwargs
                    }
                    errors.append(error_info)
                    metrics.failed_executions += 1
                
                metrics.execution_times.append(task_result.execution_time)
            
            # Finalize metrics
            metrics.finalize()
            
            # Log summary
            if metrics.failed_executions > 0:
                self.logger.warning(
                    f"Execution completed with errors: {metrics.successful_executions} succeeded, "
                    f"{metrics.failed_executions} failed in {metrics.total_duration:.2f}s",
                    emoji="�"
                )
            else:
                self.logger.info(
                    f"All {metrics.successful_executions} tasks completed successfully "
                    f"in {metrics.total_duration:.2f}s",
                    emoji=""
                )
            
            # Prepare return dictionary
            return_dict = {
                'results': results,
                'errors': errors
            }
            
            # Add metrics if requested
            if self.pp_metrics != 'none':
                return_dict['metrics'] = metrics.to_dict(verbose=(self.pp_metrics == 'verbose')) # type: ignore
                
                if self.pp_metrics == 'verbose':
                    self.logger.metrics(
                        "Detailed execution metrics",
                        return_dict['metrics'],
                        emoji="=�"
                    )
            
            return return_dict
            
        except Exception as e:
            self.logger.error(
                f"Fatal error during parallel processing: {str(e)}",
                capture_exception=True,
                emoji="=�"
            )
            
            if self.pp_errors == 'raise':
                raise
            
            # Return error information even if we're not raising
            return {
                'results': [],
                'errors': [{
                    'index': -1,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }],
                'metrics': metrics.to_dict(verbose=False) if self.pp_metrics != 'none' else None
            }


def parallel_execute(pp_function: Callable,
                    log_level: Union[str, LogLevel] = 'WARNING',
                    pass_log_level: bool = False,
                    pp_method: Literal['serial', 'threads', 'processes'] = 'threads',
                    pp_errors: Literal['raise', 'ignore'] = 'raise',
                    pp_metrics: Literal['basic', 'verbose', 'none'] = 'basic',
                    arg_list: Optional[List[Any]] = None,
                    kwarg_list: Optional[List[Dict[str, Any]]] = None,
                    pp_max_workers: int = 2,
                    timeout: Optional[float] = None) -> Dict[str, Any]:
    """
    Convenience function for parallel execution without creating a class instance.
    
    Args:
        pp_function: The function to execute
        log_level: Logging level
        pass_log_level: Whether to pass log_level to the function
        pp_method: Execution method (serial, threads, processes)
        pp_errors: Error handling (raise or ignore)
        pp_metrics: Metrics collection level
        arg_list: List of positional arguments
        kwarg_list: List of keyword arguments
        pp_max_workers: Maximum number of workers (default: 2)
        timeout: Timeout per task
    
    Returns:
        Dictionary with 'results', 'errors', and optionally 'metrics'
    """
    processor = ParallelProcessor(
        pp_function=pp_function,
        log_level=log_level,
        pass_log_level=pass_log_level,
        pp_method=pp_method,
        pp_errors=pp_errors,
        pp_metrics=pp_metrics,
        pp_max_workers=pp_max_workers,
        timeout=timeout
    )
    
    return processor.execute(arg_list=arg_list, kwarg_list=kwarg_list)
