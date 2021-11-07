"""
Logger tools for loging
"""

import time


class Logger:
    def __init__(self, log_name="log.log"):
        self._log_file = open(log_name, 'w')

    def log_content(self, content):
        self._log_file.write("Log: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n")
        self._log_file.write(content + "\n\n")
        self._log_file.flush()
