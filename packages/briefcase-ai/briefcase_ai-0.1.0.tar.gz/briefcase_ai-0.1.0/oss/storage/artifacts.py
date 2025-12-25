"""Artifact management with content deduplication and storage."""

import os
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, BinaryIO
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from .database import get_session
from .models import Artifact, ArtifactContent
from .compression import CompressionManager, CompressionType, compress_data, decompress_data


class ArtifactManager:
    """Manages artifact storage with content deduplication."""

    def __init__(
        self,
        storage_path: Optional[str] = None,
        max_inline_size: int = 1024 * 1024,  # 1MB
        session: Optional[Session] = None,
        enable_compression: bool = True,
        compression_threshold: int = 4096,  # 4KB
        prefer_speed: bool = False,
    ):
        self.storage_path = Path(storage_path or "./artifacts")
        self.max_inline_size = max_inline_size
        self._session = session
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold
        self.prefer_speed = prefer_speed
        self.compression_manager = CompressionManager()
        self._ensure_storage_directory()

    def _get_session(self) -> Session:
        """Get session, either provided or create new one."""
        return self._session or get_session()

    def _ensure_storage_directory(self) -> None:
        """Ensure artifact storage directory exists."""
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def store_artifact(
        self,
        snapshot_id: str,
        name: str,
        content: Union[bytes, str, BinaryIO],
        artifact_type: str = "file",
        metadata: Optional[Dict[str, Any]] = None,
        content_type: Optional[str] = None,
    ) -> Artifact:
        """Store an artifact with automatic deduplication."""
        # Convert content to bytes if needed
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        elif hasattr(content, 'read'):
            content_bytes = content.read()
            if hasattr(content, 'seek'):
                content.seek(0)  # Reset position for potential reuse
        else:
            content_bytes = content

        # Compute content hash for deduplication
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        content_size = len(content_bytes)

        session = self._get_session()
        try:
            # Check if content already exists
            existing_content = session.query(ArtifactContent).filter(
                ArtifactContent.content_hash == content_hash
            ).first()

            if existing_content:
                # Increment reference count
                existing_content.reference_count += 1
                content_storage_path = existing_content.file_path
                content_data = existing_content.content_data
                compression_type_str = existing_content.compression_type
                compression_ratio = existing_content.compression_ratio
            else:
                # Store new content
                content_storage_path, content_data, compression_type, compression_ratio = self._store_content(
                    content_bytes, content_hash, content_size, content_type
                )
                compression_type_str = compression_type.value

                # Create content record
                artifact_content = ArtifactContent(
                    content_hash=content_hash,
                    content_size=content_size,
                    content_type=content_type,
                    content_data=content_data,
                    file_path=content_storage_path,
                    compression_type=compression_type_str,
                    compressed_size=len(content_data) if content_data else (
                        Path(content_storage_path).stat().st_size if content_storage_path else content_size
                    ),
                    compression_ratio=compression_ratio,
                )
                session.add(artifact_content)

            # Create artifact record
            compressed_size = len(content_data) if content_data else (
                Path(content_storage_path).stat().st_size if content_storage_path else content_size
            )

            artifact = Artifact(
                snapshot_id=snapshot_id,
                artifact_name=name,
                artifact_type=artifact_type,
                content_hash=content_hash,
                content_size=content_size,
                content_path=content_storage_path,
                content_data=content_data if content_size <= self.max_inline_size else None,
                artifact_metadata=metadata or {},
                is_external=False,
                compression_type=compression_type_str,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
            )

            session.add(artifact)

            if self._session is None:
                session.commit()

            return artifact

        except IntegrityError as e:
            if self._session is None:
                session.rollback()
            raise ValueError(f"Artifact {name} already exists for snapshot {snapshot_id}") from e
        finally:
            if self._session is None:
                session.close()

    def store_external_artifact(
        self,
        snapshot_id: str,
        name: str,
        external_path: str,
        artifact_type: str = "external_file",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        """Store reference to external artifact without copying content."""
        # Get file info without reading content
        path = Path(external_path)
        if not path.exists():
            raise FileNotFoundError(f"External artifact not found: {external_path}")

        content_size = path.stat().st_size

        # Use path as hash basis for external files
        path_hash = hashlib.sha256(str(path.absolute()).encode()).hexdigest()

        session = self._get_session()
        try:
            artifact = Artifact(
                snapshot_id=snapshot_id,
                artifact_name=name,
                artifact_type=artifact_type,
                content_hash=path_hash,
                content_size=content_size,
                content_path=str(path.absolute()),
                content_data=None,
                artifact_metadata=metadata or {},
                is_external=True,
            )

            session.add(artifact)

            if self._session is None:
                session.commit()

            return artifact

        except IntegrityError as e:
            if self._session is None:
                session.rollback()
            raise ValueError(f"Artifact {name} already exists for snapshot {snapshot_id}") from e
        finally:
            if self._session is None:
                session.close()

    def get_artifact(self, snapshot_id: str, name: str) -> Optional[Artifact]:
        """Get artifact by snapshot and name."""
        session = self._get_session()
        try:
            return session.query(Artifact).filter(
                Artifact.snapshot_id == snapshot_id,
                Artifact.artifact_name == name,
            ).first()
        finally:
            if self._session is None:
                session.close()

    def get_artifacts(self, snapshot_id: str) -> List[Artifact]:
        """Get all artifacts for a snapshot."""
        session = self._get_session()
        try:
            return session.query(Artifact).filter(
                Artifact.snapshot_id == snapshot_id
            ).all()
        finally:
            if self._session is None:
                session.close()

    def get_artifact_content(self, artifact: Artifact) -> bytes:
        """Retrieve and decompress artifact content."""
        if artifact.is_external:
            # Read external file (no decompression for external files)
            if not artifact.content_path:
                raise ValueError("External artifact has no path")

            path = Path(artifact.content_path)
            if not path.exists():
                raise FileNotFoundError(f"External artifact not found: {artifact.content_path}")

            return path.read_bytes()

        # Get raw content first
        raw_content = None

        # Check inline content first
        if artifact.content_data:
            raw_content = artifact.content_data
        # Read from file storage
        elif artifact.content_path:
            path = Path(artifact.content_path)
            if path.exists():
                raw_content = path.read_bytes()
        else:
            # Try to get from deduplicated storage
            session = self._get_session()
            try:
                content_record = session.query(ArtifactContent).filter(
                    ArtifactContent.content_hash == artifact.content_hash
                ).first()

                if content_record:
                    if content_record.content_data:
                        raw_content = content_record.content_data
                    elif content_record.file_path:
                        path = Path(content_record.file_path)
                        if path.exists():
                            raw_content = path.read_bytes()

                if raw_content is None:
                    raise FileNotFoundError(f"Content for artifact {artifact.artifact_name} not found")
            finally:
                if self._session is None:
                    session.close()

        if raw_content is None:
            raise FileNotFoundError(f"Content for artifact {artifact.artifact_name} not found")

        # Decompress if needed
        compression_type_str = getattr(artifact, 'compression_type', 'none')
        if compression_type_str and compression_type_str != 'none':
            try:
                compression_type = CompressionType(compression_type_str)
                return decompress_data(raw_content, compression_type)
            except Exception as e:
                raise RuntimeError(f"Failed to decompress artifact {artifact.artifact_name}: {e}")

        return raw_content

    def delete_artifact(self, snapshot_id: str, name: str) -> bool:
        """Delete an artifact and clean up unreferenced content."""
        session = self._get_session()
        try:
            artifact = session.query(Artifact).filter(
                Artifact.snapshot_id == snapshot_id,
                Artifact.artifact_name == name,
            ).first()

            if not artifact:
                return False

            content_hash = artifact.content_hash
            session.delete(artifact)

            # Decrement content reference count if not external
            if not artifact.is_external:
                content_record = session.query(ArtifactContent).filter(
                    ArtifactContent.content_hash == content_hash
                ).first()

                if content_record:
                    content_record.reference_count -= 1

                    # Clean up unreferenced content
                    if content_record.reference_count <= 0:
                        if content_record.file_path:
                            path = Path(content_record.file_path)
                            if path.exists():
                                path.unlink()
                        session.delete(content_record)

            if self._session is None:
                session.commit()
            return True

        except Exception:
            if self._session is None:
                session.rollback()
            raise
        finally:
            if self._session is None:
                session.close()

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        session = self._get_session()
        try:
            # Artifact counts by type
            artifact_counts = dict(
                session.query(Artifact.artifact_type, func.count(Artifact.id))
                .group_by(Artifact.artifact_type)
                .all()
            )

            # Total storage used
            total_size = session.query(
                func.coalesce(func.sum(ArtifactContent.content_size), 0)
            ).scalar()

            # Deduplication stats
            unique_contents = session.query(func.count(ArtifactContent.content_hash)).scalar()
            total_artifacts = session.query(func.count(Artifact.id)).scalar()

            deduplication_ratio = (
                (total_artifacts - unique_contents) / total_artifacts
                if total_artifacts > 0 else 0
            )

            return {
                "artifact_counts": artifact_counts,
                "total_size_bytes": total_size,
                "unique_contents": unique_contents,
                "total_artifacts": total_artifacts,
                "deduplication_ratio": deduplication_ratio,
                "storage_path": str(self.storage_path),
            }
        finally:
            if self._session is None:
                session.close()

    def cleanup_orphaned_content(self) -> int:
        """Clean up content with zero references."""
        session = self._get_session()
        try:
            orphaned = session.query(ArtifactContent).filter(
                ArtifactContent.reference_count <= 0
            ).all()

            count = 0
            for content in orphaned:
                if content.file_path:
                    path = Path(content.file_path)
                    if path.exists():
                        path.unlink()
                session.delete(content)
                count += 1

            if self._session is None:
                session.commit()
            return count

        except Exception:
            if self._session is None:
                session.rollback()
            raise
        finally:
            if self._session is None:
                session.close()

    def _store_content(
        self,
        content: bytes,
        content_hash: str,
        content_size: int,
        content_type: Optional[str],
    ) -> tuple[Optional[str], Optional[bytes], CompressionType, Optional[float]]:
        """Store content based on size threshold with optional compression."""
        compression_type = CompressionType.NONE
        compression_ratio = None

        # Apply compression if enabled and content meets threshold
        final_content = content
        if self.enable_compression and content_size >= self.compression_threshold:
            try:
                compressed_data, compression_type, compression_ratio = compress_data(
                    content, prefer_speed=self.prefer_speed
                )

                # Only use compressed data if it's actually smaller
                if len(compressed_data) < content_size:
                    final_content = compressed_data
                else:
                    compression_type = CompressionType.NONE
                    compression_ratio = None
            except Exception:
                # Fall back to no compression on error
                compression_type = CompressionType.NONE
                compression_ratio = None

        if len(final_content) <= self.max_inline_size:
            # Store inline in database
            return None, final_content, compression_type, compression_ratio
        else:
            # Store in file system
            file_path = self._get_storage_path(content_hash, compression_type)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(final_content)
            return str(file_path), None, compression_type, compression_ratio

    def _get_storage_path(self, content_hash: str, compression_type: CompressionType = CompressionType.NONE) -> Path:
        """Get file storage path for content hash with compression extension."""
        # Use first 2 characters as subdirectory for better filesystem performance
        subdir = content_hash[:2]
        extension = self.compression_manager.get_recommended_extension(compression_type)
        filename = f"{content_hash}.bin{extension}"
        return self.storage_path / subdir / filename


def get_artifact_manager(
    storage_path: Optional[str] = None,
    max_inline_size: int = 1024 * 1024,
    enable_compression: bool = True,
    compression_threshold: int = 4096,
    prefer_speed: bool = False,
) -> ArtifactManager:
    """Get a configured artifact manager instance."""
    return ArtifactManager(
        storage_path=storage_path,
        max_inline_size=max_inline_size,
        enable_compression=enable_compression,
        compression_threshold=compression_threshold,
        prefer_speed=prefer_speed,
    )
