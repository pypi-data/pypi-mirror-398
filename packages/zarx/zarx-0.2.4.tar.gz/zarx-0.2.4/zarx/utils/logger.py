"""
Production-grade logging system for zarx-IGRIS.
Includes distributed logging, metrics aggregation, and real-time monitoring.
"""

import logging
import sys
import os
import json
import time
import csv
import threading
import queue
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import warnings
import traceback
import atexit

# Try to import optional dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    warnings.warn("NumPy not available, some features disabled")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    warnings.warn("PyTorch not available, some features disabled")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    warnings.warn("psutil not available, some performance monitoring features disabled")


class LogLevel(Enum):
    """Log levels with numeric values."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    level: str
    module: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        if self.exception is None:
            result.pop('exception')
        if self.stack_trace is None:
            result.pop('stack_trace')
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class MetricEntry:
    """Metric entry for time series data."""
    timestamp: str
    metric_name: str
    value: float
    step: int
    epoch: int
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AsyncLogHandler:
    """Asynchronous log handler for high-performance logging."""
    
    def __init__(self, max_queue_size: int = 10000, batch_size: int = 100):
        """
        Initialize async log handler.
        
        Args:
            max_queue_size: Maximum queue size before blocking
            batch_size: Batch size for processing
        """
        self.queue = queue.Queue(maxsize=max_queue_size)
        self.batch_size = batch_size
        self.handlers: List[Callable] = []
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.batch_buffer: List[Union[LogEntry, MetricEntry]] = []
        
    def start(self):
        """Start async processing thread."""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._process_loop,
            daemon=True,
            name="AsyncLogHandler"
        )
        self.worker_thread.start()
        
        # Register cleanup
        atexit.register(self.stop)
    
    def stop(self):
        """Stop async processing thread."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
    
    def add_handler(self, handler: Callable):
        """Add log handler."""
        self.handlers.append(handler)
    
    def log(self, entry: Union[LogEntry, MetricEntry]):
        """Add log entry to queue."""
        try:
            self.queue.put(entry, block=False)
        except queue.Full:
            # Fallback to synchronous logging if queue is full
            self._process_entry(entry)
    
    def _process_loop(self):
        """Main processing loop."""
        while self.running:
            try:
                # Wait for entry with timeout
                entry = self.queue.get(timeout=0.1)
                self.batch_buffer.append(entry)
                
                # Process batch if full
                if len(self.batch_buffer) >= self.batch_size:
                    self._process_batch()
                    
            except queue.Empty:
                # Process any remaining entries in buffer
                if self.batch_buffer:
                    self._process_batch()
            except Exception as e:
                # Log error but don't crash
                print(f"Error in async log handler: {e}")
    
    def _process_batch(self):
        """Process batch of entries."""
        if not self.batch_buffer:
            return
        
        for handler in self.handlers:
            try:
                handler(self.batch_buffer)
            except Exception as e:
                print(f"Error in log handler: {e}")
        
        self.batch_buffer = []
    
    def _process_entry(self, entry: Union[LogEntry, MetricEntry]):
        """Process single entry synchronously."""
        for handler in self.handlers:
            try:
                handler([entry])
            except Exception as e:
                print(f"Error in log handler: {e}")


class ZARXLogger:
    """
    Main logger for zarx-IGRIS with multiple outputs and monitoring.
    """
    
    def __init__(
        self,
        name: str = "zarx",
        log_dir: Union[str, Path] = "logs",
        level: LogLevel = LogLevel.INFO,
        enable_async: bool = True,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_metrics: bool = True,
        distributed_rank: int = 0
    ):
        """
        Initialize zarx logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files, or a full path to a log file.
            level: Logging level
            enable_async: Enable async logging for performance
            enable_console: Enable console output
            enable_file: Enable file output
            enable_metrics: Enable metrics collection
            distributed_rank: Rank in distributed training
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.level = level
        self.distributed_rank = distributed_rank
        
        # Create log directory if log_dir is a directory
        if self.log_dir.is_dir() or '.' not in self.log_dir.name:
             self.log_dir.mkdir(parents=True, exist_ok=True)
        else: # it's a file
             self.log_dir.parent.mkdir(parents=True, exist_ok=True)

        
        # Setup async handler if enabled
        self.async_handler = AsyncLogHandler() if enable_async else None
        
        # Initialize handlers
        self.handlers: Dict[str, Any] = {}
        self.metric_writers: Dict[str, Any] = {}
        
        
        # Setup outputs
        if enable_console:
            self._setup_console_handler()
        
        if enable_file:
            self._setup_file_handler()
        
        if enable_metrics:
            self._setup_metrics_handler()
        
        # Start async handler if enabled
        if enable_async and self.async_handler:
            self.async_handler.start()
        
        # Statistics
        self.stats = {
            "log_count": 0,
            "metric_count": 0,
            "error_count": 0,
            "last_error": None
        }
        
        # Performance monitoring
        self.performance_stats = {
            "avg_log_time": 0.0,
            "total_log_time": 0.0,
            "max_log_time": 0.0
        }
        
        # Register cleanup
        atexit.register(self.cleanup)
    
    def _setup_console_handler(self):
        """Setup console output handler."""
        class ConsoleHandler:
            def __init__(self, rank: int):
                self.rank = rank
            
            def __call__(self, entries: List[Union[LogEntry, MetricEntry]]):
                for entry in entries:
                    if isinstance(entry, LogEntry):
                        if self.rank == 0:  # Only rank 0 prints to console
                            level_color = {
                                "DEBUG": "\033[90m",      # Gray
                                "INFO": "\033[94m",       # Blue
                                "WARNING": "\033[93m",    # Yellow
                                "ERROR": "\033[91m",      # Red
                                "CRITICAL": "\033[95m"    # Magenta
                            }
                            reset = "\033[0m"
                            
                            color = level_color.get(entry.level, "\033[0m")
                            msg = f"{color}[{entry.timestamp}] [{entry.level}] [{entry.module}] {entry.message}{reset}"
                            
                            if entry.exception:
                                msg += f"\n{color}Exception: {entry.exception}{reset}"
                                if entry.stack_trace and entry.level == LogLevel.CRITICAL.name:
                                    msg += f"\n{color}Stack Trace:\n{entry.stack_trace}{reset}"
                            
                            print(msg)
        
        handler = ConsoleHandler(self.distributed_rank)
        self.handlers["console"] = handler
        
        if self.async_handler:
            self.async_handler.add_handler(handler)
    
    def _setup_file_handler(self):
        """Setup file output handler."""
        if self.log_dir.is_dir():
            log_file = self.log_dir / f"zarx_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            metrics_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else: # it's a file path
            log_file = self.log_dir
            metrics_file = self.log_dir.with_suffix('.csv')

        class FileHandler:
            def __init__(self, log_path: Path, metrics_path: Path):
                self.log_path = log_path
                self.metrics_path = metrics_path
                self.log_file = None
                self.metrics_file = None
                self.metrics_writer = None
                self._initialize_files()

            def _initialize_files(self):
                # This logic is now inside a method to be called after the handler is created
                self.log_file = open(self.log_path, 'a', encoding='utf-8')
                
                # Ensure metrics file has header
                if not self.metrics_path.exists() or os.stat(self.metrics_path).st_size == 0:
                    with open(self.metrics_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=[
                            'timestamp', 'metric_name', 'value', 'step', 'epoch', 'tags'
                        ])
                        writer.writeheader()
            
            def __call__(self, entries: List[Union[LogEntry, MetricEntry]]):
                log_entries_to_write = []
                metric_entries_to_write = []

                for entry in entries:
                    if isinstance(entry, LogEntry):
                        log_entries_to_write.append(entry.to_json())
                    elif isinstance(entry, MetricEntry):
                        metric_entries_to_write.append(entry.to_dict())

                if log_entries_to_write:
                    with open(self.log_path, 'a', encoding='utf-8') as f:
                        f.write('\n'.join(log_entries_to_write) + '\n')

                if metric_entries_to_write:
                    # Open in append mode, create writer if needed
                    if self.metrics_file is None or self.metrics_file.closed:
                        self.metrics_file = open(self.metrics_path, 'a', newline='', encoding='utf-8')
                        self.metrics_writer = csv.DictWriter(
                            self.metrics_file,
                            fieldnames=['timestamp', 'metric_name', 'value', 'step', 'epoch', 'tags']
                        )
                    
                    self.metrics_writer.writerows(metric_entries_to_write)
                    self.metrics_file.flush() # Ensure it's written
            
            def close(self):
                """Close file handles."""
                if self.log_file and not self.log_file.closed:
                    self.log_file.close()
                if self.metrics_file and not self.metrics_file.closed:
                    self.metrics_file.close()
        
        # Create and add the handler instance first
        handler = FileHandler(log_file, metrics_file)
        self.handlers["file"] = handler
        
        if self.async_handler:
            self.async_handler.add_handler(handler)
    
    def _setup_metrics_handler(self):
        """Setup metrics aggregation handler."""
        class MetricsHandler:
            def __init__(self):
                self.metrics: Dict[str, List[MetricEntry]] = {}
                self.aggregated: Dict[str, Dict[str, float]] = {}
            
            def __call__(self, entries: List[Union[LogEntry, MetricEntry]]):
                for entry in entries:
                    if isinstance(entry, MetricEntry):
                        # Store metric
                        if entry.metric_name not in self.metrics:
                            self.metrics[entry.metric_name] = []
                        self.metrics[entry.metric_name].append(entry)
                        
                        # Aggregate last 100 values
                        recent = self.metrics[entry.metric_name][-100:]
                        values = [m.value for m in recent]
                        
                        if values:
                            self.aggregated[entry.metric_name] = {
                                'mean': np.mean(values) if NUMPY_AVAILABLE else sum(values)/len(values),
                                'std': np.std(values) if NUMPY_AVAILABLE else 0.0,
                                'min': min(values),
                                'max': max(values),
                                'count': len(values)
                            }
        
        handler = MetricsHandler()
        self.metric_writers["aggregator"] = handler
        
        if self.async_handler:
            self.async_handler.add_handler(handler)
    
    def log(
        self,
        level: LogLevel,
        module: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """
        Log a message.
        
        Args:
            level: Log level
            module: Module name
            message: Log message
            data: Additional data
            exception: Exception to log
        """
        # Skip if below log level
        if level.value < self.level.value:
            return
        
        start_time = time.time()
        
        # Create log entry
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.name,
            module=module,
            message=message,
            data=data or {},
            exception=str(exception) if exception else None,
            stack_trace="".join(traceback.format_exception(type(exception), exception, exception.__traceback__)) if exception else None
        )
        
        # Update statistics
        self.stats["log_count"] += 1
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.stats["error_count"] += 1
            self.stats["last_error"] = entry
        
        # Send to async handler or process directly
        if self.async_handler:
            self.async_handler.log(entry)
        else:
            # Process synchronously
            for handler in self.handlers.values():
                handler([entry])
        
        # Update performance stats
        log_time = time.time() - start_time
        self.performance_stats["total_log_time"] += log_time
        self.performance_stats["avg_log_time"] = (
            self.performance_stats["total_log_time"] / self.stats["log_count"]
        )
        self.performance_stats["max_log_time"] = max(
            self.performance_stats["max_log_time"], log_time
        )
    
    def debug(self, module: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self.log(LogLevel.DEBUG, module, message, data)
    
    def info(self, module: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self.log(LogLevel.INFO, module, message, data)
    
    def warning(self, module: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self.log(LogLevel.WARNING, module, message, data)
    
    def error(
        self,
        module: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """Log error message."""
        self.log(LogLevel.ERROR, module, message, data, exception)
    
    def critical(
        self,
        module: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """Log critical message."""
        self.log(LogLevel.CRITICAL, module, message, data, exception)
    
    def metric(
        self,
        name: str,
        value: float,
        step: int,
        epoch: int,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Log a metric.
        
        Args:
            name: Metric name
            value: Metric value
            step: Training step
            epoch: Training epoch
            tags: Additional tags
        """
        entry = MetricEntry(
            timestamp=datetime.now().isoformat(),
            metric_name=name,
            value=value,
            step=step,
            epoch=epoch,
            tags=tags or {}
        )
        
        # Update statistics
        self.stats["metric_count"] += 1
        
        # Send to async handler or process directly
        if self.async_handler:
            self.async_handler.log(entry)
        else:
            # Process synchronously
            for handler in self.handlers.values():
                handler([entry])
    
    def log_model_metrics(
        self,
        metrics: Dict[str, float],
        step: int,
        epoch: int,
        prefix: str = "train"
    ):
        """
        Log multiple model metrics.
        
        Args:
            metrics: Dictionary of metric names to values
            step: Training step
            epoch: Training epoch
            prefix: Metric name prefix
        """
        for name, value in metrics.items():
            self.metric(f"{prefix}/{name}", value, step, epoch)
    
    def log_router_stats(
        self,
        stats: Dict[str, Any],
        step: int,
        epoch: int
    ):
        """
        Log router statistics.
        
        Args:
            stats: Router statistics dictionary
            step: Training step
            epoch: Training epoch
        """
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                self.metric(f"router/{key}", value, step, epoch)
            elif isinstance(value, list):
                for i, val in enumerate(value):
                    if isinstance(val, (int, float)):
                        self.metric(f"router/{key}_{i}", val, step, epoch)
    
    def log_expert_stats(
        self,
        expert_id: int,
        activation_count: int,
        load: float,
        step: int,
        epoch: int
    ):
        """
        Log expert statistics.
        
        Args:
            expert_id: Expert ID
            activation_count: Number of activations
            load: Current load
            step: Training step
            epoch: Training epoch
        """
        self.metric(f"expert/{expert_id}/activation_count", activation_count, step, epoch)
        self.metric(f"expert/{expert_id}/load", load, step, epoch)
    
    def log_memory_stats(
        self,
        stats: Dict[str, float],
        step: int,
        epoch: int
    ):
        """
        Log memory statistics.
        
        Args:
            stats: Memory statistics
            step: Training step
            epoch: Training epoch
        """
        for key, value in stats.items():
            self.metric(f"memory/{key}", value, step, epoch)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get logger statistics.
        
        Returns:
            Dictionary of statistics
        """
        stats = self.stats.copy()
        stats.update(self.performance_stats)
        
        # Get aggregated metrics if available
        if "aggregator" in self.metric_writers:
            stats["aggregated_metrics"] = self.metric_writers["aggregator"].aggregated
        
        return stats
    
    def create_checkpoint(self, path: Union[str, Path]):
        """
        Create logger checkpoint.
        
        Args:
            path: Path to save checkpoint
        """
        stats_for_dump = self.stats.copy()
        if stats_for_dump["last_error"] is not None:
            stats_for_dump["last_error"] = stats_for_dump["last_error"].to_dict()

        checkpoint = {
            "stats": stats_for_dump,
            "performance_stats": self.performance_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def load_checkpoint(self, path: Union[str, Path]):
        """
        Load logger checkpoint.
        
        Args:
            path: Path to load checkpoint from
        """
        try:
            with open(path, 'r') as f:
                checkpoint = json.load(f)
            
            self.stats.update(checkpoint.get("stats", {}))
            self.performance_stats.update(checkpoint.get("performance_stats", {}))
            
            self.info(
                "logger",
                f"Loaded checkpoint from {path}",
                {"checkpoint_timestamp": checkpoint.get("timestamp")}
            )
        except Exception as e:
            self.error("logger", f"Failed to load checkpoint: {e}", exception=e)
    
    def cleanup(self):
        """Cleanup resources."""
        if self.async_handler:
            self.async_handler.stop()
        
        # Close file handlers
        for handler in self.handlers.values():
            if hasattr(handler, 'close'):
                handler.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        if exc_type is not None:
            self.error(
                "logger",
                f"Context manager exited with exception: {exc_type.__name__}",
                exception=exc_val
            )


# ==================== DISTRIBUTED LOGGING ====================

class DistributedLogger:
    """
    Logger for distributed training environments.
    """
    
    def __init__(
        self,
        base_logger: ZARXLogger,
        world_size: int,
        rank: int,
        enable_all_reduce: bool = True
    ):
        """
        Initialize distributed logger.
        
        Args:
            base_logger: Base zarx logger
            world_size: World size (number of processes)
            rank: Process rank
            enable_all_reduce: Enable metric aggregation across processes
        """
        self.base_logger = base_logger
        self.world_size = world_size
        self.rank = rank
        self.enable_all_reduce = enable_all_reduce
        
        # Buffer for metrics to aggregate
        self.metric_buffer: Dict[str, List[float]] = {}
    
    def log_metric_all_reduce(
        self,
        name: str,
        value: float,
        step: int,
        epoch: int,
        reduction: str = "mean"
    ):
        """
        Log metric with all-reduce across processes.
        
        Args:
            name: Metric name
            value: Local metric value
            step: Training step
            epoch: Training epoch
            reduction: Reduction method ('mean', 'sum', 'max', 'min')
        """
        if not self.enable_all_reduce or self.world_size == 1:
            # Single process or all-reduce disabled
            self.base_logger.metric(name, value, step, epoch)
            return
        
        # Buffer metric for aggregation
        if name not in self.metric_buffer:
            self.metric_buffer[name] = []
        
        self.metric_buffer[name].append((value, step, epoch))
        
        # Aggregate when buffer is full
        if len(self.metric_buffer[name]) >= self.world_size:
            values = [v for v, _, _ in self.metric_buffer[name]]
            steps = [s for _, s, _ in self.metric_buffer[name]]
            epochs = [e for _, _, e in self.metric_buffer[name]]
            
            # All processes should have same step and epoch
            step_consistent = all(s == steps[0] for s in steps)
            epoch_consistent = all(e == epochs[0] for e in epochs)
            
            if step_consistent and epoch_consistent:
                # Apply reduction
                if reduction == "mean":
                    reduced_value = sum(values) / len(values)
                elif reduction == "sum":
                    reduced_value = sum(values)
                elif reduction == "max":
                    reduced_value = max(values)
                elif reduction == "min":
                    reduced_value = min(values)
                else:
                    reduced_value = sum(values) / len(values)  # Default to mean
                
                # Only rank 0 logs the aggregated metric
                if self.rank == 0:
                    self.base_logger.metric(
                        f"distributed/{name}",
                        reduced_value,
                        steps[0],
                        epochs[0]
                    )
                
                # Clear buffer
                del self.metric_buffer[name]
    
    def log_router_stats_distributed(
        self,
        stats: Dict[str, Any],
        step: int,
        epoch: int
    ):
        """
        Log router statistics with distributed aggregation.
        
        Args:
            stats: Router statistics
            step: Training step
            epoch: Training epoch
        """
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                self.log_metric_all_reduce(
                    f"router/{key}",
                    value,
                    step,
                    epoch,
                    reduction="mean"
                )
    
    def flush(self):
        """Flush buffered metrics."""
        for name, buffer in list(self.metric_buffer.items()):
            if buffer:
                # Log whatever we have
                values = [v for v, _, _ in buffer]
                steps = [s for _, s, _ in buffer]
                epochs = [e for _, _, e in buffer]
                
                # Take most common step and epoch
                from collections import Counter
                step = Counter(steps).most_common(1)[0][0]
                epoch = Counter(epochs).most_common(1)[0][0]
                
                # Log average
                avg_value = sum(values) / len(values)
                
                if self.rank == 0:
                    self.base_logger.metric(
                        f"distributed/flushed/{name}",
                        avg_value,
                        step,
                        epoch
                    )
                
                # Clear buffer
                del self.metric_buffer[name]


# ==================== PERFORMANCE MONITORING ====================

class PerformanceMonitor:
    """
    Real-time performance monitoring.
    """
    
    def __init__(
        self,
        logger: ZARXLogger,
        update_interval: int = 100,  # steps
        enable_profiling: bool = False
    ):
        """
        Initialize performance monitor.
        
        Args:
            logger: zarx logger instance
            update_interval: Update interval in steps
            enable_profiling: Enable PyTorch profiling
        """
        self.logger = logger
        self.update_interval = update_interval
        self.enable_profiling = enable_profiling
        
        # Performance metrics
        self.metrics = {
            "throughput_tokens_per_sec": 0.0,
            "memory_allocated_mb": 0.0,
            "memory_reserved_mb": 0.0,
            "cpu_usage_percent": 0.0,
            "gpu_usage_percent": 0.0,
            "io_wait_time_sec": 0.0
        }
        
        # Counters
        self.step_count = 0
        self.token_count = 0
        self.start_time = time.time()
        
        # Profiling
        self.profiler = None
        if enable_profiling and TORCH_AVAILABLE:
            try:
                self.profiler = torch.profiler.profile(
                    activities=[
                        torch.profiler.ProfilerActivity.CPU,
                        torch.profiler.ProfilerActivity.CUDA
                    ] if torch.cuda.is_available() else [
                        torch.profiler.ProfilerActivity.CPU
                    ],
                    schedule=torch.profiler.schedule(
                        wait=1,
                        warmup=1,
                        active=3,
                        repeat=1
                    ),
                    on_trace_ready=self._on_trace_ready
                )
            except Exception as e:
                self.logger.warning(
                    "performance_monitor",
                    f"Failed to initialize profiler: {e}"
                )
    
    def start_step(self):
        """Start monitoring a training step."""
        self.step_start_time = time.time()
        
        if self.profiler:
            self.profiler.start()
    
    def end_step(self, tokens_processed: int):
        """
        End monitoring a training step.
        
        Args:
            tokens_processed: Number of tokens processed
        """
        step_time = time.time() - self.step_start_time
        
        # Update counters
        self.step_count += 1
        self.token_count += tokens_processed
        
        # Update profiler
        if self.profiler:
            self.profiler.step()
        
        # Update metrics periodically
        if self.step_count % self.update_interval == 0:
            self._update_metrics(step_time, tokens_processed)
    
    def _update_metrics(self, step_time: float, tokens_processed: int):
        """Update performance metrics."""
        # Compute throughput
        total_time = time.time() - self.start_time
        self.metrics["throughput_tokens_per_sec"] = self.token_count / total_time
        
        # Memory usage
        if TORCH_AVAILABLE:
            self.metrics["memory_allocated_mb"] = (
                torch.cuda.memory_allocated() / 1e6
                if torch.cuda.is_available()
                else 0.0
            )
            self.metrics["memory_reserved_mb"] = (
                torch.cuda.memory_reserved() / 1e6
                if torch.cuda.is_available()
                else 0.0
            )
        
        # CPU usage (simplified)
        self.metrics["cpu_usage_percent"] = psutil.cpu_percent() if PSUTIL_AVAILABLE else 0.0
        
        # GPU usage (if available)
        if TORCH_AVAILABLE and torch.cuda.is_available():
            self.metrics["gpu_usage_percent"] = torch.cuda.utilization()
        
        # Log metrics
        self.logger.log_model_metrics(
            self.metrics,
            self.step_count,
            epoch=0,  # Will be updated by trainer
            prefix="performance"
        )
    
    def _on_trace_ready(self, prof):
        """Handle profiler trace."""
        # Save profiler trace
        trace_file = self.logger.log_dir / f"trace_step_{self.step_count}.json"
        prof.export_chrome_trace(str(trace_file))
        
        self.logger.info(
            "performance_monitor",
            f"Saved profiler trace to {trace_file}"
        )
    
    def get_report(self) -> Dict[str, Any]:
        """
        Get performance report.
        
        Returns:
            Performance report
        """
        return {
            "metrics": self.metrics,
            "counters": {
                "step_count": self.step_count,
                "token_count": self.token_count,
                "total_time_sec": time.time() - self.start_time
            },
            "efficiency": {
                "tokens_per_second": self.metrics["throughput_tokens_per_sec"],
                "memory_efficiency": self.token_count / (self.metrics["memory_allocated_mb"] + 1e-6),
                "compute_utilization": min(
                    self.metrics["cpu_usage_percent"],
                    self.metrics.get("gpu_usage_percent", 0.0)
                ) / 100.0
            }
        }
    
    def reset(self):
        """Reset monitor."""
        self.step_count = 0
        self.token_count = 0
        self.start_time = time.time()
        self.metrics = {k: 0.0 for k in self.metrics}


# ==================== GLOBAL LOGGER INSTANCE ====================

# Global logger instance
_GLOBAL_LOGGER: Optional[ZARXLogger] = None
_GLOBAL_DISTRIBUTED_LOGGER: Optional[DistributedLogger] = None
_GLOBAL_PERFORMANCE_MONITOR: Optional[PerformanceMonitor] = None


def setup_global_logger(
    name: str = "zarx",
    log_dir: Union[str, Path] = "logs",
    level: LogLevel = LogLevel.INFO,
    enable_async: bool = True,
    distributed_world_size: int = 1,
    distributed_rank: int = 0,
    enable_performance_monitoring: bool = True
):
    """
    Setup global logger instance.
    
    Args:
        name: Logger name
        log_dir: Log directory
        level: Log level
        enable_async: Enable async logging
        distributed_world_size: World size for distributed training
        distributed_rank: Rank for distributed training
        enable_performance_monitoring: Enable performance monitoring
    """
    global _GLOBAL_LOGGER, _GLOBAL_DISTRIBUTED_LOGGER, _GLOBAL_PERFORMANCE_MONITOR
    
    # Create base logger
    _GLOBAL_LOGGER = ZARXLogger(
        name=name,
        log_dir=log_dir,
        level=level,
        enable_async=enable_async,
        enable_file=True, # Explicitly enable file logging
        enable_metrics=True, # Explicitly enable metrics logging
        distributed_rank=distributed_rank
    )
    
    # Create distributed logger if needed
    if distributed_world_size > 1:
        _GLOBAL_DISTRIBUTED_LOGGER = DistributedLogger(
            _GLOBAL_LOGGER,
            world_size=distributed_world_size,
            rank=distributed_rank
        )
    
    # Create performance monitor if enabled
    if enable_performance_monitoring:
        _GLOBAL_PERFORMANCE_MONITOR = PerformanceMonitor(_GLOBAL_LOGGER)
    
    # Log initialization
    get_logger().info(
        "global_logger",
        "Global logger initialized",
        {
            "log_dir": str(log_dir),
            "level": level.name,
            "distributed_world_size": distributed_world_size,
            "distributed_rank": distributed_rank
        }
    )


def get_logger() -> ZARXLogger:
    """
    Get global logger instance.
    
    Returns:
        Global logger instance
    """
    global _GLOBAL_LOGGER
    
    if _GLOBAL_LOGGER is None:
        # Setup default logger
        setup_global_logger()
    
    return _GLOBAL_LOGGER


def get_distributed_logger() -> Optional[DistributedLogger]:
    """
    Get global distributed logger instance.
    
    Returns:
        Distributed logger or None if not initialized
    """
    global _GLOBAL_DISTRIBUTED_LOGGER
    return _GLOBAL_DISTRIBUTED_LOGGER


def get_performance_monitor() -> Optional[PerformanceMonitor]:
    """
    Get global performance monitor.
    
    Returns:
        Performance monitor or None if not initialized
    """
    global _GLOBAL_PERFORMANCE_MONITOR
    return _GLOBAL_PERFORMANCE_MONITOR


# ==================== CONTEXT MANAGERS ====================

class timed_block:
    """Context manager for timing code blocks."""
    
    def __init__(self, name: str, logger: Optional[ZARXLogger] = None):
        """
        Initialize timed block.
        
        Args:
            name: Block name
            logger: Logger instance (uses global if None)
        """
        self.name = name
        self.logger = logger or get_logger()
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        self.logger.info(
            "timed_block",
            f"Block '{self.name}' completed in {elapsed:.3f}s",
            {"elapsed_seconds": elapsed}
        )


class log_exceptions:
    """Context manager for logging exceptions."""
    
    def __init__(self, module: str, logger: Optional[ZARXLogger] = None):
        """
        Initialize exception logger.
        
        Args:
            module: Module name
            logger: Logger instance
        """
        self.module = module
        self.logger = logger or get_logger()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                self.module,
                f"Exception occurred: {exc_type.__name__}",
                exception=exc_val
            )
        # Don't suppress the exception
        return False


# ==================== TESTING ====================

__all__ = [
    'LogLevel',
    'LogEntry',
    'MetricEntry',
    'ZARXLogger',
    'DistributedLogger',
    'PerformanceMonitor',
    'setup_global_logger',
    'get_logger',
    'get_distributed_logger',
    'get_performance_monitor',
    'timed_block',
    'log_exceptions',
]

