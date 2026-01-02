"""
Global configuration for journalist package.
"""

import os
import logging

logger = logging.getLogger(__name__)

class JournalistConfig:
    """Centralized configuration for Journalist class."""
    
    # Environment detection
    IS_LOCAL = os.getenv('ENVIRONMENT', 'local') == 'local'
      # Default values - environment dependent
    if IS_LOCAL:
        DEFAULT_BASE_WORKSPACE_PATH = "/tmp/.journalist_workspace"
    else:
        DEFAULT_BASE_WORKSPACE_PATH = "/tmp/.journalist_workspace"
    
    _logged_once = False  # Class variable to ensure we only log once
    
    def __init__(self):
        """Initialize configuration with defaults."""
        self.base_workspace_path = self.DEFAULT_BASE_WORKSPACE_PATH
    
    @classmethod
    def get_base_workspace_path(cls) -> str:
        """Get base workspace path."""
        # Log when the path is requested (first time only)
        if not cls._logged_once:
            logger.info(f"Workspace path: {cls.DEFAULT_BASE_WORKSPACE_PATH} (IS_LOCAL: {cls.IS_LOCAL})")
            cls._logged_once = True
        return cls.DEFAULT_BASE_WORKSPACE_PATH
