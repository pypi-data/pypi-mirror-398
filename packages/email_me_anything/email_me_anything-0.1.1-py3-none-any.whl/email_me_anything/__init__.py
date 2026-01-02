"""email_me_anything — utilities to select CSV rows and send templated emails.

This package provides small helpers to read CSVs, build email content from templates,
and send emails via an external provider. The top-level package exports the
primary helpers for convenience:

- `config`: environment-based settings
- `csvutils`: CSV reading and selection helpers
- `emailutils`: functions to build HTML content and send emails
- `luckyemail`: orchestration function to send a random CSV row as an email
"""

# Expose main modules for easy import
from .config import Config
from .csvutils import read_csv, select_random_row
from .emailutils import build_html_content, send_email, build_context
from .luckyemail import send_lucky_email
