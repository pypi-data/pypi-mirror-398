"""Show command - display note-header and URLs for specified issues."""

import sys
from argparse import Namespace

from ..context import StoreContext
from ..gh_wrapper import GhError, get_issue
from ..utils import resolve_note_ident, format_note_header


def run(args: Namespace) -> int:
    """
    Execute show command.
    
    Displays note-header and URL for each specified note-ident.
    Continues processing all idents even if some fail.
    
    Returns:
        0 if all successful, 1 if any errors occurred
    """
    context = StoreContext.resolve(args)
    any_errors = False
    
    for i, ident in enumerate(args.note_idents):
        # Add blank line between issues (except before first)
        if i > 0:
            print()
        
        try:
            issue_num, error = resolve_note_ident(context, ident)
            
            if error:
                print(f"Error: {error}", file=sys.stderr)
                any_errors = True
                continue
            
            # Fetch full issue data (includes html_url which list_issues uses 'url')
            issue = get_issue(context.host, context.org, context.repo, issue_num)
            
            # Display note-header
            print(format_note_header(issue))
            
            # Display URL (indented with 2 spaces)
            url = issue["html_url"]
            print(f"  {url}")
            
        except GhError as e:
            print(f"Error processing '{ident}': {e.stderr.strip()}", file=sys.stderr)
            any_errors = True
    
    return 1 if any_errors else 0
