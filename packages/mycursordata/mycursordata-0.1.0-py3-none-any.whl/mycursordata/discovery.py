"""
Dynamic discovery of Cursor state.vscdb database files.

Searches common locations across different operating systems and logs
which paths are found and used.
"""

import os
import platform
import logging
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


def get_home_dir() -> Path:
    """Get the user's home directory."""
    return Path.home()


def get_default_cursor_paths() -> list[Path]:
    """
    Get list of common paths where Cursor stores state.vscdb.
    
    Returns paths for:
    - Cursor (main app)
    - Cursor Nightly
    - Cursor Insiders
    - VS Code (for compatibility)
    
    Platform-specific locations are used for macOS, Linux, and Windows.
    """
    home = get_home_dir()
    system = platform.system()
    
    paths = []
    
    if system == "Darwin":  # macOS
        base_paths = [
            home / "Library" / "Application Support",
        ]
        app_names = ["Cursor", "Cursor Nightly", "cursor", "Code"]
    elif system == "Linux":
        base_paths = [
            home / ".config",
            home / ".local" / "share",
        ]
        app_names = ["Cursor", "cursor", "Code"]
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", str(home / "AppData" / "Roaming"))
        base_paths = [Path(appdata)]
        app_names = ["Cursor", "cursor", "Code"]
    else:
        logger.warning(f"Unknown platform: {system}, using generic paths")
        base_paths = [home / ".config", home / ".local" / "share"]
        app_names = ["Cursor", "cursor", "Code"]
    
    # Build full paths for each combination
    for base in base_paths:
        for app_name in app_names:
            # Main state.vscdb location
            paths.append(base / app_name / "User" / "globalStorage" / "state.vscdb")
            
            # Per-workspace state files
            workspace_storage = base / app_name / "User" / "workspaceStorage"
            if workspace_storage.exists():
                paths.append(workspace_storage)
    
    return paths


def find_state_files_in_workspace_storage(workspace_storage: Path) -> Iterator[Path]:
    """
    Find all state.vscdb files within a workspaceStorage directory.
    
    These are per-project databases that may contain additional conversation history.
    """
    if not workspace_storage.exists() or not workspace_storage.is_dir():
        return
    
    for item in workspace_storage.iterdir():
        if item.is_dir():
            state_file = item / "state.vscdb"
            if state_file.exists():
                yield state_file


def discover_cursor_databases(
    extra_paths: list[Path] | None = None,
    include_workspace_dbs: bool = True,
) -> list[dict]:
    """
    Discover all available Cursor state.vscdb databases.
    
    Args:
        extra_paths: Additional paths to check
        include_workspace_dbs: Whether to also search workspaceStorage directories
        
    Returns:
        List of dicts with keys:
        - path: Path to the database file
        - type: 'global' or 'workspace'
        - source: Description of where it was found
    """
    found_databases = []
    checked_paths = []
    
    # Get default paths
    default_paths = get_default_cursor_paths()
    all_paths = default_paths + (extra_paths or [])
    
    for path in all_paths:
        path = Path(path)
        
        # Check if this is a workspaceStorage directory
        if path.name == "workspaceStorage" and path.is_dir():
            logger.info(f"📁 Scanning workspaceStorage: {path}")
            checked_paths.append({"path": str(path), "status": "scanning"})
            
            if include_workspace_dbs:
                for ws_db in find_state_files_in_workspace_storage(path):
                    workspace_id = ws_db.parent.name
                    logger.info(f"  ✅ Found workspace DB: {ws_db}")
                    found_databases.append({
                        "path": ws_db,
                        "type": "workspace",
                        "source": f"workspaceStorage/{workspace_id}",
                    })
        elif path.suffix == ".vscdb" or path.name == "state.vscdb":
            # Direct database file
            if path.exists():
                logger.info(f"✅ Found database: {path}")
                checked_paths.append({"path": str(path), "status": "found"})
                
                # Determine source from path
                source = "global"
                if "Cursor Nightly" in str(path):
                    source = "cursor-nightly/global"
                elif "Cursor" in str(path):
                    source = "cursor/global"
                elif "Code" in str(path):
                    source = "vscode/global"
                    
                found_databases.append({
                    "path": path,
                    "type": "global",
                    "source": source,
                })
            else:
                logger.debug(f"❌ Not found: {path}")
                checked_paths.append({"path": str(path), "status": "not_found"})
        else:
            # Unknown path type, check if it's a directory with state.vscdb
            state_file = path / "state.vscdb"
            if state_file.exists():
                logger.info(f"✅ Found database: {state_file}")
                found_databases.append({
                    "path": state_file,
                    "type": "global",
                    "source": str(path.name),
                })
            else:
                logger.debug(f"❌ Not found: {path}")
    
    return found_databases


def get_primary_database(
    extra_paths: list[Path] | None = None,
) -> Path | None:
    """
    Get the primary (most likely to have data) Cursor database.
    
    Prioritizes:
    1. Cursor global state.vscdb
    2. Cursor Nightly global state.vscdb
    3. Any found global database
    4. Any found workspace database
    
    Returns:
        Path to the database, or None if not found
    """
    databases = discover_cursor_databases(extra_paths=extra_paths, include_workspace_dbs=True)
    
    if not databases:
        logger.warning("No Cursor databases found!")
        return None
    
    # Sort by priority
    def priority(db: dict) -> int:
        if db["type"] == "global" and "cursor" in db["source"]:
            return 0
        if db["type"] == "global" and "cursor-nightly" in db["source"]:
            return 1
        if db["type"] == "global":
            return 2
        return 3
    
    databases.sort(key=priority)
    
    primary = databases[0]
    logger.info(f"📌 Using primary database: {primary['path']} ({primary['source']})")
    
    return primary["path"]

