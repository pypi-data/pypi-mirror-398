"""
Windows Service Manager

Handles Windows-specific functionality for the WATS Client:
- Auto-start on system startup
- Windows registry management
- System tray functionality
"""

import os
import sys
import winreg
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# Registry key for auto-start programs
REGISTRY_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "pyWATS_Client"


def get_executable_path() -> str:
    """Get the path to the executable/script for auto-start"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return sys.executable
    else:
        # Running as Python script
        # Use pythonw.exe for no console window
        python_exe = sys.executable
        if python_exe.endswith('python.exe'):
            pythonw = python_exe.replace('python.exe', 'pythonw.exe')
            if os.path.exists(pythonw):
                python_exe = pythonw
        
        # Get the pywats_client module path
        module_path = Path(__file__).parent.parent
        return f'"{python_exe}" -m pywats_client'


def enable_auto_start() -> bool:
    """
    Enable auto-start on Windows startup.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        executable = get_executable_path()
        
        # Open the registry key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_RUN_KEY,
            0,
            winreg.KEY_SET_VALUE
        )
        
        # Set the value
        winreg.SetValueEx(
            key,
            APP_NAME,
            0,
            winreg.REG_SZ,
            executable
        )
        
        winreg.CloseKey(key)
        logger.info(f"Auto-start enabled: {executable}")
        return True
        
    except WindowsError as e:
        logger.error(f"Failed to enable auto-start: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error enabling auto-start: {e}")
        return False


def disable_auto_start() -> bool:
    """
    Disable auto-start on Windows startup.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Open the registry key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_RUN_KEY,
            0,
            winreg.KEY_SET_VALUE
        )
        
        # Delete the value
        try:
            winreg.DeleteValue(key, APP_NAME)
        except WindowsError:
            # Value doesn't exist, that's fine
            pass
        
        winreg.CloseKey(key)
        logger.info("Auto-start disabled")
        return True
        
    except WindowsError as e:
        logger.error(f"Failed to disable auto-start: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error disabling auto-start: {e}")
        return False


def is_auto_start_enabled() -> bool:
    """
    Check if auto-start is enabled.
    
    Returns:
        True if auto-start is enabled, False otherwise
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_RUN_KEY,
            0,
            winreg.KEY_READ
        )
        
        try:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except WindowsError:
            winreg.CloseKey(key)
            return False
            
    except WindowsError:
        return False
    except Exception as e:
        logger.debug(f"Error checking auto-start status: {e}")
        return False


def set_auto_start(enabled: bool) -> bool:
    """
    Enable or disable auto-start based on parameter.
    
    Args:
        enabled: True to enable, False to disable
        
    Returns:
        True if successful
    """
    if enabled:
        return enable_auto_start()
    else:
        return disable_auto_start()


def create_startup_shortcut(target_path: Optional[str] = None) -> bool:
    """
    Create a shortcut in the Windows Startup folder.
    Alternative to registry method.
    
    Args:
        target_path: Path to the executable/script (uses default if None)
        
    Returns:
        True if successful
    """
    try:
        import win32com.client
        
        # Get startup folder path
        startup_folder = Path(os.environ['APPDATA']) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
        shortcut_path = startup_folder / f"{APP_NAME}.lnk"
        
        if target_path is None:
            target_path = get_executable_path()
        
        # Create shortcut
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        
        if '"' in target_path:
            # It's a command with arguments
            parts = target_path.split('" ', 1)
            shortcut.TargetPath = parts[0].strip('"')
            if len(parts) > 1:
                shortcut.Arguments = parts[1]
        else:
            shortcut.TargetPath = target_path
        
        shortcut.WorkingDirectory = str(Path.home())
        shortcut.Description = "WATS Client - Test Report Management"
        shortcut.save()
        
        logger.info(f"Startup shortcut created: {shortcut_path}")
        return True
        
    except ImportError:
        logger.error("win32com not available - cannot create shortcut")
        return False
    except Exception as e:
        logger.error(f"Failed to create startup shortcut: {e}")
        return False


def remove_startup_shortcut() -> bool:
    """
    Remove the startup shortcut.
    
    Returns:
        True if successful or shortcut doesn't exist
    """
    try:
        startup_folder = Path(os.environ['APPDATA']) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
        shortcut_path = startup_folder / f"{APP_NAME}.lnk"
        
        if shortcut_path.exists():
            shortcut_path.unlink()
            logger.info(f"Startup shortcut removed: {shortcut_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to remove startup shortcut: {e}")
        return False
