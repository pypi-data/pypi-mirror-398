"""
Email utilities for building and sending emails using MailerSend.
Functions:
- build_context: Creates a context dictionary for template rendering.
- build_html_content: Renders an HTML template with provided data.
- send_email: Sends an email via MailerSend.
"""
from pathlib import Path
from typing import Any, Dict, List

from mailersend import MailerSendClient, EmailBuilder

def build_context(data: Dict[str, Any], variable_map: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Build a context dictionary by mapping data keys to template variables.
    Args:
        data: A dictionary containing the source data to be mapped.
        variable_map: Optional dictionary mapping template variable names to data keys.
                     If None, returns the data dictionary as-is.
    Returns:
        A dictionary containing the context for template rendering. If variable_map is None,
        returns the original data dictionary. Otherwise, returns a new dictionary with template
        variable names as keys and corresponding values from data (or empty strings if keys
        are not found).
    Example:
        >>> data = {"user_name": "John", "email": "john@example.com"}
        >>> var_map = {"name": "user_name", "contact": "email"}
        >>> build_context(data, var_map)
        {"name": "John", "contact": "john@example.com"}
    """
    
    context = {}
    if variable_map is None:
        context = data
    else:
        for template_var, data_key in variable_map.items():
            context[template_var] = data.get(data_key, "")
    return context
        
def build_html_content(template_path: Path, data: Dict[str, Any], variable_map: Dict[str, Any] = None) -> str:
    """
    Build HTML content by rendering a template with provided data.

    Args:
        template_path (Path): Path to the HTML template file.
        data (Dict[str, Any]): Dictionary containing data to be used in the template.
        variable_map (Dict[str, Any], optional): Optional mapping to transform or alias variables
            from the data dictionary. Defaults to None.

    Returns:
        str: Rendered HTML content with variables substituted from the context.

    Raises:
        FileNotFoundError: If the template file does not exist at template_path.
        KeyError: If a required variable in the template is missing from the context.
        UnicodeDecodeError: If the template file cannot be decoded as UTF-8.
    """
    
    context = build_context(data, variable_map)
    with open(template_path, "r", encoding="utf-8") as file:
        html_template = file.read()
    return html_template.format_map(context)

def send_email(sender: Dict[str, str], recipients: List[Dict[str, str]], subject: str, html_content: str) -> Dict[str, Any]:
    """
    Send an email using the MailerSend service.

    Args:
        sender (Dict[str, str]): A dictionary containing the sender's email address and name.
            Expected keys: "email" (str), "name" (str).
        recipients (List[Dict[str, str]]): A list of dictionaries containing recipient information.
            Each dictionary should contain recipient email and name details.
        subject (str): The subject line of the email.
        html_content (str): The HTML-formatted body content of the email.

    Returns:
        Dict[str, Any]: A dictionary representation of the MailerSend API response,
            containing status, message ID, and other response metadata.

    Raises:
        Exception: May raise exceptions from the MailerSend client if the email
            fails to send (e.g., invalid email addresses, authentication errors).

    Example:
        >>> sender = {"email": "from@example.com", "name": "John Doe"}
        >>> recipients = [{"email": "to@example.com", "name": "Jane Smith"}]
        >>> response = send_email(sender, recipients, "Hello", "<p>Hello World</p>")
    """
    
    ms = MailerSendClient()
    email = (
        EmailBuilder()
        .from_email(sender["email"], sender["name"])
        .to_many(recipients)
        .subject(subject)
        .html(html_content)
        .build()
    )
    response = ms.emails.send(email)
    return response.to_dict()
