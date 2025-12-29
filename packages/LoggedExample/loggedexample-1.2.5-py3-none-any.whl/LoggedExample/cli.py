#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import sys
import os
from ChronicleLogger import ChronicleLogger

class Example:
    CLASSNAME = "Example"
    MAJOR_VERSION = 1
    MINOR_VERSION = 2
    PATCH_VERSION = 5

    def __init__(self, basedir="/var/app", logger=None):
        """
        Initializes the Example object with base directory and logger.
        """
        self.basedir = basedir
        self.logger = logger

    @staticmethod
    def class_version():
        return f"{Example.CLASSNAME} v{Example.MAJOR_VERSION}.{Example.MINOR_VERSION}.{Example.PATCH_VERSION}"

    def log(self, message, level="INFO", component=""):
        """Logs a message using the provided logger if available."""
        if self.logger:
            self.logger.log_message(message, level, component)
        else:
            print(message)  # Fallback to print if no logger is provided

    def info(self):
        print("This is an example app using ChronicleLogger")
        self.log("Example info command executed", "INFO", "command")


def debug_dump_chroniclelogger(logger):
    """Print detailed debug information about the ChronicleLogger instance + environment"""
    print("\n" + "="*80)
    print("  CHRONICLELOGGER + ENVIRONMENT DEBUG DUMP  ".center(80, "="))
    print("="*80)

    # ── ChronicleLogger state ────────────────────────────────────────────────
    logger_info = [
        ("class_version()",      ChronicleLogger.class_version()),
        ("logName()",            logger.logName()),
        ("baseDir()",            logger.baseDir()),
        ("logDir()",             logger.logDir()),
        ("current logfile",      logger._get_log_filename() if hasattr(logger, '_get_log_filename') else "N/A"),
        ("isDebug()",            logger.isDebug()),
        ("inPython()",           logger.inPython()),
        ("inVenv()",             logger.inVenv()),
        ("venv_path()",          logger.venv_path()),
        ("inPyenv()",            logger.inPyenv()),
        ("pyenvVenv()",          logger.pyenvVenv()),
        ("inConda()",            logger.inConda()),
        ("condaPath()",          logger.condaPath()),
        ("is_root()",            ChronicleLogger.is_root()),
        ("root_or_sudo()",       ChronicleLogger.root_or_sudo() if hasattr(ChronicleLogger, 'root_or_sudo') else "N/A"),
    ]

    print(" ChronicleLogger State ".center(80, "-"))
    for name, value in logger_info:
        print(f"  {name:26} → {value!r}")
    print()

    # ── Environment & Python context ─────────────────────────────────────────
    env_vars = [
        ("sys.executable",       sys.executable),
        ("os.getcwd()",          os.getcwd()),
        ("sys.version",          sys.version.split('\n')[0]),
        ("PYTHONPATH",           os.environ.get("PYTHONPATH", "not set")),
        ("VIRTUAL_ENV",          os.environ.get("VIRTUAL_ENV", "not set")),
        ("CONDA_DEFAULT_ENV",    os.environ.get("CONDA_DEFAULT_ENV", "not set")),
        ("CONDA_PREFIX",         os.environ.get("CONDA_PREFIX", "not set")),
        ("CONDA_PROMPT_MODIFIER",os.environ.get("CONDA_PROMPT_MODIFIER", "not set")),
        ("PYENV_VERSION",        os.environ.get("PYENV_VERSION", "not set")),
        ("PYENV_ROOT",           os.environ.get("PYENV_ROOT", "not set")),
        ("PATH (first entry)",   os.environ.get("PATH", "").split(os.pathsep)[0] if os.environ.get("PATH") else "not set"),
    ]

    print(" Environment & Python Context ".center(80, "-"))
    for name, value in env_vars:
        print(f"  {name:26} → {value!r}")
    print()

    print("="*80 + "\n")


def usage(appname):
    print(f"Usage: {appname} info")
    print(f"       DEBUG=show {appname} info    ← shows detailed logger + environment debug")


def main():
    appname = 'LoggedExample'
    MAJOR_VERSION = 1
    MINOR_VERSION = 2
    PATCH_VERSION = 5

    # Create logger instance
    logger = ChronicleLogger(logname=appname)
    appname = logger.logName()       # Use kebab-case version if applicable
    basedir = logger.baseDir()

    # === DEBUG MODE: Detailed dump ===
    if logger.isDebug():
        logger.log_message(
            f"{appname} v{MAJOR_VERSION}.{MINOR_VERSION}.{PATCH_VERSION} ({__file__}) started in DEBUG mode",
            level="DEBUG",
            component="main"
        )
        logger.log_message(f">> {ChronicleLogger.class_version()}", component="main")

        debug_dump_chroniclelogger(logger)

    if len(sys.argv) < 2:
        usage(appname)
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "info":
        app = Example(basedir=basedir, logger=logger)
        app.info()
    else:
        usage(appname)
        sys.exit(1)


if __name__ == '__main__':
    main()