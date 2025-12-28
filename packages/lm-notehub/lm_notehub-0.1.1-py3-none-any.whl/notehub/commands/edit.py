"""Edit command - edit note-issue body in $EDITOR."""

import os
import subprocess
import sys
import tempfile
from argparse import Namespace

from ..context import StoreContext
from ..config import get_editor
from ..gh_wrapper import GhError, get_issue, update_issue
from ..utils import resolve_note_ident


def _prepare_editor_command(editor: str) -> list[str]:
    """
    Prepare editor command, adding -w flag for VS Code if needed.
    
    VS Code requires the -w flag to wait for the file to be closed before
    continuing, otherwise the script will immediately proceed without user input.
    
    Args:
        editor: Editor command (e.g., 'vim', 'code')
        
    Returns:
        List of command arguments
    """
    # Check if editor is VS Code (code, code.cmd, code.exe, or path containing 'code')
    if editor and 'code' in os.path.basename(editor).lower():
        # Add -w flag if not already present
        if '-w' not in editor and '--wait' not in editor:
            return [editor, '-w']
    
    return [editor]


def edit_in_temp_file(content: str, editor: str) -> str | None:
    """
    Open content in temporary file using editor.
    
    Args:
        content: Original content to edit
        editor: Editor command (e.g., 'vim', 'nano')
    
    Returns:
        Modified content if file was changed, None if unchanged or editor failed
    """
    # Create temp file with .md suffix for syntax highlighting
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Get original modification time
        original_mtime = os.path.getmtime(tmp_path)
        
        # Prepare editor command (add -w for VS Code)
        editor_cmd = _prepare_editor_command(editor)
        
        # Print helpful message for VS Code users
        if len(editor_cmd) > 1 and editor_cmd[1] == '-w':
            print("Opening in VS Code... Close the editor tab when done to continue.")
        
        # Open in editor
        try:
            result = subprocess.run([*editor_cmd, tmp_path], shell=True)
        except FileNotFoundError:
            if sys.platform == 'win32':
                print(f"Error: Editor '{editor}' not found. On Windows, try adding .exe to the EDITOR setting (e.g. 'vi.exe').", file=sys.stderr)
            else:
                print(f"Error: Editor '{editor}' not found. Please check your EDITOR environment variable or configuration.", file=sys.stderr)
            return None
        
        # Check if editor failed
        if result.returncode != 0:
            return None
        
        # Check if file was modified
        new_mtime = os.path.getmtime(tmp_path)
        if new_mtime == original_mtime:
            return None
        
        # Read modified content
        with open(tmp_path, 'r') as f:
            return f.read()
    
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def run(args: Namespace) -> int:
    """
    Execute edit command.
    
    Workflow:
    1. Resolve note-ident to issue number
    2. Fetch issue body
    3. Open in editor
    4. Detect changes
    5. Update if modified
    
    Returns:
        0 if successful, 1 if error
    """
    context = StoreContext.resolve(args)
    
    try:
        # Resolve note-ident
        issue_num, error = resolve_note_ident(context, args.note_ident)
        if error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        
        # Fetch current issue
        issue = get_issue(context.host, context.org, context.repo, issue_num)
        original_body = issue.get('body') or ''
        
        # Edit in $EDITOR
        editor = get_editor()
        modified_body = edit_in_temp_file(original_body, editor)
        
        if modified_body is None:
            print("No changes made.")
            return 0
        
        # Handle empty body - confirm with user
        if not modified_body.strip():
            try:
                confirm = input("Warning: Issue body is empty. Update anyway? [y/N] ")
                if confirm.lower() != 'y':
                    print("Update cancelled.")
                    return 0
            except (EOFError, KeyboardInterrupt):
                print("\nUpdate cancelled.")
                return 0
        
        # Update issue
        update_issue(context.host, context.org, context.repo, issue_num, modified_body)
        print(f"Updated issue #{issue_num}")
        return 0
        
    except GhError:
        # Error already printed to stderr by gh_wrapper
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 1
