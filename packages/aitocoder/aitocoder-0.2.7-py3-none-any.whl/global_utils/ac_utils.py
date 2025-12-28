from rich.console import Console

def clear_screen(console):
    """Clear the terminal screen and scrollback buffer."""
    console.clear()
    try:
        console.control('\033[3J')  # Clear scrollback buffer
        console.file.flush()  # Ensure immediate execution
    except:
        pass


def clear_lines(console, num_lines):
    """Clear the specified number of lines above the current cursor position.

    Args:
        console: Rich Console instance
        num_lines: Number of lines to clear (moving up from current position)
    """
    for _ in range(num_lines):
        console.file.write("\033[F")  # Move cursor up one line
        console.file.write("\033[2K")  # Clear entire line
    console.file.flush()  # Ensure immediate execution of control sequences
