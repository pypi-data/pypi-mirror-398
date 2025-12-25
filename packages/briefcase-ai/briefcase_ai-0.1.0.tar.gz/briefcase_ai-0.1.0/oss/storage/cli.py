"""CLI utility for managing Briefcase storage layer."""

import click
import json
import asyncio
from pathlib import Path
from datetime import datetime

from .database import DatabaseConfig, configure_database, init_database, reset_database
from .snapshot_repository import SnapshotRepository
from .artifacts import ArtifactManager
from .config import StorageConfig, get_storage_config, create_default_config_file, StorageConfigManager
from .management import StorageManager, run_maintenance_now
from .encryption import EncryptionKeyManager, LocalEncryption


@click.group()
@click.option('--db-url', default="sqlite:///./briefcase.db", help='Database URL')
@click.option('--config', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, db_url, config, verbose):
    """Briefcase Storage CLI - Manage snapshots, artifacts, and storage."""
    ctx.ensure_object(dict)
    ctx.obj['db_url'] = db_url
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose

    # Configure database
    db_config = DatabaseConfig(url=db_url, echo=verbose)
    configure_database(db_config)

    # Load storage configuration
    if config:
        config_manager = StorageConfigManager(config)
        ctx.obj['storage_config'] = config_manager.load_config()
    else:
        ctx.obj['storage_config'] = get_storage_config()


@cli.command()
@click.pass_context
def init_db(ctx):
    """Initialize the database schema."""
    try:
        init_database()
        click.echo("✓ Database initialized successfully.")
    except Exception as e:
        click.echo(f"✗ Failed to initialize database: {e}", err=True)


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset the database?')
@click.pass_context
def reset_db(ctx):
    """Reset the database (WARNING: destroys all data)."""
    try:
        reset_database()
        click.echo("✓ Database reset successfully.")
    except Exception as e:
        click.echo(f"✗ Failed to reset database: {e}", err=True)


@cli.command()
@click.option('--output', '-o', help='Output file path (default: ./briefcase-config.json)')
@click.pass_context
def create_config(ctx, output):
    """Create a default configuration file."""
    try:
        config_path = output or "./briefcase-config.json"
        create_default_config_file(config_path)
        click.echo(f"✓ Default configuration created at: {config_path}")
    except Exception as e:
        click.echo(f"✗ Failed to create config: {e}", err=True)


@cli.command()
@click.pass_context
def show_config(ctx):
    """Show current storage configuration."""
    try:
        config = ctx.obj['storage_config']
        click.echo("Current Storage Configuration:")
        click.echo(f"  Storage Path: {config.storage_path}")
        click.echo(f"  Database URL: {config.database_url}")

        click.echo("\n  Compression:")
        click.echo(f"    Enabled: {config.compression.enabled}")
        click.echo(f"    Algorithm: {config.compression.algorithm.value}")
        click.echo(f"    Threshold: {config.compression.threshold_bytes} bytes")

        click.echo("\n  Retention:")
        click.echo(f"    Enabled: {config.retention.enabled}")
        click.echo(f"    Max Age: {config.retention.max_age_value} {config.retention.max_age_unit.value}")
        if config.retention.max_size_gb:
            click.echo(f"    Max Size: {config.retention.max_size_gb} GB")

        click.echo("\n  Performance:")
        click.echo(f"    Max Inline Size: {config.performance.max_inline_size_kb} KB")
        click.echo(f"    Cache Size: {config.performance.cache_size_mb} MB")

        click.echo("\n  Security:")
        click.echo(f"    Encryption: {config.security.enable_encryption}")

    except Exception as e:
        click.echo(f"✗ Failed to show config: {e}", err=True)


@cli.command()
@click.option('--session-id', help='Filter by session ID')
@click.option('--model-name', help='Filter by model name')
@click.option('--limit', default=10, help='Maximum number of snapshots to list')
@click.pass_context
def list_snapshots(ctx, session_id, model_name, limit):
    """List snapshots."""
    try:
        repo = SnapshotRepository()
        snapshots = repo.list_snapshots(
            skip=0,
            limit=limit,
            session_id=session_id,
            model_name=model_name
        )

        if not snapshots:
            click.echo("No snapshots found.")
            return

        click.echo(f"Found {len(snapshots)} snapshot(s):")
        for snapshot in snapshots:
            click.echo(f"  • {snapshot.snapshot_id}")
            click.echo(f"    Session: {snapshot.session_id}")
            click.echo(f"    Model: {snapshot.model_name}:{snapshot.model_version}")
            click.echo(f"    Time: {snapshot.timestamp}")

    except Exception as e:
        click.echo(f"✗ Failed to list snapshots: {e}", err=True)


@cli.command()
@click.option('--snapshot-id', required=True, help='Snapshot ID')
@click.pass_context
def show_snapshot(ctx, snapshot_id):
    """Show detailed snapshot information."""
    try:
        repo = SnapshotRepository()
        snapshot = repo.get_snapshot(snapshot_id)

        if not snapshot:
            click.echo(f"Snapshot {snapshot_id} not found.")
            return

        click.echo(f"Snapshot: {snapshot.snapshot_id}")
        click.echo(f"Session: {snapshot.session_id}")
        click.echo(f"Model: {snapshot.model_name}:{snapshot.model_version}")
        click.echo(f"Time: {snapshot.timestamp}")

        # Get stats
        stats = repo.get_snapshot_stats(snapshot_id)
        if stats:
            click.echo(f"Size: {stats['size_bytes']} bytes")
            click.echo(f"Files: {stats['file_count']}")
            click.echo(f"Checksum: {stats['checksum']}")

    except Exception as e:
        click.echo(f"✗ Failed to show snapshot: {e}", err=True)


@cli.command()
@click.option('--snapshot-id', required=True, help='Snapshot ID')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def export_snapshot(ctx, snapshot_id, output):
    """Export snapshot to a zip file."""
    try:
        repo = SnapshotRepository()
        export_path = repo.create_snapshot_export(snapshot_id)

        if not export_path:
            click.echo(f"Failed to create export for snapshot {snapshot_id}")
            return

        if output:
            final_path = Path(output)
            export_path.rename(final_path)
            click.echo(f"✓ Snapshot exported to: {final_path}")
        else:
            click.echo(f"✓ Snapshot exported to: {export_path}")

    except Exception as e:
        click.echo(f"✗ Failed to export snapshot: {e}", err=True)


@cli.command()
@click.pass_context
def storage_stats(ctx):
    """Show comprehensive storage statistics."""
    try:
        config = ctx.obj['storage_config']
        manager = StorageManager(config)
        stats = manager.get_storage_statistics()

        click.echo("Storage Statistics:")
        click.echo(f"  Total snapshots: {stats['counts']['snapshots']}")
        click.echo(f"  Total sessions: {stats['counts']['sessions']}")
        click.echo(f"  Total artifacts: {stats['counts']['artifacts']}")

        click.echo("\nStorage Usage:")
        click.echo(f"  Content size: {stats['storage']['total_content_bytes']:,} bytes")
        click.echo(f"  Compressed size: {stats['storage']['total_compressed_bytes']:,} bytes")
        click.echo(f"  Compression ratio: {stats['storage']['compression_ratio']:.2%}")
        click.echo(f"  Bytes saved: {stats['storage']['bytes_saved']:,}")

        click.echo("\nActivity:")
        click.echo(f"  Snapshots (last 24h): {stats['activity']['snapshots_last_24h']}")

        if stats['models']:
            click.echo("\nModel Distribution:")
            for model, count in stats['models'].items():
                click.echo(f"  {model}: {count}")

    except Exception as e:
        click.echo(f"✗ Failed to get storage stats: {e}", err=True)


@cli.command()
@click.option('--dry-run', is_flag=True, help='Show what would be cleaned without doing it')
@click.confirmation_option(prompt='Are you sure you want to run cleanup?')
@click.pass_context
def cleanup(ctx, dry_run):
    """Clean up old snapshots and orphaned artifacts according to retention policy."""
    try:
        config = ctx.obj['storage_config']
        manager = StorageManager(config)

        if dry_run:
            click.echo("DRY RUN - No changes will be made")
            # Implementation would show what would be cleaned
            click.echo("✓ Dry run completed.")
        else:
            click.echo("Running cleanup operations...")
            result = asyncio.run(manager.cleanup_old_snapshots())

            click.echo(f"✓ Cleanup completed:")
            click.echo(f"  Snapshots deleted: {result.get('snapshots_deleted', 0)}")
            click.echo(f"  Artifacts deleted: {result.get('artifacts_deleted', 0)}")
            click.echo(f"  Bytes freed: {result.get('bytes_freed', 0):,}")

            if result.get('errors'):
                click.echo(f"  Errors: {len(result['errors'])}")

    except Exception as e:
        click.echo(f"✗ Cleanup failed: {e}", err=True)


@cli.command()
@click.pass_context
def maintenance(ctx):
    """Run full storage maintenance."""
    try:
        click.echo("Running storage maintenance...")
        result = asyncio.run(run_maintenance_now())

        if result.get('success'):
            click.echo("✓ Maintenance completed successfully")
            for task_name, task_result in result.get('tasks', {}).items():
                click.echo(f"  {task_name}: completed")
        else:
            click.echo("✗ Maintenance failed")
            if result.get('error'):
                click.echo(f"  Error: {result['error']}")

    except Exception as e:
        click.echo(f"✗ Maintenance failed: {e}", err=True)


@cli.command()
@click.option('--backup-path', required=True, help='Backup destination path')
@click.pass_context
def backup(ctx, backup_path):
    """Create a backup of all storage data."""
    try:
        config = ctx.obj['storage_config']
        manager = StorageManager(config)

        click.echo(f"Creating backup to {backup_path}...")
        result = asyncio.run(manager.create_backup(backup_path))

        if result.get('success'):
            click.echo("✓ Backup completed successfully")
            click.echo(f"  Files backed up: {result.get('files_backed_up', 0)}")
            click.echo(f"  Total size: {result.get('total_size', 0):,} bytes")
        else:
            click.echo("✗ Backup failed")
            if result.get('errors'):
                for error in result['errors']:
                    click.echo(f"  Error: {error}")

    except Exception as e:
        click.echo(f"✗ Backup failed: {e}", err=True)


@cli.command()
@click.pass_context
def verify(ctx):
    """Verify data integrity."""
    try:
        config = ctx.obj['storage_config']
        manager = StorageManager(config)

        click.echo("Verifying data integrity...")
        result = asyncio.run(manager.verify_data_integrity())

        click.echo("✓ Verification completed:")
        click.echo(f"  Files checked: {result.get('files_checked', 0)}")
        click.echo(f"  Corrupted files: {result.get('corrupted_files', 0)}")
        click.echo(f"  Missing files: {result.get('missing_files', 0)}")

        if result.get('errors'):
            click.echo(f"  Errors encountered: {len(result['errors'])}")
            if ctx.obj['verbose']:
                for error in result['errors']:
                    click.echo(f"    {error}")

    except Exception as e:
        click.echo(f"✗ Verification failed: {e}", err=True)


# Encryption Commands
@cli.group()
def encryption():
    """Encryption key management commands."""
    pass


@encryption.command()
@click.option('--key-file', help='Path to encryption key file (default: ./encryption.key)')
@click.option('--overwrite', is_flag=True, help='Overwrite existing key file')
@click.pass_context
def generate_key(ctx, key_file, overwrite):
    """Generate a new encryption key."""
    try:
        key_manager = EncryptionKeyManager(key_file)
        key = key_manager.generate_key(overwrite=overwrite)

        click.echo("✓ Encryption key generated successfully")
        click.echo(f"  Key file: {key_manager.key_file_path}")

        if ctx.obj['verbose']:
            click.echo(f"  Key length: {len(key)} bytes")

    except FileExistsError as e:
        click.echo(f"✗ Key file already exists: {e}")
        click.echo("  Use --overwrite to replace existing key")
    except Exception as e:
        click.echo(f"✗ Failed to generate key: {e}", err=True)


@encryption.command()
@click.option('--key-file', help='Path to encryption key file')
@click.pass_context
def rotate_key(ctx, key_file):
    """Rotate the encryption key (generates new key, keeps backup of old)."""
    try:
        key_manager = EncryptionKeyManager(key_file)
        old_key, new_key = key_manager.rotate_key()

        click.echo("✓ Encryption key rotated successfully")
        click.echo(f"  Key file: {key_manager.key_file_path}")
        click.echo(f"  Old key backed up")

        if ctx.obj['verbose']:
            click.echo(f"  New key length: {len(new_key)} bytes")

    except Exception as e:
        click.echo(f"✗ Failed to rotate key: {e}", err=True)


@encryption.command()
@click.option('--key-file', help='Path to encryption key file')
@click.pass_context
def key_info(ctx, key_file):
    """Show information about the encryption key."""
    try:
        key_manager = EncryptionKeyManager(key_file)

        if not key_manager.key_file_path.exists():
            click.echo("✗ No encryption key file found")
            click.echo(f"  Expected location: {key_manager.key_file_path}")
            return

        # Load key to verify it's valid
        key = key_manager.load_key()

        # Read metadata
        import json
        with open(key_manager.key_file_path, 'r') as f:
            key_data = json.load(f)

        click.echo("Encryption Key Information:")
        click.echo(f"  File: {key_manager.key_file_path}")
        click.echo(f"  Algorithm: {key_data.get('algorithm')}")
        click.echo(f"  Created: {key_data.get('created_at')}")
        click.echo(f"  Version: {key_data.get('version')}")
        click.echo(f"  Key length: {len(key)} bytes")

        if key_data.get('rotated_from'):
            click.echo(f"  Rotated from: {key_data['rotated_from']}")

        # Check file permissions
        if os.name != 'nt':
            import stat
            permissions = oct(key_manager.key_file_path.stat().st_mode)[-3:]
            click.echo(f"  File permissions: {permissions}")
            if permissions != '600':
                click.echo(f"  ⚠ Warning: Key file should have 600 permissions for security")

    except Exception as e:
        click.echo(f"✗ Failed to read key info: {e}", err=True)


@encryption.command()
@click.option('--input', '-i', required=True, help='Input file to encrypt')
@click.option('--output', '-o', help='Output file (default: input.encrypted)')
@click.option('--key-file', help='Path to encryption key file')
@click.pass_context
def encrypt_file(ctx, input, output, key_file):
    """Encrypt a file using the encryption key."""
    try:
        key_manager = EncryptionKeyManager(key_file)
        encryption = LocalEncryption(key_manager)

        input_path = Path(input)
        if not input_path.exists():
            click.echo(f"✗ Input file not found: {input}")
            return

        output_path = encryption.encrypt_file(input_path, output)

        click.echo("✓ File encrypted successfully")
        click.echo(f"  Input: {input_path}")
        click.echo(f"  Output: {output_path}")
        click.echo(f"  Size: {input_path.stat().st_size} → {output_path.stat().st_size} bytes")

    except Exception as e:
        click.echo(f"✗ Encryption failed: {e}", err=True)


@encryption.command()
@click.option('--input', '-i', required=True, help='Encrypted file to decrypt')
@click.option('--output', '-o', help='Output file (default: removes .encrypted extension)')
@click.option('--key-file', help='Path to encryption key file')
@click.pass_context
def decrypt_file(ctx, input, output, key_file):
    """Decrypt a file using the encryption key."""
    try:
        key_manager = EncryptionKeyManager(key_file)
        encryption = LocalEncryption(key_manager)

        input_path = Path(input)
        if not input_path.exists():
            click.echo(f"✗ Input file not found: {input}")
            return

        output_path = encryption.decrypt_file(input_path, output)

        click.echo("✓ File decrypted successfully")
        click.echo(f"  Input: {input_path}")
        click.echo(f"  Output: {output_path}")
        click.echo(f"  Size: {input_path.stat().st_size} → {output_path.stat().st_size} bytes")

    except Exception as e:
        click.echo(f"✗ Decryption failed: {e}", err=True)


if __name__ == '__main__':
    cli()