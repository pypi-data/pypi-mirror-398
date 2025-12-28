"""repl_entry.py

This module is the entry to the AitoCoder REPL.
It handles user authentication, model initialization,
and starts the REPL session.
"""
import sys
import os

# Parse flag before importing modules that suppress warnings
# (By default, warnings are suppressed for cleaner user experience.)
if "--show-warning" not in sys.argv:
    os.environ["AITOCODER_SUPPRESS_WARNINGS"] = "1"
else:
    sys.argv.remove("--show-warning")

from importlib.metadata import version
from login_modules import Auth, ModelManager
from autocoder.chat_auto_coder import main as autocoder_repl

from rich.console import Console
from rich.panel import Panel

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML

from global_utils import clear_screen, clear_lines, COLORS

console = Console()
BLUE = COLORS.BLUE
ORANGE = COLORS.ORANGE

# Get version from package metadata synced with pyproject.toml
try:
    __version__ = version("aitocoder")
except Exception:
    __version__ = "v.beta"


def ac_welcome():
    """Display welcome panel"""
    WelcomePanel = Panel(f"[bold {BLUE}]Welcome to[/bold {BLUE}]\n"
                         f"[bold][{ORANGE}]AitoCoder CLI - REPL[/bold][/{ORANGE}]\n"
                         f"[{ORANGE}]v{__version__}[/{ORANGE}]\n"
                        #  f"[{BLUE}]Type /help to see available commands.[/{BLUE}]\n"
                         f"[{BLUE}]─────────────────────────────────────[/{BLUE}]\n"
                         f"[{ORANGE}]>>[/{ORANGE}] [{BLUE}]Visit https://aitocoder.com \n  for sign-up, web platform and more.[/{BLUE}]\n\n"
                         f"[{ORANGE}]>>[/{ORANGE}] [{BLUE}]Ctrl+C to force quit a task.[/{BLUE}]\n"
                         f"[{ORANGE}]>>[/{ORANGE}] [{BLUE}]Ctrl+D to exit.[/{BLUE}]",
                         title="[italic]beta[/italic]", title_align="right",
                         width=42, border_style=f"{BLUE}",
                         padding=(0,1),
                         highlight=False)
    console.print(WelcomePanel)
    console.print()


def chat_login():
    """Login flow with authentication and model initialization"""
    auth = Auth()

    # Check existing authentication
    if auth.is_authenticated():
        with console.status(f"[{BLUE}]Fetching user info...[/{BLUE}]"):
            user = auth.get_user_info()
        if not user:
            console.print("[red]Failed to fetch user info[/red]")
            return False
        username = user.get('user', {}).get('userName', 'User')
        console.print(f"[{BLUE}]\u00B7 Hello, [/{BLUE}]{username}!", highlight=False)
        console.print(f"[{BLUE}]──────────────────────────────────────[/{BLUE}]")
        console.print(f"[{BLUE}]\u00B7 Type /help to see available commands.[/{BLUE}]\n")
        return True

    # Login
    while True:
        # Prompt for credentials
        try:
            username = prompt(
                HTML(f'<style fg="{BLUE}">Username:</style> '),
            ).strip()

            password = prompt(
                HTML(f'<style fg="{BLUE}">Password:</style> '),
                is_password=True,
            )
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[red]Login cancelled![/red]\n")
            return False

        # Clear the username and password lines
        clear_lines(console, 2)

        # Authenticate
        with console.status(f"[{BLUE}]Logging in...[/{BLUE}]"):
            login_success = auth.login(username, password)

        if not login_success:
            console.print("[red]Login failed[/red]")
            console.print(f"[dim]Press Ctrl+C or Ctrl+D to exit[/dim]\n")
            continue  # Retry login

        break

    # Initialize models
    with console.status(f"[{BLUE}]Initializing models...[/{BLUE}]"):
        auth_data = auth.storage.load()
        token = auth_data.get("token")
        manager = ModelManager()
        init_success = manager.initialize_models(token)

    if init_success:
        console.print(f"\n[italic {ORANGE}]You are all set![/italic {ORANGE}]")
        return True
    else:
        console.print("\n[yellow]Model initialization failed[/yellow]")
        return True


def main():
    """Entry point"""
    try:
        ac_welcome()
        if not chat_login():
            sys.exit(0)
        autocoder_repl()
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
