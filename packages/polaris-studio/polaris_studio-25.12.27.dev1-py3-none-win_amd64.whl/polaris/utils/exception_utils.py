# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import os
import sys
import tempfile
import traceback

# Configuration
SHOW_FULL_TRACEBACK = False  # Set to True to show full traceback for debugging
SHOW_HINTS = True  # Set to True to show helpful hints for common errors


class NotAPolarisProjectError(Exception):
    """Raised when the current directory is not a Polaris project."""

    def __init__(self, message, dir=None):
        super().__init__(message)
        self.dir = dir


class SQLError(Exception):
    """Raised when running sql that doesn't work"""

    def __init__(self, message, sql=None):
        super().__init__(message)
        self.sql = sql


class FriendlyExceptionHandler:
    ERROR_MESSAGES = {
        "NotAPolarisProjectError": lambda x: {
            "message": f"❗ Not a Polaris project: {x.dir}",
            "hints": [
                "Make sure you are correctly specifying the root directory of a Polaris project.",
                "This directory should have a polaris.yaml file in it.",
                "Use '--data_dir=<path>' if you are using the CLI.",
            ],
        },
        "SQLError": lambda x: {
            "message": f"❗ SQL Error while running: {x.sql}",
            "hints": [
                "Check the given sql carefully for errors",
                "Have you run model.upgrade() or 'polaris upgrade' on your projct?",
            ],
        },
    }

    def __init__(self, show_traceback=False, show_hints=True):
        self.show_traceback = show_traceback
        self.show_hints = show_hints

    def format_exception(self, exc_type, exc_value, exc_traceback):
        """
        Format an exception into a user-friendly message
        """
        exception_name = exc_type.__name__

        # Get error info from our mapping (or a default)
        default = {"message": f"❗ {exception_name}", "hints": ["This is an unexpected error type"]}
        error_info = self.ERROR_MESSAGES.get(exception_name, default)

        # Allow the error info to include actual attributes from the error (if it is callable)
        if callable(error_info):
            error_info = error_info(exc_value)

        # Build the friendly error message
        lines = [""]
        line_len = max(len(e) for e in error_info["message"].split("\n")) + 2
        lines.append("-" * line_len)
        lines.append(f'{error_info["message"]}')
        lines.append("-" * line_len)

        lines.append(f"\n{exc_value}\n")

        with tempfile.NamedTemporaryFile(delete=False, prefix="polaris_error_", suffix=".log", mode="w") as f:
            f.write("UNHANDLED EXCEPTION\n")
            f.write("=" * 40 + "\n\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            logfile = f.name

        # Add hints if enabled
        if self.show_hints and error_info["hints"]:
            lines.append("💡 Helpful Hints:")
            for hint in error_info["hints"]:
                lines.append(f"   • {hint}")
            lines.append("")

        # Optionally show full traceback
        if self.show_traceback:
            lines.append("📋 Full Traceback (for debugging):")
            lines.extend(traceback.format_exception(exc_type, exc_value, exc_traceback))
        else:
            lines.append(f"📋 Debug information is saved to: {logfile}\n")

        return "\n".join(lines)


def setup_notebook_exception_handler(show_traceback=SHOW_FULL_TRACEBACK, show_hints=SHOW_HINTS):
    from IPython.core.interactiveshell import InteractiveShell  # delay import

    handler = FriendlyExceptionHandler(show_traceback, show_hints)

    def custom_exception_handler(self, exc_type, exc_value, exc_traceback, tb_offset=None):
        if exc_type is KeyboardInterrupt:
            return None  # Don't intercept keyboard interrupts

        friendly_message = handler.format_exception(exc_type, exc_value, exc_traceback)
        print(friendly_message, file=sys.stderr)

        return None  # Return None to prevent default traceback

    # Get the IPython instance and set custom exception handler
    ip = InteractiveShell.instance()
    ip.set_custom_exc((Exception,), custom_exception_handler)


# For regular Python applications
def setup_application_exception_handler(show_traceback=SHOW_FULL_TRACEBACK, show_hints=SHOW_HINTS):
    handler = FriendlyExceptionHandler(show_traceback, show_hints)

    def custom_excepthook(exc_type, exc_value, exc_traceback):
        """Custom exception hook for sys.excepthook"""
        if exc_type is KeyboardInterrupt:
            # Don't intercept keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        friendly_message = handler.format_exception(exc_type, exc_value, exc_traceback)
        print(friendly_message, file=sys.stderr)

    sys.excepthook = custom_excepthook


# Convenience function - auto-detects environment
def install_friendly_errors(show_traceback=SHOW_FULL_TRACEBACK, show_hints=SHOW_HINTS):
    if os.environ.get("FRIENDLY_ERRORS_DISABLED", "0") == "1":
        print("⚠️ Friendly exception handler is disabled via FRIENDLY_ERRORS_DISABLED")
        return
    try:
        # Try to get IPython instance - if this works, we're in a notebook
        get_ipython()
        setup_notebook_exception_handler(show_traceback, show_hints)
    except NameError:
        # Not in IPython/Jupyter, use regular sys.excepthook
        setup_application_exception_handler(show_traceback, show_hints)

    print("✅ Friendly exception handler installed! [to disable set FRIENDLY_ERRORS_DISABLED=1 before importing]")
