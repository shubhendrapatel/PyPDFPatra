"""
pypdfpatra.logger
~~~~~~~~~~~~~~~~~
Logging configuration for the PyPDFPatra library.
"""

import logging

# Define a standard logger for the library
logger = logging.getLogger("pypdfpatra")

# Set default level (can be overridden by the user)
logger.setLevel(logging.INFO)

# Create a console handler with a formatter
handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Add the handler only if the logger doesn't already have handlers to avoid duplicates
if not logger.handlers:
    logger.addHandler(handler)
