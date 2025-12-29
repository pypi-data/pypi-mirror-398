"""
Progress tracking for ETL pipelines.

This module provides progress reporting and observability for long-running ETL jobs.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional


@dataclass
class ETLProgress:
    """Progress information for ETL pipeline execution."""
    
    stage: str  # 'extract', 'transform', 'load'
    batch_num: int
    total_batches: Optional[int]
    records_processed: int
    records_total: Optional[int]
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float]
    memory_usage_mb: Optional[float] = None
    error_count: int = 0
    
    def __str__(self) -> str:
        """Human-readable progress string."""
        stage_emoji = {
            'extract': '📥',
            'transform': '🔄',
            'load': '📤',
        }.get(self.stage, '⚙️')
        
        progress_pct = (
            f"{(self.records_processed / self.records_total * 100):.1f}%"
            if self.records_total
            else "?"
        )
        
        batch_info = (
            f"Batch {self.batch_num}/{self.total_batches}"
            if self.total_batches
            else f"Batch {self.batch_num}"
        )
        
        time_info = f"{self.elapsed_seconds:.1f}s"
        if self.estimated_remaining_seconds:
            time_info += f" (est. {self.estimated_remaining_seconds:.1f}s remaining)"
        
        memory_info = f" | {self.memory_usage_mb:.1f}MB" if self.memory_usage_mb else ""
        error_info = f" | {self.error_count} errors" if self.error_count > 0 else ""
        
        records_info = (
            f"{self.records_processed:,}/{self.records_total:,} records ({progress_pct})"
            if self.records_total is not None
            else f"{self.records_processed:,} records"
        )
        
        return (
            f"{stage_emoji} [{self.stage.upper()}] {batch_info} | "
            f"{records_info} | "
            f"{time_info}{memory_info}{error_info}"
        )


class ProgressTracker:
    """Tracks and reports ETL pipeline progress."""
    
    def __init__(
        self,
        callback: Optional[Callable[[ETLProgress], None]] = None,
        verbose: bool = True,
    ):
        """
        Initialize progress tracker.
        
        Args:
            callback: Optional callback function to call with progress updates
            verbose: If True, print progress to stdout
        """
        self.callback = callback
        self.verbose = verbose
        self.start_time: Optional[datetime] = None
        self.stage_start_time: Optional[datetime] = None
        self.last_batch_times: list[float] = []  # Track last N batch processing times
        self.max_batch_times = 10  # Keep last 10 batch times for estimation
    
    def start(self):
        """Start tracking."""
        self.start_time = datetime.now()
        self.stage_start_time = self.start_time
    
    def report(
        self,
        stage: str,
        batch_num: int,
        records_processed: int,
        records_total: Optional[int] = None,
        total_batches: Optional[int] = None,
        memory_usage_mb: Optional[float] = None,
        error_count: int = 0,
    ):
        """
        Report progress update.
        
        Args:
            stage: Current stage ('extract', 'transform', 'load')
            batch_num: Current batch number (1-indexed)
            records_processed: Total records processed so far
            records_total: Total records expected (None if unknown)
            total_batches: Total batches expected (None if unknown)
            memory_usage_mb: Current memory usage in MB (None if not tracked)
            error_count: Number of errors encountered so far
        """
        if not self.start_time:
            self.start_time = datetime.now()
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        # Estimate remaining time based on average batch processing time
        estimated_remaining = None
        if self.last_batch_times and records_total:
            avg_batch_time = sum(self.last_batch_times) / len(self.last_batch_times)
            remaining_records = records_total - records_processed
            if records_processed > 0:
                records_per_batch = records_processed / batch_num
                remaining_batches = remaining_records / records_per_batch if records_per_batch > 0 else 0
                estimated_remaining = avg_batch_time * remaining_batches
        
        progress = ETLProgress(
            stage=stage,
            batch_num=batch_num,
            total_batches=total_batches,
            records_processed=records_processed,
            records_total=records_total,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=estimated_remaining,
            memory_usage_mb=memory_usage_mb,
            error_count=error_count,
        )
        
        # Call callback if provided
        if self.callback:
            try:
                self.callback(progress)
            except Exception as e:
                # Don't let callback errors break the pipeline
                pass
        
        # Print if verbose
        if self.verbose:
            print(str(progress))
    
    def record_batch_time(self, batch_time_seconds: float):
        """Record batch processing time for estimation."""
        self.last_batch_times.append(batch_time_seconds)
        if len(self.last_batch_times) > self.max_batch_times:
            self.last_batch_times.pop(0)
    
    def reset_stage(self):
        """Reset stage start time (for multi-stage tracking)."""
        self.stage_start_time = datetime.now()

