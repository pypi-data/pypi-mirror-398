import argparse
from typing import Any
import logging
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.display import display, Markdown

from .load import load as core_load
from .search import search as core_search
from .errors import KaggleEaseError

logger = logging.getLogger(__name__)

@magics_class
class KaggleMagics(Magics):
    def __init__(self, shell: Any) -> None:
        super(KaggleMagics, self).__init__(shell)
        # Don't pollute user namespace on initialization

    @line_magic
    def kaggle(self, line: str) -> None:
        """
        A magic command to interact with the KaggleEase library.
        
        Usage:
            %kaggle load <dataset> [--file <filename>] [--as <varname>]
            %kaggle preview <dataset> [--file <filename>]
            %kaggle search <query>
        """
        parser = argparse.ArgumentParser(prog="%kaggle", add_help=False)
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Load command
        load_parser = subparsers.add_parser("load", help="Load a dataset")
        load_parser.add_argument("dataset", type=str, help="Dataset handle (e.g., 'titanic')")
        load_parser.add_argument("--file", type=str, help="Specific file to load")
        load_parser.add_argument("--as", dest="dest_var", type=str, default="data", help="Variable name to store the DataFrame in")
        load_parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds for the operation")

        # Preview command
        preview_parser = subparsers.add_parser("preview", help="Preview a dataset")
        preview_parser.add_argument("dataset", type=str, help="Dataset handle")
        preview_parser.add_argument("--file", type=str, help="Specific file to preview")
        preview_parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds for the operation")

        # Search command
        search_parser = subparsers.add_parser("search", help="Search for datasets")
        search_parser.add_argument("query", type=str, help="Search query")
        search_parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds for the search operation")
        search_parser.add_argument("--top", type=int, default=5, help="Maximum number of results to return")

        try:
            # Manually handle empty line or -h/--help
            if not line.strip() or line.strip() in ('-h', '--help'):
                display(Markdown(f"<pre>{parser.format_help()}</pre>"))
                return

            args = parser.parse_args(line.split())

            if args.command == "load":
                df = core_load(args.dataset, file=args.file, timeout=args.timeout)
                self.shell.user_ns[args.dest_var] = df
                logger.info(f"Dataset loaded into variable '{args.dest_var}'.")
                display(df.head(5))

            elif args.command == "preview":
                df = core_load(args.dataset, file=args.file, timeout=args.timeout)
                logger.info("Previewing dataset:")
                display(df.head(5))
                
            elif args.command == "search":
                results = core_search(args.query, top=args.top, timeout=args.timeout)
                if results:
                    # Simple markdown table for display
                    md = "| Handle | Title | Size | Votes |\n"
                    md += "|---|---|---|---|\n"
                    for r in results:
                        md += f"| {r['handle']} | {r['title']} | {r['size']} | {r['votes']} |\n"
                    display(Markdown(md))

        except KaggleEaseError as e:
            msg = f"### ❌ KaggleEase Error\n\n**{e.message}**\n\n"
            if hasattr(e, 'fix_suggestion') and e.fix_suggestion:
                msg += f"> **💡 Fix Suggestion:** {e.fix_suggestion}\n\n"
            if hasattr(e, 'docs_link') and e.docs_link:
                msg += f"🔗 [Documentation]({e.docs_link})\n"
            display(Markdown(msg))
        except SystemExit:
            # Argparse calls SystemExit on --help or error, catch it to prevent kernel crash
            display(Markdown(f"<pre>{parser.format_help()}</pre>"))
        except Exception as e:
            # Catch any other unexpected errors
            display(Markdown(f"**An unexpected error occurred:** {e}"))

def register_magics() -> None:
    """
    Function to register the magics with IPython.

    This function attempts to register the KaggleMagics class with IPython
    if we're in an IPython environment. If not, it silently passes.
    """
    try:
        from IPython import get_ipython
        ipython = get_ipython()
        if ipython:
            ipython.register_magics(KaggleMagics)
    except ImportError:
        pass # Not in an IPython environment
