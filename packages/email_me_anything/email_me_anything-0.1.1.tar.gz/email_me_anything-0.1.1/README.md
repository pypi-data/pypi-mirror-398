# Email Me Anything

A simple Python package for sending emails programmatically with various content, such as quotes, custom messages, or data from CSV files. It provides utilities for handling CSV files, email configuration, and sending templated emails via MailerSend.

## Installation

Install the package from PyPI:

```bash
pip install email_me_anything
```

## Configuration

The package uses environment variables for configuration. Most are optional, but if you intend to send emails, certain variables become mandatory.

Create a `.env` file in your project directory with the following variables as needed:

```env
# Optional: Sender details
EMAIL_SENDER=Your Name
EMAIL_SENDER_ADDRESS=your-email@example.com

# Optional: Recipient details (can be set programmatically if needed)
EMAIL_RECIPIENT_0_NAME=Recipient Name
EMAIL_RECIPIENT_0_ADDRESS=recipient@example.com

# Mandatory if email sending is required; defaults to false (no emails sent)
PROD_MODE=true
MAILERSEND_API_KEY=your-mailersend-api-key
```

- **PROD_MODE**: Set to `true` to enable email sending. If `false` (default), no emails are sent just created and saved in `debug-email.html`, and no other keys are required.
- If `PROD_MODE` is `true`, you must configure your MailerSend API key as per the `mailersend` library documentation (e.g., via `MAILERSEND_API_KEY` environment variable).

## Usage

Import the helpers below and work with pathlib Paths whenever you load templates or CSV files.

### Sending a Lucky Email

Send a random row from a CSV file by rendering it into an HTML template. You can override the default sender and recipient values or pass a `variable_map` that renames CSV columns for the template.

```python
from pathlib import Path
from email_me_anything import send_lucky_email

csv_path = Path("quotes.csv")
template_path = Path("templates/quote.html")

send_lucky_email(
    csv_path,
    template_path,
    subject="Daily Inspiration",
    recipients=[{"email": "friend@example.com", "name": "Friend"}],
    variable_map={"quote": "text", "author": "author"},
)
```

### Sending a Custom Email

Use `build_html_content` (and `build_context` if you need to massage the data) to render a template and send it with `send_email`.

```python
from pathlib import Path
from email_me_anything import build_context, build_html_content, send_email

template = Path("templates/notification.html")
data = {"status": "Completed", "details": "System update succeeded."}
context = build_context(data)
html_content = build_html_content(template, context)

sender = {"email": "alerts@example.com", "name": "Alert Bot"}
recipients = [{"email": "ops@example.com", "name": "Ops Team"}]
send_email(sender, recipients, "System Alert", html_content)
```

`variable_map` lets you rename keys from `data` before rendering the template.

### Working with CSV Files

`read_csv` returns the raw rows from a file, while `select_random_row` returns a dict keyed by the header row (or `col0`, `col1`, etc. when headers are missing).

```python
from pathlib import Path
from email_me_anything import read_csv, select_random_row

csv_path = Path("quotes.csv")
rows = read_csv(csv_path)

if rows:
    sample = select_random_row(csv_path)
    print(sample)
```

`select_random_row` yields `False` when the file cannot be read and `None` when there are no rows beyond the header.

## Examples

### Example 1: Daily Quote Email

```python
import schedule
from pathlib import Path
from email_me_anything import send_lucky_email

csv_path = Path("quotes.csv")
template_path = Path("templates/quote.html")

def send_daily_quote():
    send_lucky_email(csv_path, template_path, subject="Quote of the Day")

# Schedule to run daily at 8 AM
schedule.every().day.at("08:00").do(send_daily_quote)
```

### Example 2: Custom Notification Email

```python
from pathlib import Path
from email_me_anything import build_context, build_html_content, send_email

template_path = Path("templates/notification.html")
data = {"title": "Alert", "message": "System update completed successfully."}
context = build_context(data, variable_map={"title": "title", "message": "message"})
html_content = build_html_content(template_path, context)

sender = {"email": "alerts@example.com", "name": "Alert System"}
recipients = [{"email": "team@example.com", "name": "Team"}]
send_email(sender, recipients, "System Alert", html_content)
```

### Example 3: Bulk Email from CSV

```python
from pathlib import Path
from email_me_anything import read_csv, build_html_content, send_email

template_path = Path("templates/bulk-welcome.html")
csv_path = Path("recipients.csv")
rows = read_csv(csv_path)

if not rows or len(rows) < 2:
    raise SystemExit("No recipient data")

headers = rows[0]
sender = {"email": "hello@example.com", "name": "Hello Team"}

for row in rows[1:]:
    data = dict(zip(headers, row))
    recipient = {"email": data["email"], "name": data["name"]}
    html = build_html_content(template_path, data)
    send_email(sender, [recipient], f"Welcome {data['name']}", html)
```

## Testing

The package includes comprehensive test coverage using pytest. Tests verify:

- **Configuration Management**: Parsing of environment variables with proper defaults
- **CSV Operations**: Reading CSV files, handling missing/malformed data, random row selection with deterministic and probabilistic tests
- **Email Building**: HTML template rendering, variable mapping, Unicode support, error handling
- **Email Sending**: Integration with MailerSend API, recipient handling, production vs. debug modes
- **Complete Workflows**: End-to-end email sending through `send_lucky_email` with variable maps and default values

### Running Tests

Install development dependencies and run pytest:

```bash
pip install pytest
pytest tests/ -v
```

Current test suite includes 42 tests covering:
- 8 configuration tests (env variable parsing, defaults)
- 13 CSV utility tests (reading, parsing, randomization)
- 11 email utility tests (context building, HTML rendering, sending)
- 10 integration tests (complete workflows, mode switching)

## License

Apache License 2.0
