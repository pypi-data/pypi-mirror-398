#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHLOROS+ CLI Styling Module
Modern terminal UI with figlet headers, gradients, boxes, and animations
"""

import sys
import time
import itertools
import threading
from typing import Optional, Callable

# Note: UTF-8 console configuration is handled in chloros_cli.py before this module is imported

# ============================================================================
# ANSI Color Codes
# ============================================================================

class ANSIColors:
    """ANSI escape codes for terminal styling"""
    # Reset
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_GREEN = '\033[42m'
    BG_CYAN = '\033[46m'
    
    # GUI Color Palette (CHLOROS brand colors)
    CHLOROS_GREEN = '\033[38;2;76;175;80m'      # #4CAF50
    CHLOROS_CYAN = '\033[38;2;0;204;255m'       # #00ccff
    CHLOROS_YELLOW = '\033[38;2;255;170;0m'     # #ffaa00
    CHLOROS_LIGHT_GREEN = '\033[38;2;0;255;0m'  # #00ff00
    CHLOROS_GRAY = '\033[38;2;200;200;210m'     # rgb(200,200,210)
    
    @staticmethod
    def supports_color() -> bool:
        """Check if terminal supports ANSI colors"""
        # Windows 10+ supports ANSI through VT100 emulation
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # Enable VT100 mode on Windows
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except:
                return False
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """Create RGB color code"""
        return f'\033[38;2;{r};{g};{b}m'


# ============================================================================
# Gradient Generator
# ============================================================================

def create_gradient(text: str, start_color: tuple, end_color: tuple) -> str:
    """
    Create color gradient across text
    
    Args:
        text: Text to apply gradient to
        start_color: RGB tuple (r, g, b) for start color
        end_color: RGB tuple (r, g, b) for end color
    
    Returns:
        Styled text with gradient
    """
    if not ANSIColors.supports_color():
        return text
    
    lines = text.split('\n')
    result = []
    
    for line in lines:
        if not line.strip():
            result.append(line)
            continue
        
        gradient_line = ""
        length = len(line)
        
        for i, char in enumerate(line):
            if char.strip():  # Only color non-whitespace
                # Calculate color interpolation
                ratio = i / max(length - 1, 1)
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                
                gradient_line += f"\033[38;2;{r};{g};{b}m{char}"
            else:
                gradient_line += char
        
        result.append(gradient_line + ANSIColors.RESET)
    
    return '\n'.join(result)


# ============================================================================
# Figlet-Style ASCII Art Header
# ============================================================================

CHLOROS_LOGO = r"""
  ██████╗██╗  ██╗██╗      ██████╗ ██████╗  ██████╗ ███████╗ ██         ██████╗██╗     ██╗
 ██╔════╝██║  ██║██║     ██╔═══██╗██╔══██╗██╔═══██╗██╔════╝████       ██╔════╝██║     ██║
 ██║     ███████║██║     ██║   ██║██████╔╝██║   ██║███████╗ ██        ██║     ██║     ██║
 ██║     ██╔══██║██║     ██║   ██║██╔══██╗██║   ██║╚════██║           ██║     ██║     ██║
 ╚██████╗██║  ██║███████╗╚██████╔╝██║  ██║╚██████╔╝███████║           ╚██████╗███████╗██║
  ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝            ╚═════╝╚══════╝╚═╝
"""

CHLOROS_LOGO_SMALL = r"""
 ██████╗██╗  ██╗██╗      ██████╗ ██████╗  ██████╗ ███████╗+
██╔════╝██║  ██║██║     ██╔═══██╗██╔══██╗██╔═══██╗██╔════╝
██║     ███████║██║     ██║   ██║██████╔╝██║   ██║███████╗
██║     ██╔══██║██║     ██║   ██║██╔══██╗██║   ██║╚════██║
╚██████╗██║  ██║███████╗╚██████╔╝██║  ██║╚██████╔╝███████║
 ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
"""


def print_header(subtitle: str = "MAPIR CHLOROS+ Command Line Interface", version: str = "1.0.0") -> None:
    """Print fancy header with gradient"""
    
    # Green to Yellow-Green gradient colors (matching GUI - less yellow, more green-biased)
    GREEN = (76, 175, 80)        # #4CAF50 - Start color
    YELLOW_GREEN = (180, 200, 60)  # More yellow-green, less pure yellow (shifted right in gradient)
    
    # Split logo into CHLOROS+ and CLI parts
    logo_lines = CHLOROS_LOGO.strip('\n').split('\n')
    
    # Split position (approximate position where CLI starts)
    # CHLOROS+ (including full +) ends around column 68, CLI starts around column 69
    # Keep gradient well away from CLI to prevent bleeding
    split_pos = 68
    
    result_lines = []
    for line in logo_lines:
        # Split each line into CHLOROS+ part and CLI part
        chloros_part = line[:split_pos]
        cli_part = line[split_pos:]
        
        # Apply gradient to CHLOROS+ part only
        chloros_colored = ""
        if ANSIColors.supports_color():
            length = len(chloros_part)
            for i, char in enumerate(chloros_part):
                if char.strip():  # Only color non-whitespace
                    # Calculate color interpolation
                    ratio = i / max(length - 1, 1)
                    r = int(GREEN[0] + (YELLOW_GREEN[0] - GREEN[0]) * ratio)
                    g = int(GREEN[1] + (YELLOW_GREEN[1] - GREEN[1]) * ratio)
                    b = int(GREEN[2] + (YELLOW_GREEN[2] - GREEN[2]) * ratio)
                    chloros_colored += f"\033[38;2;{r};{g};{b}m{char}"
                else:
                    chloros_colored += char
            chloros_colored += ANSIColors.RESET
            
            # Apply white color to CLI part
            cli_colored = f"{ANSIColors.BRIGHT_WHITE}{cli_part}{ANSIColors.RESET}"
        else:
            chloros_colored = chloros_part
            cli_colored = cli_part
        
        result_lines.append(chloros_colored + cli_colored)
    
    header = '\n'.join(result_lines)
    
    print("\n")
    print(header)
    
    # Subtitle with cyan color
    if ANSIColors.supports_color():
        subtitle_styled = f"{ANSIColors.CHLOROS_GREEN}{subtitle}{ANSIColors.RESET}"
        version_styled = f"{ANSIColors.CHLOROS_GRAY}v{version} | www.mapir.camera{ANSIColors.RESET}"
    else:
        subtitle_styled = subtitle
        version_styled = f"v{version} | www.mapir.camera"
    
    # Center the subtitle
    width = 80
    print(subtitle_styled.center(width + 20))  # +20 for ANSI codes
    print(version_styled.center(width + 20))
    print()


# ============================================================================
# Box Drawing
# ============================================================================

class Box:
    """Unicode box drawing characters"""
    # Single line
    HORIZONTAL = '─'
    VERTICAL = '│'
    TOP_LEFT = '┌'
    TOP_RIGHT = '┐'
    BOTTOM_LEFT = '└'
    BOTTOM_RIGHT = '┘'
    
    # Double line
    DOUBLE_HORIZONTAL = '═'
    DOUBLE_VERTICAL = '║'
    DOUBLE_TOP_LEFT = '╔'
    DOUBLE_TOP_RIGHT = '╗'
    DOUBLE_BOTTOM_LEFT = '╚'
    DOUBLE_BOTTOM_RIGHT = '╝'
    
    @staticmethod
    def create(content: str, width: int = 80, style: str = 'single', 
               color: str = ANSIColors.CHLOROS_GREEN) -> str:
        """
        Create a box around content
        
        Args:
            content: Text to put in box
            width: Width of box
            style: 'single' or 'double'
            color: ANSI color code
        
        Returns:
            Boxed text
        """
        if style == 'double':
            h, v = Box.DOUBLE_HORIZONTAL, Box.DOUBLE_VERTICAL
            tl, tr = Box.DOUBLE_TOP_LEFT, Box.DOUBLE_TOP_RIGHT
            bl, br = Box.DOUBLE_BOTTOM_LEFT, Box.DOUBLE_BOTTOM_RIGHT
        else:
            h, v = Box.HORIZONTAL, Box.VERTICAL
            tl, tr = Box.TOP_LEFT, Box.TOP_RIGHT
            bl, br = Box.BOTTOM_LEFT, Box.BOTTOM_RIGHT
        
        lines = content.split('\n')
        result = []
        
        # Top border
        result.append(f"{color}{tl}{h * (width - 2)}{tr}{ANSIColors.RESET}")
        
        # Content lines
        for line in lines:
            padding = width - len(line) - 4
            result.append(f"{color}{v}{ANSIColors.RESET} {line}{' ' * padding} {color}{v}{ANSIColors.RESET}")
        
        # Bottom border
        result.append(f"{color}{bl}{h * (width - 2)}{br}{ANSIColors.RESET}")
        
        return '\n'.join(result)


# ============================================================================
# Status Icons and Messages
# ============================================================================

class Icons:
    """Unicode icons for status messages"""
    import sys
    import os
    
    # Detect Windows PowerShell (poor Unicode support)
    _is_powershell = os.environ.get('PSModulePath') is not None
    
    if _is_powershell:
        # ASCII fallback for Windows PowerShell
        SUCCESS = '[OK]'
        ERROR = '[X]'
        WARNING = '[!]'
        INFO = '[i]'
        ARROW = '->'
        BULLET = '*'
        SPINNER = ['|', '/', '-', '\\']
    else:
        # Unicode for terminals with proper support
        SUCCESS = '✓'
        ERROR = '✗'
        WARNING = '⚠'
        INFO = 'ℹ'
        ARROW = '→'
        BULLET = '•'
        SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    DOTS = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    BOX_SPINNER = ['◰', '◳', '◲', '◱']


def print_success(message: str) -> None:
    """Print success message"""
    if ANSIColors.supports_color():
        print(f"{ANSIColors.CHLOROS_GREEN}{Icons.SUCCESS} {message}{ANSIColors.RESET}")
    else:
        print(f"[SUCCESS] {message}")


def print_error(message: str) -> None:
    """Print error message"""
    if ANSIColors.supports_color():
        print(f"{ANSIColors.BRIGHT_RED}{Icons.ERROR} {message}{ANSIColors.RESET}", file=sys.stderr)
    else:
        print(f"[ERROR] {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print warning message"""
    if ANSIColors.supports_color():
        print(f"{ANSIColors.CHLOROS_YELLOW}{Icons.WARNING} {message}{ANSIColors.RESET}")
    else:
        print(f"[WARNING] {message}")


def print_info(message: str) -> None:
    """Print info message"""
    if ANSIColors.supports_color():
        print(f"{ANSIColors.CHLOROS_GREEN}{Icons.INFO} {message}{ANSIColors.RESET}")
    else:
        print(f"[INFO] {message}")


def print_step(step: int, total: int, message: str) -> None:
    """Print step indicator"""
    if ANSIColors.supports_color():
        step_str = f"{ANSIColors.CHLOROS_GREEN}[{step}/{total}]{ANSIColors.RESET}"
        print(f"{step_str} {ANSIColors.BOLD}{message}{ANSIColors.RESET}")
    else:
        print(f"[{step}/{total}] {message}")


# ============================================================================
# Progress Bar
# ============================================================================

def print_progress_bar(percent: float, message: str = "", width: int = 50) -> None:
    """
    Print animated progress bar
    
    Args:
        percent: Progress percentage (0-100)
        message: Optional message to display
        width: Width of progress bar
    """
    filled = int(width * percent / 100)
    empty = width - filled
    
    if ANSIColors.supports_color():
        # Gradient bar from green to cyan
        bar_filled = f"{ANSIColors.CHLOROS_GREEN}{'█' * filled}{ANSIColors.RESET}"
        bar_empty = f"{ANSIColors.DIM}{'░' * empty}{ANSIColors.RESET}"
        percent_str = f"{ANSIColors.BOLD}{ANSIColors.CHLOROS_GREEN}{percent:5.1f}%{ANSIColors.RESET}"
        
        print(f"\r[{bar_filled}{bar_empty}] {percent_str} {message}", end='', flush=True)
    else:
        bar = '█' * filled + '░' * empty
        print(f"\r[{bar}] {percent:5.1f}% {message}", end='', flush=True)


# ============================================================================
# Spinner Animation
# ============================================================================

class Spinner:
    """Animated spinner for long-running operations"""
    
    def __init__(self, message: str = "Loading...", spinner_type: str = 'dots'):
        self.message = message
        self.spinner_type = spinner_type
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        if spinner_type == 'dots':
            self.frames = Icons.DOTS
        elif spinner_type == 'box':
            self.frames = Icons.BOX_SPINNER
        else:
            self.frames = Icons.SPINNER
    
    def _animate(self):
        """Animation loop"""
        for frame in itertools.cycle(self.frames):
            if not self.running:
                break
            
            if ANSIColors.supports_color():
                spinner = f"{ANSIColors.CHLOROS_GREEN}{frame}{ANSIColors.RESET}"
                msg = f"{ANSIColors.CHLOROS_GRAY}{self.message}{ANSIColors.RESET}"
                print(f"\r{spinner} {msg}", end='', flush=True)
            else:
                print(f"\r{frame} {self.message}", end='', flush=True)
            
            time.sleep(0.1)
    
    def start(self):
        """Start spinner animation"""
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
    
    def stop(self, success: bool = True, final_message: Optional[str] = None):
        """Stop spinner animation"""
        self.running = False
        if self.thread:
            self.thread.join()
        
        # Clear line
        print('\r' + ' ' * 100 + '\r', end='', flush=True)
        
        # Print final message
        if final_message:
            if success:
                print_success(final_message)
            else:
                print_error(final_message)


# ============================================================================
# Table Display
# ============================================================================

def print_table(headers: list, rows: list, colors: Optional[list] = None) -> None:
    """
    Print a formatted table
    
    Args:
        headers: List of column headers
        rows: List of row data (list of lists)
        colors: Optional list of colors for each column
    """
    if not rows:
        return
    
    # Calculate column widths
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Print header
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    if ANSIColors.supports_color():
        print(f"{ANSIColors.BOLD}{ANSIColors.CHLOROS_GREEN}{header_line}{ANSIColors.RESET}")
        print(f"{ANSIColors.CHLOROS_GRAY}{Box.HORIZONTAL * (sum(col_widths) + len(headers) * 2)}{ANSIColors.RESET}")
    else:
        print(header_line)
        print("-" * (sum(col_widths) + len(headers) * 2))
    
    # Print rows
    for row in rows:
        row_str = "  ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        print(row_str)


# ============================================================================
# Utility Functions
# ============================================================================

def clear_line():
    """Clear current line"""
    print('\r' + ' ' * 100 + '\r', end='', flush=True)


def print_divider(char: str = '─', width: int = 80, color: str = ANSIColors.CHLOROS_GRAY):
    """Print horizontal divider"""
    if ANSIColors.supports_color():
        print(f"{color}{char * width}{ANSIColors.RESET}")
    else:
        print(char * width)


def print_banner(text: str, width: int = 80):
    """Print text in a banner"""
    if ANSIColors.supports_color():
        print()
        print(f"{ANSIColors.CHLOROS_GREEN}{Box.HORIZONTAL * width}{ANSIColors.RESET}")
        print(f"{ANSIColors.BOLD}{ANSIColors.BRIGHT_WHITE}{text.center(width)}{ANSIColors.RESET}")
        print(f"{ANSIColors.CHLOROS_GREEN}{Box.HORIZONTAL * width}{ANSIColors.RESET}")
        print()
    else:
        print()
        print("=" * width)
        print(text.center(width))
        print("=" * width)
        print()


# ============================================================================
# Demo/Test Function
# ============================================================================

def demo():
    """Demonstrate all styling features"""
    
    # Enable Windows color support
    ANSIColors.supports_color()
    
    # Header
    print_header()
    
    # Status messages
    print_info("Initializing CHLOROS+ CLI...")
    time.sleep(0.5)
    print_success("Backend connected successfully")
    print_warning("Using cached credentials (offline mode)")
    print_error("Invalid project path")
    print()
    
    # Steps
    print_step(1, 3, "Loading project files")
    print_step(2, 3, "Applying calibration settings")
    print_step(3, 3, "Processing images")
    print()
    
    # Box
    box_content = "CHLOROS+ License Active\nSubscription: Professional\nExpires: 2025-12-31"
    print(Box.create(box_content, width=60, style='double', color=ANSIColors.CHLOROS_GREEN))
    print()
    
    # Table
    print_banner("PROCESSING RESULTS")
    headers = ["Image", "Status", "Time"]
    rows = [
        ["IMG_0001.tif", "✓ Complete", "2.3s"],
        ["IMG_0002.tif", "✓ Complete", "2.1s"],
        ["IMG_0003.tif", "✓ Complete", "2.4s"],
    ]
    print_table(headers, rows)
    print()
    
    # Progress bar demo
    print_info("Simulating processing...")
    for i in range(101):
        print_progress_bar(i, f"Processing image {i}/100")
        time.sleep(0.02)
    print()
    print()
    
    # Spinner demo
    spinner = Spinner("Loading project data...", spinner_type='dots')
    spinner.start()
    time.sleep(3)
    spinner.stop(success=True, final_message="Project loaded successfully")
    
    print()
    print_divider()
    print()


if __name__ == '__main__':
    demo()

