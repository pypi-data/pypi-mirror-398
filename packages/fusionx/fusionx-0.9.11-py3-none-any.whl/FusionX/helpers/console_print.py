import sys
import logging
import atexit
from datetime import datetime

_progress_active = False
_cursor_hidden = False

def hide_cursor():
    """Hide the terminal cursor"""
    global _cursor_hidden
    sys.stdout.write("\033[?25l")  # ANSI escape sequence to hide cursor
    sys.stdout.flush()
    _cursor_hidden = True

def show_cursor():
    """Show the terminal cursor"""
    global _cursor_hidden
    if _cursor_hidden:
        sys.stdout.write("\033[?25h")  # ANSI escape sequence to show cursor
        sys.stdout.flush()
        _cursor_hidden = False

# Ensure cursor is shown when the program exits
atexit.register(show_cursor)

def print_progress(message):
    global _progress_active
    
    # Hide cursor when starting to print progress
    if not _cursor_hidden:
        hide_cursor()
    
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    formatted_message = f"{timestamp}-FusionX: {message}"
    
    padding = " " * 5
    
    sys.stdout.write(f"\r{formatted_message}{padding}")
    sys.stdout.flush()
    _progress_active = True

def print_message(message):
    global _progress_active
    
    # Hide cursor when printing messages
    if not _cursor_hidden:
        hide_cursor()
    
    if _progress_active:
        sys.stdout.write("\n")
        sys.stdout.flush()
        _progress_active = False
    
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    formatted_message = f"{timestamp}-FusionX: {message}"
    print(formatted_message)

def finish_progress():
    global _progress_active
    
    if _progress_active:
        sys.stdout.write("\n")
        sys.stdout.flush()
        _progress_active = False

# Add a function to properly finish and restore cursor when program ends
def finalize():
    finish_progress()
    show_cursor()
