"""
Local PII Guard Configuration - GITIGNORED.

Add your personal/sensitive info here to ensure they don't leak into the codebase.
This file is gitignored, so your personal info stays private.

See pii_guard_config.example.py for full documentation.
"""

# Personal identifiers
FORBIDDEN_NAMES = []

# Email addresses
FORBIDDEN_EMAILS = []

# API keys & secrets (even partial prefixes)
FORBIDDEN_API_KEYS = []

# Personal domains, internal URLs
FORBIDDEN_URLS = []

# Phone numbers
FORBIDDEN_PHONE_NUMBERS = []

# Physical addresses
FORBIDDEN_ADDRESSES = []

# Custom regex patterns
FORBIDDEN_PATTERNS = []

# Specific files to check (optional)
FILES_TO_CHECK = []
