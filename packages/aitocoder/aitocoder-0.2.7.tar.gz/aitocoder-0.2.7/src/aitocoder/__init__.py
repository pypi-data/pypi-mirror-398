"""
AitoCoder - An AI-powered coding agent from the terminal

autocoder/ contains all the functionality, while
login_modules/ handles login & authentication
"""

# Suppress all warnings early (before any other imports)
# unless the user has specified --show-warning flag
import os
import warnings

if os.environ.get("AITOCODER_SUPPRESS_WARNINGS") == "1":
    warnings.filterwarnings("ignore")
