"""User-facing strings and fixed settings for the GUI.

Strings shown in the page itself live in ``static/``; these are the ones the
server sends back.
"""

APP_TITLE = "alphaPhos"

HOST = "127.0.0.1"
DEFAULT_PORT = 5006
LOCAL_HOSTS = ("localhost", "127.0.0.1")

REPORT_SUFFIXES = (".tsv", ".txt", ".parquet")
RUN_COLUMN = "R.FileName"

EMPTY_PATH = "Enter the path to a report first."
MISSING_FILE = "No file at {path}."
WRONG_SUFFIX = "{name} is not a report file; expected one of {suffixes}."
READ_FAILED = "Could not read {name}: {reason}"
FOREIGN_ORIGIN = "Requests from other websites are not accepted."
