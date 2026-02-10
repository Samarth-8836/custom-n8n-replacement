"""
File System Manager

Handles all file system operations for the Pipeline system.
Manages directories for pipelines, runs, temp workspaces, and archives.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

import config


class FileManager:
    """
    Manages file system operations for the Pipeline system.

    The file system structure:
    {pipeline_id}/
    ├── .pipeline_system/
    │   ├── db/
    │   │   └── state.db
    │   ├── definitions/
    │   │   ├── pipeline.json
    │   │   └── checkpoints/
    │   │       └── {checkpoint_id}.json
    │   └── logs/
    │       └── system.log
    ├── runs/
    │   ├── v1/
    │   ├── v2/
    │   └── latest -> v2
    ├── .temp/
    │   └── exec_{execution_id}/
    ├── .archived/
    │   └── rollback_{rollback_id}_{datetime}/
    └── .errored/
        └── exec_{execution_id}_{datetime}/
    """

    def __init__(self, pipeline_id: str):
        """
        Initialize the FileManager for a specific pipeline.

        Args:
            pipeline_id: The pipeline UUID
        """
        self.pipeline_id = pipeline_id
        self.base_path = Path(config.BASE_PIPELINES_PATH) / pipeline_id
        self.system_dir = self.base_path / config.PIPELINE_SYSTEM_DIR
        self.db_dir = self.system_dir / config.PIPELINE_DB_DIR
        self.definitions_dir = self.system_dir / config.PIPELINE_DEFINITIONS_DIR
        self.checkpoints_dir = self.definitions_dir / "checkpoints"
        self.logs_dir = self.system_dir / config.PIPELINE_LOGS_DIR
        self.runs_dir = self.base_path / config.PIPELINE_RUNS_DIR
        self.temp_dir = self.base_path / config.PIPELINE_TEMP_DIR
        self.archived_dir = self.base_path / config.PIPELINE_ARCHIVED_DIR
        self.errored_dir = self.base_path / config.PIPELINE_ERRORED_DIR

    def initialize_pipeline_structure(self) -> None:
        """
        Create the initial directory structure for a new pipeline.
        """
        directories = [
            self.system_dir,
            self.db_dir,
            self.checkpoints_dir,
            self.logs_dir,
            self.runs_dir,
            self.temp_dir,
            self.archived_dir,
            self.errored_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_run_directory(self, run_version: int) -> Path:
        """
        Get the directory path for a specific run version.

        Args:
            run_version: The run version number (e.g., 1, 2, 3)

        Returns:
            Path: The run directory path
        """
        return self.runs_dir / f"v{run_version}"

    def create_run_directory(self, run_version: int) -> Path:
        """
        Create a directory for a new run version.

        Args:
            run_version: The run version number

        Returns:
            Path: The created run directory path
        """
        run_dir = self.get_run_directory(run_version)
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def get_checkpoint_directory(self, run_version: int, checkpoint_name: str, checkpoint_position: int) -> Path:
        """
        Get the directory path for a specific checkpoint execution.

        Args:
            run_version: The run version number
            checkpoint_name: The checkpoint name
            checkpoint_position: The checkpoint position in the pipeline

        Returns:
            Path: The checkpoint directory path
        """
        run_dir = self.get_run_directory(run_version)
        checkpoint_dir_name = f"checkpoint_{checkpoint_position}_{checkpoint_name}"
        return run_dir / checkpoint_dir_name

    def create_checkpoint_directory(self, run_version: int, checkpoint_name: str, checkpoint_position: int) -> Path:
        """
        Create a directory for a checkpoint execution.

        Args:
            run_version: The run version number
            checkpoint_name: The checkpoint name
            checkpoint_position: The checkpoint position in the pipeline

        Returns:
            Path: The created checkpoint directory path
        """
        checkpoint_dir = self.get_checkpoint_directory(run_version, checkpoint_name, checkpoint_position)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        return checkpoint_dir

    def get_checkpoint_outputs_directory(self, run_version: int, checkpoint_name: str, checkpoint_position: int) -> Path:
        """
        Get the outputs directory for a checkpoint execution.

        Args:
            run_version: The run version number
            checkpoint_name: The checkpoint name
            checkpoint_position: The checkpoint position in the pipeline

        Returns:
            Path: The outputs directory path
        """
        checkpoint_dir = self.get_checkpoint_directory(run_version, checkpoint_name, checkpoint_position)
        return checkpoint_dir / "outputs"

    def create_checkpoint_outputs_directory(self, run_version: int, checkpoint_name: str, checkpoint_position: int) -> Path:
        """
        Create the outputs directory for a checkpoint execution.

        Args:
            run_version: The run version number
            checkpoint_name: The checkpoint name
            checkpoint_position: The checkpoint position in the pipeline

        Returns:
            Path: The created outputs directory path
        """
        outputs_dir = self.get_checkpoint_outputs_directory(run_version, checkpoint_name, checkpoint_position)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        return outputs_dir

    def get_temp_execution_directory(self, execution_id: str) -> Path:
        """
        Get the temp workspace directory for a checkpoint execution.

        Args:
            execution_id: The execution UUID

        Returns:
            Path: The temp execution directory path
        """
        return self.temp_dir / f"exec_{execution_id}"

    def create_temp_execution_directory(self, execution_id: str) -> Path:
        """
        Create a temp workspace directory for a checkpoint execution.

        The temp workspace persists across retry attempts (same execution_id).

        Args:
            execution_id: The execution UUID

        Returns:
            Path: The created temp execution directory path
        """
        exec_dir = self.get_temp_execution_directory(execution_id)
        exec_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (exec_dir / "workspace").mkdir(exist_ok=True)
        (exec_dir / "artifacts_staging").mkdir(exist_ok=True)

        return exec_dir

    def delete_temp_execution_directory(self, execution_id: str) -> None:
        """
        Delete the temp workspace directory for a checkpoint execution.

        Args:
            execution_id: The execution UUID
        """
        exec_dir = self.get_temp_execution_directory(execution_id)
        if exec_dir.exists():
            shutil.rmtree(exec_dir)

    def get_artifact_staging_path(self, execution_id: str, artifact_name: str, artifact_id: str, artifact_format: str) -> Path:
        """
        Get the staging path for an artifact (before promotion to permanent).

        Args:
            execution_id: The execution UUID
            artifact_name: The artifact name
            artifact_id: The artifact definition UUID
            artifact_format: The artifact format (e.g., 'json', 'md')

        Returns:
            Path: The staging file path
        """
        exec_dir = self.get_temp_execution_directory(execution_id)
        staging_dir = exec_dir / "artifacts_staging"
        return staging_dir / f"{artifact_name}_{artifact_id}.{artifact_format}"

    def get_permanent_artifact_path(
        self,
        run_version: int,
        checkpoint_name: str,
        checkpoint_position: int,
        artifact_name: str,
        artifact_id: str,
        artifact_format: str
    ) -> Path:
        """
        Get the permanent path for an artifact.

        Args:
            run_version: The run version number
            checkpoint_name: The checkpoint name
            checkpoint_position: The checkpoint position
            artifact_name: The artifact name
            artifact_id: The artifact definition UUID
            artifact_format: The artifact format (e.g., 'json', 'md')

        Returns:
            Path: The permanent file path
        """
        outputs_dir = self.get_checkpoint_outputs_directory(run_version, checkpoint_name, checkpoint_position)
        return outputs_dir / f"{artifact_name}_{artifact_id}_v{run_version}.{artifact_format}"

    def promote_artifact_to_permanent(
        self,
        execution_id: str,
        run_version: int,
        checkpoint_name: str,
        checkpoint_position: int,
        artifact_name: str,
        artifact_id: str,
        artifact_format: str
    ) -> Path:
        """
        Move an artifact from staging to permanent storage.

        Args:
            execution_id: The execution UUID
            run_version: The run version number
            checkpoint_name: The checkpoint name
            checkpoint_position: The checkpoint position
            artifact_name: The artifact name
            artifact_id: The artifact definition UUID
            artifact_format: The artifact format

        Returns:
            Path: The permanent file path
        """
        staging_path = self.get_artifact_staging_path(execution_id, artifact_name, artifact_id, artifact_format)
        permanent_path = self.get_permanent_artifact_path(
            run_version, checkpoint_name, checkpoint_position, artifact_name, artifact_id, artifact_format
        )

        # Ensure output directory exists
        permanent_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file
        shutil.move(str(staging_path), str(permanent_path))

        return permanent_path

    def create_rollback_directory(self, rollback_id: str) -> Path:
        """
        Create a directory for rollback archives.

        Args:
            rollback_id: The rollback UUID

        Returns:
            Path: The created rollback directory path
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rollback_dir = self.archived_dir / f"rollback_{rollback_id}_{timestamp}"
        rollback_dir.mkdir(parents=True, exist_ok=True)

        # Create archived data subdirectory
        (rollback_dir / "archived_data").mkdir(exist_ok=True)

        return rollback_dir

    def create_errored_execution_directory(self, execution_id: str) -> Path:
        """
        Create a directory for a failed execution.

        Args:
            execution_id: The execution UUID

        Returns:
            Path: The created error directory path
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        errored_dir = self.errored_dir / f"exec_{execution_id}_{timestamp}"
        errored_dir.mkdir(parents=True, exist_ok=True)
        return errored_dir

    def update_latest_symlink(self, run_version: int) -> None:
        """
        Update the 'latest' symlink to point to the specified run version.

        On Windows, creates a junction point.

        Args:
            run_version: The run version number to point to
        """
        latest_path = self.runs_dir / "latest"
        target_path = self.get_run_directory(run_version)

        # Remove existing link/junction if it exists
        if latest_path.exists() or latest_path.is_symlink():
            if latest_path.is_symlink() or latest_path.is_junction():
                latest_path.unlink()
            else:
                shutil.rmtree(latest_path)

        # Create new junction (Windows) or symlink (Unix)
        try:
            if os.name == 'nt':
                import subprocess
                subprocess.run(['mklink', '/J', str(latest_path), str(target_path)], shell=True, check=True)
            else:
                latest_path.symlink_to(target_path)
        except Exception:
            # Fallback: just create a marker file
            (latest_path).mkdir(parents=True, exist_ok=True)
            (latest_path / f"points_to_v{run_version}").touch()

    def save_pipeline_definition(self, pipeline_data: dict) -> Path:
        """
        Save the pipeline definition to a JSON file.

        Args:
            pipeline_data: The pipeline definition data

        Returns:
            Path: The saved file path
        """
        definition_path = self.definitions_dir / "pipeline.json"
        with open(definition_path, 'w') as f:
            json.dump(pipeline_data, f, indent=2, default=str)
        return definition_path

    def load_pipeline_definition(self) -> dict:
        """
        Load the pipeline definition from JSON file.

        Returns:
            dict: The pipeline definition data

        Raises:
            FileNotFoundError: If the definition file doesn't exist
        """
        definition_path = self.definitions_dir / "pipeline.json"
        with open(definition_path, 'r') as f:
            return json.load(f)

    def save_checkpoint_definition(self, checkpoint_id: str, checkpoint_data: dict) -> Path:
        """
        Save a checkpoint definition to a JSON file.

        Args:
            checkpoint_id: The checkpoint UUID
            checkpoint_data: The checkpoint definition data

        Returns:
            Path: The saved file path
        """
        definition_path = self.checkpoints_dir / f"{checkpoint_id}.json"
        with open(definition_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
        return definition_path

    def load_checkpoint_definition(self, checkpoint_id: str) -> dict:
        """
        Load a checkpoint definition from JSON file.

        Args:
            checkpoint_id: The checkpoint UUID

        Returns:
            dict: The checkpoint definition data

        Raises:
            FileNotFoundError: If the definition file doesn't exist
        """
        definition_path = self.checkpoints_dir / f"{checkpoint_id}.json"
        with open(definition_path, 'r') as f:
            return json.load(f)

    def delete_checkpoint_definition(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint definition JSON file.

        Args:
            checkpoint_id: The checkpoint UUID

        Returns:
            bool: True if deleted, False if file didn't exist
        """
        definition_path = self.checkpoints_dir / f"{checkpoint_id}.json"
        if definition_path.exists():
            definition_path.unlink()
            return True
        return False

    def save_run_info(self, run_version: int, run_data: dict) -> Path:
        """
        Save run info to a JSON file.

        Args:
            run_version: The run version number
            run_data: The run data

        Returns:
            Path: The saved file path
        """
        run_dir = self.get_run_directory(run_version)
        info_path = run_dir / "run_info.json"
        with open(info_path, 'w') as f:
            json.dump(run_data, f, indent=2, default=str)
        return info_path

    def load_run_info(self, run_version: int) -> dict:
        """
        Load run info from JSON file.

        Args:
            run_version: The run version number

        Returns:
            dict: The run data

        Raises:
            FileNotFoundError: If the info file doesn't exist
        """
        run_dir = self.get_run_directory(run_version)
        info_path = run_dir / "run_info.json"
        with open(info_path, 'r') as f:
            return json.load(f)

    def get_file_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA-256 checksum of a file.

        Args:
            file_path: Path to the file

        Returns:
            str: Hexadecimal checksum string
        """
        import hashlib

        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get_file_size(self, file_path: Path) -> int:
        """
        Get the size of a file in bytes.

        Args:
            file_path: Path to the file

        Returns:
            int: File size in bytes
        """
        return file_path.stat().st_size


# Import os for Windows symlink detection
import os
