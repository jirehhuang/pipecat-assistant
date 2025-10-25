"""Helper module to suppress import warnings in Alexa module."""

import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)
