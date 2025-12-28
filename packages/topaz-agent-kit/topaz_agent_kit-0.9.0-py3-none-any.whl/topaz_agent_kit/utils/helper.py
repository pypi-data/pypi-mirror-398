"""
Helper Utilities

This module provides common utility functions used across the Topaz Agent Kit.
"""

from pathlib import Path

from topaz_agent_kit.utils.logger import Logger


class Helper:
    """Generic helper class with utility functions."""
    
    def __init__(self):
        self.logger = Logger("Helper")
    
    def find_project_dir(self, start: Path, max_levels: int = 10) -> Path:
        """
        Find project directory by looking for pipeline.yml starting from a given path.
        
        Args:
            start: Starting path to search from
            max_levels: Maximum number of parent directories to search
            
        Returns:
            Path to the project directory containing pipeline.yml
            
        Raises:
            FileNotFoundError: If no project directory is found within max_levels
        """
        self.logger.debug("Searching for project directory starting from: {}", start)
        
        current = start
        for level in range(max_levels):
            pipeline_file = current / "config" / "pipeline.yml"
            
            if pipeline_file.exists():
                self.logger.debug("Found project directory at level {}: {}", level, current)
                return current
            
            if current == current.parent:  # Reached root directory
                self.logger.debug("Reached root directory at level {}", level)
                break
                
            current = current.parent
            self.logger.debug("Checking parent directory at level {}: {}", level + 1, current)
        
        # No project found - fail fast
        error_msg = f"No project directory found (no pipeline.yml) starting from {start} within {max_levels} levels"
        self.logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    def validate_project_dir(self, project_dir: Path) -> bool:
        """
        Validate that a directory contains a valid project.
        
        Args:
            project_dir: Path to validate
            
        Returns:
            True if valid project, False otherwise
        """
        required_files = [
            "config/pipeline.yml",
            "config/ui_manifest.yml"
        ]
        
        for required_file in required_files:
            if not (project_dir / required_file).exists():
                self.logger.debug("Missing required file: {}", required_file)
                return False
        
        self.logger.debug("Project directory validated successfully: {}", project_dir)
        return True


# Global instance for easy access
helper = Helper() 