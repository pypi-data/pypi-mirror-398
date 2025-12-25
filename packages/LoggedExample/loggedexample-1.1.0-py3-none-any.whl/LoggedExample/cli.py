#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import sys
from ChronicleLogger import ChronicleLogger

class Example:
    # Remember to replace Example to name of the class
    CLASSNAME = "Example"
    MAJOR_VERSION = 1
    MINOR_VERSION = 1
    PATCH_VERSION = 0

    def __init__(self, basedir="/var/app",  logger=None):
        """
        Initializes the PyxPy object with source and target folder paths and sets up the logger.
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
        print("This is an example app")

def usage(appname):
    print(f"Usage: {appname} info")

def main():
    appname = 'LoggedExample'
    MAJOR_VERSION = 1
    MINOR_VERSION = 1
    PATCH_VERSION = 0

    # Create logger instance
    logger = ChronicleLogger(logname=appname)
    appname=logger.logName()    
    basedir=logger.baseDir()
    if logger.isDebug():
        logger.log_message(f"{appname} v{MAJOR_VERSION}.{MINOR_VERSION}.{PATCH_VERSION} ({__file__}) with the following:", component="main")
        logger.log_message(f">> {ChronicleLogger.class_version()}", component="main")

    if len(sys.argv) < 2:
        usage(appname)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd=="info":
        app = Example(basedir=basedir, logger=logger)
        app.info()
    else:
        usage(appname)
        sys.exit(1)

if __name__ == '__main__':
    main()
