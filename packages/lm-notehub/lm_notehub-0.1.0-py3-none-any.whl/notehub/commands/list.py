"""List command - display all note-issues."""

import sys
from argparse import Namespace

from ..context import StoreContext
from ..gh_wrapper import GhError, list_issues
from ..utils import format_note_header


def run(args: Namespace) -> int:
    """
    Execute list command.
    
    Lists all note-issues (filtered by 'notehub' label).
    Displays note-header and URL for each.
    
    Returns:
        0 on success, 1 on error
    """
    context = StoreContext.resolve(args)
    
    try:
        # Fetch all notehub issues (auto-filtered by label)
        issues = list_issues(context.host, context.org, context.repo)
        
        # Display each issue (same format as show command)
        for i, issue in enumerate(issues):
            # Blank line between issues (except before first)
            if i > 0:
                print()
            
            # Format and display note-header
            print(format_note_header(issue))
            
            # Display URL (indented with 2 spaces, matching show command)
            print(f"  {issue['url']}")
        
        return 0
        
    except GhError as e:
        # Error message already printed to stderr by gh_wrapper
        return e.returncode
