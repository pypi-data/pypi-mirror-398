
"""
Generalized orchestration logic for sending any row of data via email using a template.
"""
from pathlib import Path

from .config import Config

from .csvutils import select_random_row
from .emailutils import build_html_content, send_email

def send_lucky_email(
    csv_path: Path,
    template_path: Path,
    sender_address: str = Config.EMAIL_SENDER_ADDRESS,
    sender_name: str = Config.EMAIL_SENDER,
    recipients: list = [{"email": Config.EMAIL_RECIPIENT_0_ADDRESS, "name": Config.EMAIL_RECIPIENT_0_NAME}],
    variable_map: dict=None,
    subject: str = None,
    output_html_path: Path = Path("debug-email.html")
) -> bool:
    """Select a random CSV row, render it into an HTML template, and send or write the email.

    Args:
        csv_path (Path): Path to the CSV file to select the data row from.
        template_path (Path): Path to an HTML template file used to render the email body.
        sender_address (str): Sender email address (defaults to env value).
        sender_name (str): Sender display name (defaults to env value).
        recipients (list): List of recipient dicts with keys 'email' and 'name'.
        variable_map (dict, optional): Optional mapping of template variable names to CSV columns.
        subject (str, optional): Email subject. If omitted, a default subject is used.
        output_html_path (Path): When not in production mode, writes a debug HTML to this path.

    Returns:
        bool: True when the operation completes (email sent or debug file written),
              False when no row could be selected from the CSV.

    Raises:
        Exception: May raise exceptions from `select_random_row`, `build_html_content`, or `send_email`.
    """
    selected_data = select_random_row(csv_path)
    if not selected_data:
        print("No row selected.")
        return False
        
    html_content = build_html_content(template_path, selected_data, variable_map)

    if not subject:
        subject = "New Data Row!"
        
    sender = {"email": sender_address, "name": sender_name}
    recipients = recipients
    
    if Config.PROD_MODE:
        response = send_email(
            sender,
            recipients,
            subject,
            html_content
        )
        print(f"Email sent: {response}")
    else:
        print("Production mode is OFF. Writing email to debug-email.html")
        with open(output_html_path, "w", encoding="utf-8") as debug_file:
            debug_file.write(html_content)
    return True
