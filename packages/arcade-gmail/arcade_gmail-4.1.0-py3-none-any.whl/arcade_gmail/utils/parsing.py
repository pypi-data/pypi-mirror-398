import logging
import re
from base64 import urlsafe_b64decode

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_email_body(body: str | None) -> str:
    """
    Remove HTML tags and clean up email body text while preserving most content.

    Args:
        body (str): The raw email body text.

    Returns:
        str: Cleaned email body text.
    """
    if not body:
        return ""

    try:
        # Remove HTML tags using BeautifulSoup
        soup = BeautifulSoup(body, "html.parser")
        text = soup.get_text(separator=" ")

        # Clean up the text
        cleaned_text = clean_text(text)

        return cleaned_text.strip()
    except Exception:
        logger.exception("Error cleaning email body")
        return body


def get_email_plain_text_body(payload: dict) -> str | None:
    """
    Extract email body from payload, handling 'multipart/alternative' parts.

    Args:
        payload (Dict[str, Any]): Email payload data.

    Returns:
        str | None: Decoded email body or None if not found.
    """
    # Direct body extraction
    if "body" in payload and payload["body"].get("data"):
        return clean_email_body(urlsafe_b64decode(payload["body"]["data"]).decode())

    # Handle multipart and alternative parts
    return clean_email_body(extract_plain_body(payload.get("parts", [])))


def get_email_html_body(payload: dict) -> str | None:
    """
    Extract email html body from payload, handling 'multipart/alternative' parts.

    Args:
        payload (Dict[str, Any]): Email payload data.

    Returns:
        str | None: Decoded email body or None if not found.
    """
    # Direct body extraction
    if "body" in payload and payload["body"].get("data"):
        return urlsafe_b64decode(payload["body"]["data"]).decode()

    # Handle multipart and alternative parts
    return extract_html_body(payload.get("parts", []))


def extract_plain_body(parts: list) -> str | None:
    """
    Recursively extract the email body from parts, handling both plain text and HTML.

    Args:
        parts (List[Dict[str, Any]]): List of email parts.

    Returns:
        str | None: Decoded and cleaned email body or None if not found.
    """
    for part in parts:
        mime_type = part.get("mimeType")

        if mime_type == "text/plain" and "data" in part.get("body", {}):
            return urlsafe_b64decode(part["body"]["data"]).decode()

        elif mime_type.startswith("multipart/"):
            subparts = part.get("parts", [])
            body = extract_plain_body(subparts)
            if body:
                return body

    return extract_html_body(parts)


def extract_html_body(parts: list) -> str | None:
    """
    Recursively extract the email body from parts, handling only HTML.

    Args:
        parts (List[Dict[str, Any]]): List of email parts.

    Returns:
        str | None: Decoded and cleaned email body or None if not found.
    """
    for part in parts:
        mime_type = part.get("mimeType")

        if mime_type == "text/html" and "data" in part.get("body", {}):
            html_content = urlsafe_b64decode(part["body"]["data"]).decode()
            return html_content

        elif mime_type.startswith("multipart/"):
            subparts = part.get("parts", [])
            body = extract_html_body(subparts)
            if body:
                return body

    return None


def clean_text(text: str) -> str:
    """
    Clean up the text while preserving most content.

    Args:
        text (str): The input text.

    Returns:
        str: Cleaned text.
    """
    # Replace multiple newlines with a single newline
    text = re.sub(r"\n+", "\n", text)

    # Replace multiple spaces with a single space
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace from each line
    text = "\n".join(line.strip() for line in text.split("\n"))

    return text
