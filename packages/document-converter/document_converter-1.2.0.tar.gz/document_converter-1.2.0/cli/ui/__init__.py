"""
UI Utilities - Terminal Management

Provides utilities for managing terminal state and cleanup.
"""
import sys
import os

def reset_terminal():
    """
    Reset terminal to a clean state.
    
    This ensures proper cleanup of:
    - Curses state (if used)
    - Colorama state (if used)
    - Input buffer
    - Screen buffer
    """
    try:
        # Try to cleanup curses if it was initialized
        try:
            import curses
            curses.endwin()
        except (ImportError, curses.error):
            pass  # Curses not used or not initialized
        
        # Try to cleanup colorama if it was used
        try:
            import colorama
            colorama.deinit()
        except (ImportError, AttributeError):
            pass  # Colorama not used or not initialized
        
        # Flush stdout and stderr
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Clear input buffer (platform-specific)
        if os.name == 'nt':  # Windows
            try:
                import msvcrt
                while msvcrt.kbhit():
                    msvcrt.getch()
            except ImportError:
                pass
        else:  # Unix-like
            try:
                import termios
                termios.tcflush(sys.stdin, termios.TCIOFLUSH)
            except (ImportError, termios.error):
                pass
        
        # Reset terminal settings to normal (Unix-like)
        if os.name != 'nt':
            try:
                os.system('stty sane')
            except:
                pass
        
    except Exception:
        # Silently ignore any errors during cleanup
        pass

def ensure_clean_exit():
    """
    Ensure clean terminal state on exit.
    
    This is a convenience wrapper that:
    1. Resets the terminal
    2. Prints a final newline for clean exit
    3. Flushes all buffers
    """
    reset_terminal()
    print()  # Final newline for clean exit
    sys.stdout.flush()