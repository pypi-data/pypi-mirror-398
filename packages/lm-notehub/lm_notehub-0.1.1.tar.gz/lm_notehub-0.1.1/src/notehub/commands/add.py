import sys
from argparse import Namespace

from ..context import StoreContext
from ..gh_wrapper import create_issue, ensure_label_exists, GhError


def run(args: Namespace) -> int:
    """
    Execute add command - create a new note-issue.

    Args:
        args: Parsed command-line arguments

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    context = StoreContext.resolve(args)

    # Ensure 'notehub' label exists before creating issue
    if not ensure_label_exists(
        context.host, context.org, context.repo,
        "notehub",
        "FFC107",  # Nice yellow color
        "Issues created by notehub CLI"
    ):
        print("Error: Could not create 'notehub' label", file=sys.stderr)
        return 1

    try:
        # Label exists, create issue with label
        create_issue(context.host, context.org, context.repo, interactive=True, labels=["notehub"])
        return 0

    except GhError as e:
        return e.returncode
