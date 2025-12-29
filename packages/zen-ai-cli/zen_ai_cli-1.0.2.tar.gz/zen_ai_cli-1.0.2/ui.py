"""UI components and styling for Zen CLI."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.box import ROUNDED, MINIMAL, HEAVY
from rich.style import Style
from rich.theme import Theme
from io import StringIO

# Custom theme
zen_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red bold",
    "highlight": "magenta",
    "muted": "dim white",
    "accent": "bold cyan",
})

console = Console(theme=zen_theme)

# ─────────────────────────────────────────────────────────────────────────────
# Branding
# ─────────────────────────────────────────────────────────────────────────────

LOGO = """
╭─────────────────────────────────────╮
│                                     │
│      ███████╗███████╗███╗   ██╗     │
│      ╚══███╔╝██╔════╝████╗  ██║     │
│        ███╔╝ █████╗  ██╔██╗ ██║     │
│       ███╔╝  ██╔══╝  ██║╚██╗██║     │
│      ███████╗███████╗██║ ╚████║     │
│      ╚══════╝╚══════╝╚═╝  ╚═══╝     │
│                                     │
│          AI Assistant CLI           │
╰─────────────────────────────────────╯
"""

def show_logo():
    """Display the Zen logo."""
    console.print(LOGO, style="bold cyan")


def show_welcome():
    """Display welcome message."""
    console.print()
    console.print("  Welcome to [bold cyan]Zen AI[/] — Your personal AI assistant", style="white")
    console.print("  Type [bold green]/help[/] for commands or just start chatting", style="muted")
    console.print()


# ─────────────────────────────────────────────────────────────────────────────
# Status & Messages
# ─────────────────────────────────────────────────────────────────────────────

def success(message: str):
    """Show success message."""
    console.print(f"  [success]✓[/] {message}")


def error(message: str):
    """Show error message."""
    console.print(f"  [error]✗[/] {message}")


def info(message: str):
    """Show info message."""
    console.print(f"  [info]ℹ[/] {message}")


def warning(message: str):
    """Show warning message."""
    console.print(f"  [warning]⚠[/] {message}")


def muted(message: str):
    """Show muted/dim message."""
    console.print(f"  {message}", style="muted")


# ─────────────────────────────────────────────────────────────────────────────
# Input
# ─────────────────────────────────────────────────────────────────────────────

def prompt(label: str = "›", style: str = "bold cyan") -> str:
    """Get user input with styled prompt."""
    console.print()
    return console.input(f"[{style}]{label}[/] ")


def prompt_password(label: str = "Password") -> str:
    """Get password input (hidden)."""
    from getpass import getpass
    console.print(f"  [muted]{label}:[/] ", end="")
    return getpass("")


def confirm(message: str, default: bool = False) -> bool:
    """Ask for confirmation."""
    suffix = "[Y/n]" if default else "[y/N]"
    response = prompt(f"{message} {suffix}", style="yellow").strip().lower()
    if not response:
        return default
    return response in ("y", "yes")


# ─────────────────────────────────────────────────────────────────────────────
# Display Components
# ─────────────────────────────────────────────────────────────────────────────

def show_help():
    """Display help menu."""
    console.print()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Command", style="bold green")
    table.add_column("Description", style="white")
    
    commands = [
        ("/help", "Show this help menu"),
        ("/chats", "Browse & manage chats (↑↓ to navigate)"),
        ("/new", "Create a new chat"),
        ("", ""),
        ("/notes", "Browse & manage notes (↑↓ to navigate)"),
        ("/note new", "Create a new note"),
        ("/search <query>", "Search notes"),
        ("", ""),
        ("/logout", "Log out"),
        ("/quit", "Exit the CLI"),
    ]
    
    for cmd, desc in commands:
        if cmd:
            table.add_row(cmd, desc)
        else:
            table.add_row("", "")
    
    console.print(Panel(table, title="[bold]Commands[/]", border_style="cyan", box=ROUNDED))
    console.print()
    muted("💡 Tip: Just type a message to start a quick chat!")


def show_chat_list(chats: list[dict]):
    """Display list of chats."""
    console.print()
    if not chats:
        muted("No chats yet. Type [bold green]/new[/] to create one.")
        return
    
    table = Table(box=MINIMAL, show_header=True, header_style="bold cyan")
    table.add_column("#", style="muted", width=4)
    table.add_column("Title", style="white")
    table.add_column("Updated", style="muted", width=20)
    table.add_column("ID", style="dim", width=24)
    
    for i, chat in enumerate(chats[:20], 1):
        title = chat.get("title", "Untitled")[:40]
        updated = chat.get("updatedAt", "")[:10]
        chat_id = chat.get("id", "")[:22]
        table.add_row(str(i), title, updated, chat_id)
    
    console.print(Panel(table, title="[bold]Your Chats[/]", border_style="cyan", box=ROUNDED))
    console.print()


def show_notes_list(notes: list[dict]):
    """Display list of notes."""
    console.print()
    if not notes:
        muted("No notes yet. Type [bold green]/note new[/] to create one.")
        return
    
    table = Table(box=MINIMAL, show_header=True, header_style="bold cyan")
    table.add_column("#", style="muted", width=4)
    table.add_column("Title", style="white")
    table.add_column("Keywords", style="magenta", width=30)
    table.add_column("ID", style="dim", width=24)
    
    for i, note in enumerate(notes[:20], 1):
        title = note.get("title", "Untitled")[:35]
        keywords = ", ".join(note.get("keywords", [])[:3])[:28]
        note_id = note.get("id", "")[:22]
        table.add_row(str(i), title, keywords, note_id)
    
    console.print(Panel(table, title="[bold]Your Notes[/]", border_style="magenta", box=ROUNDED))
    console.print()


def show_note(note: dict):
    """Display a single note."""
    console.print()
    title = note.get("title", "Untitled")
    content = note.get("content", note.get("excerpt", ""))
    keywords = note.get("keywords", [])
    trigger_words = note.get("triggerWords", [])
    
    # Build content display
    parts = []
    if content:
        parts.append(content)
    
    if keywords:
        parts.append(f"\n[magenta]Keywords:[/] {', '.join(keywords)}")
    
    if trigger_words:
        parts.append(f"[yellow]Triggers:[/] {', '.join(trigger_words)}")
    
    display_text = "\n".join(parts) if parts else "[muted]Empty note[/]"
    
    console.print(Panel(
        display_text,
        title=f"[bold]{title}[/]",
        subtitle=f"[dim]{note.get('id', '')}[/]",
        border_style="magenta",
        box=ROUNDED
    ))
    console.print()


def show_message(role: str, content: str, in_chat: bool = True):
    """Display a chat message."""
    prefix = "  " if in_chat else ""
    
    if role == "user":
        console.print(f"{prefix}[bold green]You ›[/] {content}")
    elif role == "assistant":
        console.print(f"{prefix}[bold cyan]Zen ›[/]")
        # Render markdown for assistant responses
        md = Markdown(content)
        string_io = StringIO()
        temp_console = Console(file=string_io, force_terminal=True, width=70)
        temp_console.print(md)
        rendered = string_io.getvalue()
        for line in rendered.rstrip().split('\n'):
            console.print(f"{prefix}      {line}")
        console.print()
    else:
        console.print(f"{prefix}[bold yellow]System ›[/] [dim]{content}[/]")


def show_chat_header(chat: dict):
    """Display chat header."""
    title = chat.get("title", "New Chat")
    console.print()
    console.print(Panel(
        f"[bold white]💬 {title}[/]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    if chat.get("systemPrompt"):
        console.print(f"  [dim italic]{chat['systemPrompt'][:80]}[/]")
    console.print()


def show_chat_footer():
    """Display chat footer."""
    console.print()
    console.print("  [dim]─" * 40 + "[/]")
    console.print()
    console.print()


def show_spinner(message: str = "Thinking..."):
    """Create a spinner context manager."""
    from rich.spinner import Spinner
    from rich.live import Live
    
    spinner = Spinner("dots", text=f" [cyan]{message}[/]")
    return Live(spinner, console=console, transient=True)


def clear():
    """Clear the console."""
    console.clear()


def divider():
    """Print a divider line."""
    console.print("  [muted]─" * 50 + "[/]")
