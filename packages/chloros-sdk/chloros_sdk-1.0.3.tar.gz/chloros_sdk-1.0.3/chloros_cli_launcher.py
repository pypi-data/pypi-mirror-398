#!/usr/bin/env python3
"""
Chloros CLI Launcher
Opens a terminal window with Chloros CLI ready to use
Compiles to: chloros-cli-launcher.exe
"""

import os
import sys
import subprocess
import pathlib

def find_cli_exe():
    """Find the Chloros CLI executable"""
    # Possible locations
    possible_paths = [
        # Relative to launcher
        pathlib.Path(__file__).parent / "resources" / "cli" / "chloros-cli.exe",
        # Standard installation
        pathlib.Path("C:/Program Files/MAPIR/Chloros/resources/cli/chloros-cli.exe"),
        pathlib.Path("C:/Program Files (x86)/MAPIR/Chloros/resources/cli/chloros-cli.exe"),
        # Local AppData
        pathlib.Path(os.environ.get('LOCALAPPDATA', '')) / "Programs" / "Chloros" / "resources" / "cli" / "chloros-cli.exe",
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path.resolve())
    
    return None

def main():
    """Launch interactive CLI session"""
    cli_exe = find_cli_exe()
    
    if not cli_exe:
        print("ERROR: Chloros CLI not found!")
        print("\nExpected locations:")
        print("  - C:\\Program Files\\MAPIR\\Chloros\\resources\\cli\\chloros-cli.exe")
        print("  - C:\\Program Files (x86)\\MAPIR\\Chloros\\resources\\cli\\chloros-cli.exe")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Create a batch script that will run in the new window
    cli_dir = os.path.dirname(cli_exe)
    
    # Build command to open CMD with CLI ready
    cmd = f'''@echo off
chcp 65001 >nul 2>&1
cls
echo.
echo ============================================================
echo   CHLOROS COMMAND LINE INTERFACE
echo ============================================================
echo.
echo Found: {cli_exe}
echo.
echo Quick Start Examples:
echo   chloros-cli process "C:\\path\\to\\images"
echo   chloros-cli process "C:\\path\\to\\images" --indices NDVI NDRE
echo   chloros-cli login your.email@example.com "password"
echo   chloros-cli status
echo   chloros-cli --help
echo.
echo ============================================================
echo.
set "PATH={cli_dir};%PATH%"
doskey chloros-cli="{cli_exe}" $*
cmd /k
'''
    
    # Write temp batch file
    temp_bat = os.path.join(os.environ.get('TEMP', '.'), 'chloros_cli_launcher.bat')
    with open(temp_bat, 'w', encoding='utf-8') as f:
        f.write(cmd)
    
    # Launch it
    subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', temp_bat], 
                     creationflags=subprocess.CREATE_NEW_CONSOLE)

if __name__ == '__main__':
    main()







