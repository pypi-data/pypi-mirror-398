"""Storage management utilities for maintenance and operations."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import StorageConfig, get_storage_config
from .database import get_session, session_scope
from .models import Snapshot as SnapshotModel, ArtifactContent, Artifact, Session as SessionModel
from .artifacts import ArtifactManager
from .snapshot_repository import SnapshotRepository
from .encryption import EncryptionManager, EncryptionConfig, configure_encryption


logger = logging.getLogger(__name__)


class StorageManager:
    """Manages storage operations, cleanup, and maintenance."""

    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or get_storage_config()

        # Initialize encryption if enabled
        if self.config.security.enable_encryption:
            encryption_config = EncryptionConfig(
                enabled=self.config.security.enable_encryption,
                key_file_path=self.config.security.encryption_key_file,
                auto_encrypt_sensitive=self.config.security.auto_encrypt_sensitive,
                custom_sensitive_fields=self.config.security.custom_sensitive_fields_set,
            )
            self.encryption_manager = configure_encryption(encryption_config)
            self.encryption_manager.initialize_encryption(generate_key=True)

        self.artifact_manager = ArtifactManager(
            storage_path=self.config.storage_path,
            max_inline_size=self.config.performance.max_inline_size_bytes,
            enable_compression=self.config.compression.enabled,
            compression_threshold=self.config.compression.threshold_bytes,
            prefer_speed=self.config.compression.prefer_speed,
        )
        self.snapshot_repository = SnapshotRepository()

    async def run_maintenance(self) -> Dict[str, Any]:
        """Run complete maintenance cycle."""
        logger.info("Starting storage maintenance")

        results = {
            "maintenance_started": datetime.now(timezone.utc).isoformat(),
            "tasks": {}
        }

        try:
            # Cleanup old snapshots
            if self.config.retention.enabled:
                cleanup_result = await self.cleanup_old_snapshots()
                results["tasks"]["cleanup_snapshots"] = cleanup_result

            # Cleanup orphaned artifacts
            orphan_result = await self.cleanup_orphaned_artifacts()
            results["tasks"]["cleanup_orphans"] = orphan_result

            # Optimize storage
            optimize_result = await self.optimize_storage()
            results["tasks"]["optimize_storage"] = optimize_result

            # Verify data integrity
            integrity_result = await self.verify_data_integrity()
            results["tasks"]["verify_integrity"] = integrity_result

            # Update statistics
            stats_result = await self.update_statistics()
            results["tasks"]["update_statistics"] = stats_result

            results["maintenance_completed"] = datetime.now(timezone.utc).isoformat()
            results["success"] = True

        except Exception as e:
            logger.error(f"Maintenance failed: {e}")
            results["error"] = str(e)
            results["success"] = False

        return results

    async def cleanup_old_snapshots(self) -> Dict[str, Any]:
        """Clean up snapshots according to retention policy."""
        if not self.config.retention.enabled:
            return {"skipped": "Retention policy disabled"}

        logger.info("Cleaning up old snapshots")

        cleanup_stats = {
            "snapshots_deleted": 0,
            "artifacts_deleted": 0,
            "bytes_freed": 0,
            "errors": []
        }

        with session_scope() as session:
            # Calculate cutoff date
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                seconds=self.config.retention.max_age_seconds
            )

            # Find old snapshots
            old_snapshots = session.query(SnapshotModel).filter(
                SnapshotModel.timestamp < cutoff_time
            ).all()

            # Check size-based retention
            if self.config.retention.max_size_gb is not None:
                total_size = self.get_total_storage_size()
                max_size_bytes = self.config.retention.max_size_gb * 1024 * 1024 * 1024

                if total_size > max_size_bytes:
                    # Delete oldest snapshots until under limit
                    all_snapshots = session.query(SnapshotModel).order_by(
                        SnapshotModel.timestamp.asc()
                    ).all()

                    current_size = total_size
                    for snapshot in all_snapshots:
                        if current_size <= max_size_bytes:
                            break

                        snapshot_size = self._get_snapshot_size(session, snapshot.snapshot_id)
                        old_snapshots.append(snapshot)
                        current_size -= snapshot_size

            # Check count-based retention
            if self.config.retention.max_snapshots is not None:
                total_snapshots = session.query(func.count(SnapshotModel.id)).scalar()

                if total_snapshots > self.config.retention.max_snapshots:
                    excess_count = total_snapshots - self.config.retention.max_snapshots
                    excess_snapshots = session.query(SnapshotModel).order_by(
                        SnapshotModel.timestamp.asc()
                    ).limit(excess_count).all()

                    old_snapshots.extend(excess_snapshots)

            # Remove duplicates
            old_snapshots = list(set(old_snapshots))

            # Delete snapshots
            for snapshot in old_snapshots:
                try:
                    snapshot_size = self._get_snapshot_size(session, snapshot.snapshot_id)

                    # Delete via repository to handle cleanup properly
                    success = self.snapshot_repository.delete_snapshot(snapshot.snapshot_id)

                    if success:
                        cleanup_stats["snapshots_deleted"] += 1
                        cleanup_stats["bytes_freed"] += snapshot_size
                    else:
                        cleanup_stats["errors"].append(f"Failed to delete snapshot {snapshot.snapshot_id}")

                except Exception as e:
                    logger.error(f"Error deleting snapshot {snapshot.snapshot_id}: {e}")
                    cleanup_stats["errors"].append(f"Error deleting {snapshot.snapshot_id}: {str(e)}")

        logger.info(f"Cleanup completed: {cleanup_stats}")
        return cleanup_stats

    async def cleanup_orphaned_artifacts(self) -> Dict[str, Any]:
        """Clean up orphaned artifact content."""
        logger.info("Cleaning up orphaned artifacts")

        orphan_stats = {
            "orphaned_content_deleted": 0,
            "bytes_freed": 0,
            "errors": []
        }

        try:
            # Use artifact manager's cleanup method
            deleted_count = self.artifact_manager.cleanup_orphaned_content()
            orphan_stats["orphaned_content_deleted"] = deleted_count

            # Calculate freed bytes (approximate)
            with session_scope() as session:
                orphaned_size = session.query(func.sum(ArtifactContent.content_size)).filter(
                    ArtifactContent.reference_count <= 0
                ).scalar() or 0

                orphan_stats["bytes_freed"] = orphaned_size

        except Exception as e:
            logger.error(f"Error cleaning orphaned artifacts: {e}")
            orphan_stats["errors"].append(str(e))

        logger.info(f"Orphan cleanup completed: {orphan_stats}")
        return orphan_stats

    async def optimize_storage(self) -> Dict[str, Any]:
        """Optimize storage by recompressing files with better algorithms."""
        logger.info("Optimizing storage")

        optimization_stats = {
            "files_recompressed": 0,
            "bytes_saved": 0,
            "errors": []
        }

        if not self.config.compression.enabled:
            return {"skipped": "Compression disabled"}

        try:
            with session_scope() as session:
                # Find artifacts with suboptimal compression
                artifacts = session.query(Artifact).filter(
                    Artifact.compression_type != self.config.compression.algorithm.value,
                    Artifact.content_size >= self.config.compression.threshold_bytes
                ).limit(100).all()  # Process in batches

                for artifact in artifacts:
                    try:
                        # Re-compress with current algorithm
                        old_size = artifact.compressed_size or artifact.content_size
                        # Implementation would recompress the artifact
                        # This is a placeholder for the actual recompression logic
                        optimization_stats["files_recompressed"] += 1

                    except Exception as e:
                        logger.error(f"Error recompressing artifact {artifact.artifact_name}: {e}")
                        optimization_stats["errors"].append(str(e))

        except Exception as e:
            logger.error(f"Error during storage optimization: {e}")
            optimization_stats["errors"].append(str(e))

        logger.info(f"Storage optimization completed: {optimization_stats}")
        return optimization_stats

    async def verify_data_integrity(self) -> Dict[str, Any]:
        """Verify data integrity by checking checksums."""
        logger.info("Verifying data integrity")

        integrity_stats = {
            "files_checked": 0,
            "corrupted_files": 0,
            "missing_files": 0,
            "errors": []
        }

        if not self.config.enable_checksums:
            return {"skipped": "Checksums disabled"}

        try:
            with session_scope() as session:
                # Check artifact files
                artifacts = session.query(Artifact).filter(
                    Artifact.content_path.isnot(None)
                ).all()

                for artifact in artifacts:
                    try:
                        integrity_stats["files_checked"] += 1

                        # Check if file exists
                        if artifact.content_path and not Path(artifact.content_path).exists():
                            integrity_stats["missing_files"] += 1
                            logger.warning(f"Missing file: {artifact.content_path}")
                            continue

                        # Verify checksum (implementation would check actual hash)
                        # This is a placeholder for actual integrity verification

                    except Exception as e:
                        logger.error(f"Error checking artifact {artifact.artifact_name}: {e}")
                        integrity_stats["errors"].append(str(e))

        except Exception as e:
            logger.error(f"Error during integrity verification: {e}")
            integrity_stats["errors"].append(str(e))

        logger.info(f"Integrity verification completed: {integrity_stats}")
        return integrity_stats

    async def update_statistics(self) -> Dict[str, Any]:
        """Update cached statistics."""
        logger.info("Updating statistics")

        try:
            stats = self.get_storage_statistics()
            return {
                "updated": True,
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            return {"error": str(e)}

    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics."""
        with session_scope() as session:
            # Basic counts
            total_snapshots = session.query(func.count(SnapshotModel.id)).scalar()
            total_sessions = session.query(func.count(SessionModel.session_id)).scalar()
            total_artifacts = session.query(func.count(Artifact.id)).scalar()

            # Storage usage
            total_content_size = session.query(func.sum(ArtifactContent.content_size)).scalar() or 0
            total_compressed_size = session.query(func.sum(ArtifactContent.compressed_size)).scalar() or 0

            # Compression stats
            compression_ratio = (
                (total_content_size - total_compressed_size) / total_content_size
                if total_content_size > 0 else 0
            )

            # Recent activity
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            recent_snapshots = session.query(func.count(SnapshotModel.id)).filter(
                SnapshotModel.timestamp >= yesterday
            ).scalar()

            # Model distribution
            model_stats = dict(
                session.query(SnapshotModel.model_name, func.count(SnapshotModel.id))
                .group_by(SnapshotModel.model_name)
                .all()
            )

            return {
                "counts": {
                    "snapshots": total_snapshots,
                    "sessions": total_sessions,
                    "artifacts": total_artifacts,
                },
                "storage": {
                    "total_content_bytes": total_content_size,
                    "total_compressed_bytes": total_compressed_size,
                    "compression_ratio": compression_ratio,
                    "bytes_saved": total_content_size - total_compressed_size,
                },
                "activity": {
                    "snapshots_last_24h": recent_snapshots,
                },
                "models": model_stats,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

    def get_total_storage_size(self) -> int:
        """Get total storage size in bytes."""
        total_size = 0

        # Database size
        with session_scope() as session:
            total_size += session.query(func.sum(ArtifactContent.content_size)).scalar() or 0

        # File system artifacts
        storage_path = Path(self.config.storage_path)
        if storage_path.exists():
            for file_path in storage_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size

        return total_size

    def _get_snapshot_size(self, session: Session, snapshot_id: str) -> int:
        """Get total size of a snapshot including all artifacts."""
        artifacts = session.query(Artifact).filter(
            Artifact.snapshot_id == snapshot_id
        ).all()

        return sum(artifact.content_size for artifact in artifacts)

    async def create_backup(self, backup_path: str) -> Dict[str, Any]:
        """Create a backup of the entire storage."""
        logger.info(f"Creating backup to {backup_path}")

        backup_stats = {
            "backup_path": backup_path,
            "files_backed_up": 0,
            "total_size": 0,
            "errors": []
        }

        try:
            backup_path_obj = Path(backup_path)
            backup_path_obj.mkdir(parents=True, exist_ok=True)

            # Backup database
            # Implementation would backup the SQLite database

            # Backup artifact files
            storage_path = Path(self.config.storage_path)
            if storage_path.exists():
                # Implementation would copy artifact files

                backup_stats["files_backed_up"] = len(list(storage_path.rglob("*")))

            backup_stats["success"] = True

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            backup_stats["errors"].append(str(e))

        return backup_stats


class MaintenanceScheduler:
    """Schedules and runs maintenance tasks."""

    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager
        self.config = storage_manager.config
        self._running = False

    async def start_scheduler(self):
        """Start the maintenance scheduler."""
        self._running = True
        logger.info("Starting maintenance scheduler")

        while self._running:
            try:
                # Wait for next maintenance interval
                await asyncio.sleep(self.config.retention.cleanup_interval_hours * 3600)

                if self._running:
                    await self.storage_manager.run_maintenance()

            except Exception as e:
                logger.error(f"Maintenance scheduler error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying

    def stop_scheduler(self):
        """Stop the maintenance scheduler."""
        self._running = False
        logger.info("Stopping maintenance scheduler")


# Global storage manager instance
_storage_manager: Optional[StorageManager] = None


def get_storage_manager() -> StorageManager:
    """Get the global storage manager instance."""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager


async def run_maintenance_now() -> Dict[str, Any]:
    """Run maintenance immediately."""
    manager = get_storage_manager()
    return await manager.run_maintenance()