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
LOADED = "Loaded {name}."
NO_REPORT = "Load a report first."
BUSY = "A report is already loading; wait for it to finish."
UNKNOWN_KIND = "Unknown report kind {kind!r}."
UNEXPECTED = "Unexpected error: {reason}"
DIANN_LONG_UNSUPPORTED = (
    "DIA-NN precursor-level proteome reports are not supported yet; "
    "load report.pg_matrix.tsv instead."
)

# What a report's counts count.
UNIT_ROWS = "rows"
UNIT_PROTEIN_GROUPS = "protein groups"

# Progress stages, shown under the progress bar.
STAGE_READING = "Reading file"
STAGE_PARSING = "Parsing file"
STAGE_CONTAMINANTS = "Measuring contaminants"
STAGE_FILTERING = "Removing contaminants"
