"""
Pipeline Registry
Manages versioning and storage of preprocessing pipelines
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import shutil
from datetime import datetime
import logging

from .pipeline_executor import PipelineExecutor
from .pipeline_builder import PipelineBuilder

logger = logging.getLogger(__name__)


class PipelineRegistry:
    """
    Manages versioned preprocessing pipelines
    
    Features:
        - Version management for pipelines
        - Storage and retrieval
        - Activation/deactivation
        - Metadata tracking
    """
    
    def __init__(self, storage_path: str):
        """
        Initialize PipelineRegistry
        
        Args:
            storage_path: Base path for pipeline storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._registry_file = self.storage_path / "registry.json"
        self._registry: Dict[str, Any] = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from file"""
        if self._registry_file.exists():
            with open(self._registry_file, 'r') as f:
                return json.load(f)
        return {"programs": {}}
    
    def _save_registry(self) -> None:
        """Save registry to file"""
        with open(self._registry_file, 'w') as f:
            json.dump(self._registry, f, indent=2, default=str)
    
    def _get_program_path(self, program_id: str) -> Path:
        """Get storage path for a program"""
        path = self.storage_path / program_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _get_version_path(self, program_id: str, version: int) -> Path:
        """Get path for a specific pipeline version"""
        return self._get_program_path(program_id) / f"v{version}"
    
    def register_pipeline(
        self,
        program_id: str,
        executor: PipelineExecutor,
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Register a new pipeline version
        
        Args:
            program_id: Program identifier
            executor: Fitted pipeline executor
            config: Pipeline configuration
            metadata: Optional additional metadata
        
        Returns:
            New version number
        """
        if not executor.is_fitted:
            raise ValueError("Pipeline must be fitted before registration")
        
        # Initialize program entry if needed
        if program_id not in self._registry["programs"]:
            self._registry["programs"][program_id] = {
                "versions": [],
                "active_version": None
            }
        
        program_entry = self._registry["programs"][program_id]
        
        # Determine new version number
        if program_entry["versions"]:
            new_version = max(v["version"] for v in program_entry["versions"]) + 1
        else:
            new_version = 1
        
        # Create version directory
        version_path = self._get_version_path(program_id, new_version)
        version_path.mkdir(parents=True, exist_ok=True)
        
        # Save pipeline
        pipeline_file = version_path / "pipeline.pkl"
        executor.save(str(pipeline_file))
        
        # Save config
        config_file = version_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        # Create version entry
        version_entry = {
            "version": new_version,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": False,
            "pipeline_file": str(pipeline_file),
            "config_file": str(config_file),
            "feature_names_in": executor.feature_names_in,
            "feature_names_out": executor.feature_names_out,
            "fit_report": executor.get_fit_report(),
            "metadata": metadata or {}
        }
        
        program_entry["versions"].append(version_entry)
        
        self._save_registry()
        
        logger.info(f"Registered pipeline v{new_version} for program {program_id}")
        
        return new_version
    
    def get_pipeline(
        self, 
        program_id: str, 
        version: Optional[int] = None
    ) -> PipelineExecutor:
        """
        Get a pipeline by program and version
        
        Args:
            program_id: Program identifier
            version: Optional version number (defaults to active)
        
        Returns:
            Loaded PipelineExecutor
        """
        if program_id not in self._registry["programs"]:
            raise ValueError(f"Program {program_id} not found")
        
        program_entry = self._registry["programs"][program_id]
        
        # Determine version to load
        if version is None:
            version = program_entry.get("active_version")
            if version is None:
                raise ValueError(f"No active pipeline for program {program_id}")
        
        # Find version entry
        version_entry = None
        for v in program_entry["versions"]:
            if v["version"] == version:
                version_entry = v
                break
        
        if version_entry is None:
            raise ValueError(f"Version {version} not found for program {program_id}")
        
        # Load pipeline
        pipeline_file = version_entry["pipeline_file"]
        return PipelineExecutor.load(pipeline_file)
    
    def activate_version(self, program_id: str, version: int) -> None:
        """
        Activate a specific pipeline version
        
        Args:
            program_id: Program identifier
            version: Version to activate
        """
        if program_id not in self._registry["programs"]:
            raise ValueError(f"Program {program_id} not found")
        
        program_entry = self._registry["programs"][program_id]
        
        # Validate version exists
        version_exists = any(v["version"] == version for v in program_entry["versions"])
        if not version_exists:
            raise ValueError(f"Version {version} not found")
        
        # Deactivate all versions
        for v in program_entry["versions"]:
            v["is_active"] = False
        
        # Activate specified version
        for v in program_entry["versions"]:
            if v["version"] == version:
                v["is_active"] = True
                break
        
        program_entry["active_version"] = version
        
        self._save_registry()
        
        logger.info(f"Activated pipeline v{version} for program {program_id}")
    
    def get_active_version(self, program_id: str) -> Optional[int]:
        """Get active version for a program"""
        if program_id not in self._registry["programs"]:
            return None
        return self._registry["programs"][program_id].get("active_version")
    
    def list_versions(self, program_id: str) -> List[Dict[str, Any]]:
        """
        List all versions for a program
        
        Args:
            program_id: Program identifier
        
        Returns:
            List of version metadata
        """
        if program_id not in self._registry["programs"]:
            return []
        
        versions = []
        for v in self._registry["programs"][program_id]["versions"]:
            versions.append({
                "version": v["version"],
                "created_at": v["created_at"],
                "is_active": v["is_active"],
                "features_in": len(v.get("feature_names_in", [])),
                "features_out": len(v.get("feature_names_out", [])),
                "metadata": v.get("metadata", {})
            })
        
        return sorted(versions, key=lambda x: x["version"], reverse=True)
    
    def get_version_details(
        self, 
        program_id: str, 
        version: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific version
        
        Args:
            program_id: Program identifier
            version: Version number
        
        Returns:
            Version details or None
        """
        if program_id not in self._registry["programs"]:
            return None
        
        for v in self._registry["programs"][program_id]["versions"]:
            if v["version"] == version:
                return v.copy()
        
        return None
    
    def get_config(
        self, 
        program_id: str, 
        version: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get pipeline configuration
        
        Args:
            program_id: Program identifier
            version: Optional version (defaults to active)
        
        Returns:
            Pipeline configuration
        """
        if program_id not in self._registry["programs"]:
            raise ValueError(f"Program {program_id} not found")
        
        program_entry = self._registry["programs"][program_id]
        
        if version is None:
            version = program_entry.get("active_version")
        
        if version is None:
            raise ValueError("No version specified and no active version")
        
        # Find version entry
        for v in program_entry["versions"]:
            if v["version"] == version:
                config_file = v["config_file"]
                with open(config_file, 'r') as f:
                    return json.load(f)
        
        raise ValueError(f"Version {version} not found")
    
    def delete_version(self, program_id: str, version: int) -> None:
        """
        Delete a pipeline version
        
        Args:
            program_id: Program identifier
            version: Version to delete
        """
        if program_id not in self._registry["programs"]:
            raise ValueError(f"Program {program_id} not found")
        
        program_entry = self._registry["programs"][program_id]
        
        # Check if version is active
        if program_entry.get("active_version") == version:
            raise ValueError("Cannot delete active version. Activate another version first.")
        
        # Find and remove version
        version_entry = None
        for i, v in enumerate(program_entry["versions"]):
            if v["version"] == version:
                version_entry = program_entry["versions"].pop(i)
                break
        
        if version_entry is None:
            raise ValueError(f"Version {version} not found")
        
        # Delete files
        version_path = self._get_version_path(program_id, version)
        if version_path.exists():
            shutil.rmtree(version_path)
        
        self._save_registry()
        
        logger.info(f"Deleted pipeline v{version} for program {program_id}")
    
    def copy_version(
        self, 
        program_id: str, 
        version: int, 
        new_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Copy a pipeline version (for experimentation)
        
        Args:
            program_id: Program identifier
            version: Version to copy
            new_metadata: Optional new metadata
        
        Returns:
            New version number
        """
        # Load existing pipeline
        executor = self.get_pipeline(program_id, version)
        config = self.get_config(program_id, version)
        
        # Get existing metadata
        version_details = self.get_version_details(program_id, version)
        metadata = version_details.get("metadata", {}).copy() if version_details else {}
        metadata["copied_from"] = version
        
        if new_metadata:
            metadata.update(new_metadata)
        
        # Register as new version
        return self.register_pipeline(program_id, executor, config, metadata)
    
    def list_programs(self) -> List[str]:
        """List all programs with registered pipelines"""
        return list(self._registry["programs"].keys())
    
    def get_program_summary(self, program_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary for a program
        
        Args:
            program_id: Program identifier
        
        Returns:
            Program summary or None
        """
        if program_id not in self._registry["programs"]:
            return None
        
        program_entry = self._registry["programs"][program_id]
        
        return {
            "program_id": program_id,
            "total_versions": len(program_entry["versions"]),
            "active_version": program_entry.get("active_version"),
            "versions": self.list_versions(program_id)
        }
