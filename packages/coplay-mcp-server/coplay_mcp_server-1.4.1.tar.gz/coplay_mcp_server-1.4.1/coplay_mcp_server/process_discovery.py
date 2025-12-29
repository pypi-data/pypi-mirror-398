"""Unity process discovery utilities."""

import logging
import platform
from pathlib import Path
from typing import List, Optional

import psutil

logger = logging.getLogger(__name__)


def find_unity_processes() -> List[psutil.Process]:
    """Find all running Unity Editor processes."""
    unity_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_info = proc.info
                if not proc_info['name']:
                    continue
                    
                name = proc_info['name'].lower()
                
                # Check for Unity process names across platforms
                if any(unity_name in name for unity_name in [
                    'unity', 'unity.exe', 'unity editor', 'unity hub'
                ]):
                    # Skip Unity Hub, we only want Editor instances
                    if 'hub' not in name:
                        unity_processes.append(proc)
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
        logger.error(f"Error finding Unity processes: {e}")
        
    return unity_processes


def extract_project_path_from_cmdline(cmdline: List[str]) -> Optional[str]:
    """Extract Unity project path from command line arguments."""
    if not cmdline:
        return None
        
    try:
        # Look for -projectPath argument
        for i, arg in enumerate(cmdline):
            if arg.lower() == "-projectpath" and i + 1 < len(cmdline):
                project_path = cmdline[i + 1]
                # Remove quotes if present
                project_path = project_path.strip('"\'')
                return project_path
                
    except Exception as e:
        logger.debug(f"Error extracting project path from cmdline: {e}")
        
    return None


def verify_unity_project(project_path: str) -> bool:
    """Verify that a path is a valid Unity project."""
    try:
        project_dir = Path(project_path)
        if not project_dir.exists() or not project_dir.is_dir():
            return False
            
        # Check for Assets folder (required for Unity projects)
        assets_dir = project_dir / "Assets"
        if not assets_dir.exists() or not assets_dir.is_dir():
            return False
            
        return True
        
    except Exception as e:
        logger.debug(f"Error verifying Unity project at {project_path}: {e}")
        return False


def _discover_from_temp_dirs() -> List[str]:
    """Discover Unity projects from MCP request directories in temp locations."""
    project_roots = []
    
    try:
        # Common temp directory locations
        temp_paths = []
        
        if platform.system() == "Windows":
            import tempfile
            temp_paths.append(Path(tempfile.gettempdir()))
            # Also check AppData/Local
            try:
                appdata_local = Path.home() / "AppData" / "Local"
                if appdata_local.exists():
                    temp_paths.append(appdata_local)
            except Exception:
                pass
        else:
            # Unix-like systems
            temp_paths.extend([
                Path("/tmp"),
                Path.home() / ".cache",
                Path("/var/tmp")
            ])
        
        for temp_path in temp_paths:
            if not temp_path.exists():
                continue
                
            try:
                # Look for Coplay MCP request directories
                for path in temp_path.rglob("**/Temp/Coplay/MCPRequests"):
                    if path.is_dir():
                        # Try to infer project root from temp path structure
                        temp_index = None
                        parts = path.parts
                        
                        for i, part in enumerate(parts):
                            if part.lower() == "temp":
                                temp_index = i
                                break
                                
                        if temp_index and temp_index > 0:
                            project_path = str(Path(*parts[:temp_index]))
                            if verify_unity_project(project_path):
                                project_roots.append(project_path)
                                
            except Exception as e:
                logger.debug(f"Error searching temp path {temp_path}: {e}")
                
    except Exception as e:
        logger.debug(f"Error discovering from temp directories: {e}")
        
    return project_roots


def discover_unity_project_roots() -> List[str]:
    """Discover all Unity project roots from running processes."""
    project_roots = []
    
    try:
        unity_processes = find_unity_processes()
        logger.info(f"Found {len(unity_processes)} Unity processes")
        
        for proc in unity_processes:
            try:
                cmdline = proc.cmdline()
                project_path = extract_project_path_from_cmdline(cmdline)
                
                if project_path and verify_unity_project(project_path):
                    if project_path not in project_roots:
                        project_roots.append(project_path)
                        logger.info(f"Found Unity project: {project_path}")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug(f"Error processing Unity process {proc.pid}: {e}")
                
    except Exception as e:
        logger.error(f"Error discovering Unity project roots: {e}")
        
    # Also check for MCP request directories in temp locations
    project_roots.extend(_discover_from_temp_dirs())
    
    return list(set(project_roots))  # Remove duplicates
