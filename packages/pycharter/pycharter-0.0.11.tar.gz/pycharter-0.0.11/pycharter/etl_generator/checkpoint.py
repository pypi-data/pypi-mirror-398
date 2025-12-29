"""
Checkpoint and resume functionality for ETL pipelines.

This module provides checkpoint/resume capabilities for long-running ETL jobs,
allowing them to recover from failures and resume from the last successful point.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CheckpointState:
    """State information saved in a checkpoint."""
    
    checkpoint_id: str
    timestamp: str
    stage: str  # 'extract', 'transform', 'load'
    batch_num: int
    records_processed: int
    last_processed_params: Dict[str, Any]
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointState":
        """Create from dictionary."""
        return cls(**data)


class CheckpointManager:
    """Manages checkpoint creation and restoration."""
    
    def __init__(self, checkpoint_dir: Optional[str] = None):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory to store checkpoints (None = disabled)
        """
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None
        if self.checkpoint_dir:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save(
        self,
        checkpoint_id: str,
        stage: str,
        batch_num: int,
        records_processed: int,
        last_processed_params: Dict[str, Any],
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """
        Save checkpoint state.
        
        Args:
            checkpoint_id: Unique identifier for this checkpoint
            stage: Current stage
            batch_num: Current batch number
            records_processed: Total records processed
            last_processed_params: Parameters used for last successful processing
            error: Error message if checkpointing after failure
            metadata: Additional metadata to save
        
        Returns:
            Path to saved checkpoint file, or None if checkpointing disabled
        """
        if not self.checkpoint_dir:
            return None
        
        state = CheckpointState(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now().isoformat(),
            stage=stage,
            batch_num=batch_num,
            records_processed=records_processed,
            last_processed_params=last_processed_params,
            error=error,
            metadata=metadata or {},
        )
        
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        checkpoint_path.write_text(json.dumps(state.to_dict(), indent=2))
        
        return checkpoint_path
    
    def load(self, checkpoint_id: str) -> Optional[CheckpointState]:
        """
        Load checkpoint state.
        
        Args:
            checkpoint_id: Checkpoint identifier
        
        Returns:
            CheckpointState if found, None otherwise
        """
        if not self.checkpoint_dir:
            return None
        
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        if not checkpoint_path.exists():
            return None
        
        try:
            data = json.loads(checkpoint_path.read_text())
            return CheckpointState.from_dict(data)
        except Exception:
            return None
    
    def delete(self, checkpoint_id: str) -> bool:
        """
        Delete checkpoint.
        
        Args:
            checkpoint_id: Checkpoint identifier
        
        Returns:
            True if deleted, False if not found
        """
        if not self.checkpoint_dir:
            return False
        
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            return True
        return False
    
    def list_checkpoints(self) -> list[str]:
        """
        List all checkpoint IDs.
        
        Returns:
            List of checkpoint IDs
        """
        if not self.checkpoint_dir:
            return []
        
        return [
            path.stem
            for path in self.checkpoint_dir.glob("*.json")
        ]

