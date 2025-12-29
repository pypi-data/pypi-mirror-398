"""Arrow-key selector component for Zen CLI."""
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText, ANSI
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from io import StringIO


def render_rich_to_ansi(renderable) -> str:
    """Render a Rich object to ANSI string."""
    string_io = StringIO()
    console = Console(file=string_io, force_terminal=True, width=80)
    console.print(renderable)
    return string_io.getvalue()


class Selector:
    """Interactive arrow-key selector with Rich styling."""
    
    def __init__(self, items: list[dict], display_fn: callable, title: str = "Select an item", 
                 color: str = "cyan"):
        self.items = items
        self.display_fn = display_fn
        self.title = title
        self.color = color
        self.selected_index = 0
        self.result = None
        self.cancelled = False
    
    def _render(self) -> str:
        """Render the selector using Rich."""
        lines = []
        
        for i, item in enumerate(self.items):
            is_selected = i == self.selected_index
            display_text = self.display_fn(item, is_selected)
            
            if is_selected:
                line = Text()
                line.append("  ❯ ", style=f"bold {self.color}")
                line.append(display_text, style=f"bold white on dark_{self.color}" if self.color != "cyan" else "bold white on dark_blue")
                line.append(" ", style=f"on dark_{self.color}" if self.color != "cyan" else "on dark_blue")
            else:
                line = Text()
                line.append("    ", style="dim")
                line.append(display_text, style="white")
            
            lines.append(line)
        
        # Build the content
        content = Text()
        for i, line in enumerate(lines):
            content.append_text(line)
            if i < len(lines) - 1:
                content.append("\n")
        
        # Create panel
        panel = Panel(
            content,
            title=f"[bold]{self.title}[/]",
            subtitle="[dim]↑↓ navigate • Enter select • Esc cancel[/]",
            border_style=self.color,
            box=ROUNDED,
            padding=(1, 2),
        )
        
        return render_rich_to_ansi(panel)
    
    def run(self) -> dict | None:
        """Run the selector and return selected item or None if cancelled."""
        if not self.items:
            return None
        
        # Key bindings
        kb = KeyBindings()
        
        @kb.add('up')
        @kb.add('k')
        def move_up(event):
            self.selected_index = max(0, self.selected_index - 1)
        
        @kb.add('down')
        @kb.add('j')
        def move_down(event):
            self.selected_index = min(len(self.items) - 1, self.selected_index + 1)
        
        @kb.add('enter')
        def select(event):
            self.result = self.items[self.selected_index]
            event.app.exit()
        
        @kb.add('escape')
        @kb.add('q')
        def cancel(event):
            self.cancelled = True
            event.app.exit()
        
        @kb.add('c-c')
        def ctrl_c(event):
            self.cancelled = True
            event.app.exit()
        
        # Layout with ANSI rendering
        def get_content():
            return ANSI(self._render())
        
        layout = Layout(
            Window(
                content=FormattedTextControl(get_content),
                wrap_lines=False,
            )
        )
        
        # Application
        app = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=False,
            mouse_support=True,
        )
        
        app.run()
        
        if self.cancelled:
            return None
        return self.result


def select_chat(chats: list[dict]) -> dict | None:
    """Select a chat from the list using arrow keys."""
    if not chats:
        return None
    
    def display(chat, is_selected):
        title = chat.get('title', 'Untitled')[:42]
        updated = chat.get('updatedAt', '')[:10]
        return f"{title:<44} {updated}"
    
    selector = Selector(chats, display, title="💬 Select a Chat", color="cyan")
    return selector.run()


def select_note(notes: list[dict]) -> dict | None:
    """Select a note from the list using arrow keys."""
    if not notes:
        return None
    
    def display(note, is_selected):
        title = note.get('title', 'Untitled')[:32]
        keywords = ', '.join(note.get('keywords', [])[:2])[:20]
        if keywords:
            return f"{title:<34} [{keywords}]"
        return title
    
    selector = Selector(notes, display, title="📝 Select a Note", color="magenta")
    return selector.run()


def select_action(actions: list[tuple[str, str]], title: str = "Choose Action") -> str | None:
    """
    Select an action from a list.
    
    Args:
        actions: List of (action_key, action_label) tuples
        title: Title for the selector
    
    Returns:
        The action_key of the selected action, or None if cancelled
    """
    if not actions:
        return None
    
    items = [{'key': k, 'label': l} for k, l in actions]
    
    def display(item, is_selected):
        return item['label']
    
    selector = Selector(items, display, title=title, color="yellow")
    result = selector.run()
    return result['key'] if result else None


def main_menu() -> str | None:
    """Show main menu and return selected action."""
    actions = [
        ('new_chat', '💬  New Chat'),
        ('chats', '📂  Browse Chats'),
        ('new_note', '📝  New Note'),
        ('notes', '🗂️   Browse Notes'),
        ('search', '🔍  Search Notes'),
        ('logout', '🚪  Logout'),
        ('quit', '👋  Quit'),
    ]
    
    items = [{'key': k, 'label': l} for k, l in actions]
    
    def display(item, is_selected):
        return item['label']
    
    selector = Selector(items, display, title="Zen AI", color="cyan")
    result = selector.run()
    return result['key'] if result else None
