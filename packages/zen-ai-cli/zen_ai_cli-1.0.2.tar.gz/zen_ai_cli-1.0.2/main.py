#!/usr/bin/env python3
"""
Zen AI CLI - A beautiful terminal interface for Zen AI.

Usage:
    python main.py
"""
import sys
import ui
from config import session
from commands import auth, chats, notes
from selector import select_chat, select_note, select_action, main_menu


def handle_chats_menu():
    """Interactive chats menu with arrow key navigation."""
    chat_list = chats.list_chats()
    if not chat_list:
        ui.muted("No chats yet. Create one first!")
        ui.console.input("\n  Press Enter to continue...")
        return
    
    ui.console.print()
    selected = select_chat(chat_list)
    
    if selected:
        action = select_action([
            ('open', f"💬 Open: {selected.get('title', 'Untitled')[:35]}"),
            ('delete', '🗑️  Delete this chat'),
            ('back', '← Back'),
        ], title="What do you want to do?")
        
        if action == 'open':
            chats.open_chat(selected.get('id'))
        elif action == 'delete':
            chats.delete_chat(selected.get('id'))


def handle_notes_menu():
    """Interactive notes menu with arrow key navigation."""
    notes_list = notes.list_notes()
    if not notes_list:
        ui.muted("No notes yet. Create one first!")
        ui.console.input("\n  Press Enter to continue...")
        return
    
    ui.console.print()
    selected = select_note(notes_list)
    
    if selected:
        action = select_action([
            ('view', f"📄 View: {selected.get('title', 'Untitled')[:35]}"),
            ('edit', '✏️  Edit this note'),
            ('delete', '🗑️  Delete this note'),
            ('back', '← Back'),
        ], title="What do you want to do?")
        
        if action == 'view':
            notes.view_note(selected.get('id'))
            ui.console.input("\n  Press Enter to continue...")
        elif action == 'edit':
            notes.edit_note(selected.get('id'))
        elif action == 'delete':
            notes.delete_note(selected.get('id'))


def handle_search():
    """Handle note search."""
    ui.console.print()
    query = ui.prompt("🔍 Search query").strip()
    if not query:
        return
    
    results = notes.search_notes(query)
    if results:
        ui.console.print()
        selected = select_note(results)
        if selected:
            notes.view_note(selected.get('id'))
            ui.console.input("\n  Press Enter to continue...")
    else:
        ui.muted(f"No notes found for '{query}'")
        ui.console.input("\n  Press Enter to continue...")


def main_loop():
    """Main application loop with menu navigation."""
    while True:
        try:
            ui.clear()
            ui.show_logo()
            ui.console.print(f"  [dim]Logged in as[/] [bold green]{session.email}[/]")
            ui.console.print()
            
            # Show main menu
            action = main_menu()
            
            if action is None or action == 'quit':
                ui.console.print()
                ui.muted("Goodbye! 👋")
                return False  # Exit completely
            
            if action == 'logout':
                auth.logout()
                return True  # Return to auth
            
            if action == 'new_chat':
                result = chats.create_chat()
                continue
            
            if action == 'chats':
                handle_chats_menu()
                continue
            
            if action == 'new_note':
                notes.create_note()
                continue
            
            if action == 'notes':
                handle_notes_menu()
                continue
            
            if action == 'search':
                handle_search()
                continue
                
        except KeyboardInterrupt:
            ui.console.print()
            continue
        except EOFError:
            return False


def run():
    """Entry point for the CLI."""
    ui.clear()
    ui.show_logo()
    
    # Check for saved session
    if session.is_authenticated():
        # Skip welcome, go straight to main menu
        pass
    else:
        ui.show_welcome()
        
        # Auth loop
        while not session.is_authenticated():
            result = auth.auth_menu()
            if result is None:  # User chose to exit
                ui.muted("Goodbye! 👋")
                return
            if result:
                break
    
    # Main app loop
    while True:
        should_continue = main_loop()
        
        if not should_continue:
            break
        
        # User logged out, show auth again
        if not session.is_authenticated():
            ui.clear()
            ui.show_logo()
            ui.show_welcome()
            
            result = auth.auth_menu()
            if result is None:
                ui.muted("Goodbye! 👋")
                return


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        ui.console.print()
        ui.muted("Goodbye! 👋")
        sys.exit(0)
