import logging
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.mime.text import MIMEText
from typing import Any

from arcade_gmail.models.enums import (
    DateRange,
    GmailAction,
    GmailContentType,
    GmailReplyToWhom,
)
from arcade_gmail.models.tool_outputs import EmailOutput

logger = logging.getLogger(__name__)


MAX_RESULTS = 100
MIN_RESULTS = 1
DEFAULT_RESULTS = 25


def build_email_message(
    recipient: str,
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    replying_to: EmailOutput | None = None,
    action: GmailAction = GmailAction.SEND,
    content_type: GmailContentType = GmailContentType.PLAIN,
) -> dict[str, Any]:
    if replying_to:
        body = build_reply_body(body, replying_to)

    message: EmailMessage | MIMEText

    if action == GmailAction.SEND:
        message = EmailMessage()
        message.set_content(body, subtype=content_type.value)
    elif action == GmailAction.DRAFT:
        message = MIMEText(body, content_type.value)

    message["To"] = recipient
    message["Subject"] = subject

    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    if replying_to:
        message["In-Reply-To"] = replying_to.get("header_message_id", "")
        references = replying_to.get("references", "")
        message["References"] = f"{replying_to.get('header_message_id', '')}, {references}"

    encoded_message = urlsafe_b64encode(message.as_bytes()).decode()

    data = {"raw": encoded_message}

    if replying_to:
        data["threadId"] = replying_to.get("thread_id", "")

    return data


def build_reply_body(body: str, replying_to: EmailOutput) -> str:
    sender = replying_to.get("from_", replying_to.get("from", ""))
    attribution = f"On {replying_to.get('date', '')}, {sender} wrote:"
    lines = replying_to.get("body", "").split("\n")
    quoted_plain = "\n".join([f"> {line}" for line in lines])
    return f"{body}\n\n{attribution}\n\n{quoted_plain}"


def build_gmail_query_string(
    sender: str | None = None,
    recipient: str | None = None,
    subject: str | None = None,
    body: str | None = None,
    date_range: DateRange | None = None,
    label: str | None = None,
) -> str:
    """Helper function to build a query string
    for Gmail list_emails_by_header and search_threads tools.
    """
    query = []
    if sender:
        query.append(f"from:{sender}")
    if recipient:
        query.append(f"to:{recipient}")
    if subject:
        query.append(f"subject:{subject}")
    if body:
        query.append(body)
    if date_range:
        query.append(_date_range_to_query(date_range))
    if label:
        query.append(f"label:{label}")
    return " ".join(query)


def _date_range_to_query(date_range: DateRange) -> str:
    """
    Convert a DateRange enum to a Gmail query string.

    Args:
        date_range: The date range enum value to convert.

    Returns:
        Gmail query string like "after:2024/01/15".

    Note:
        Uses UTC timezone-aware datetime for consistency across timezones.
    """
    today = datetime.now(timezone.utc)
    result = "after:"
    comparison_date = today

    if date_range == DateRange.YESTERDAY:
        comparison_date = today - timedelta(days=1)
    elif date_range == DateRange.LAST_7_DAYS:
        comparison_date = today - timedelta(days=7)
    elif date_range == DateRange.LAST_30_DAYS:
        comparison_date = today - timedelta(days=30)
    elif date_range == DateRange.THIS_MONTH:
        comparison_date = today.replace(day=1)
    elif date_range == DateRange.LAST_MONTH:
        comparison_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    elif date_range == DateRange.THIS_YEAR:
        comparison_date = today.replace(month=1, day=1)

    return result + comparison_date.strftime("%Y/%m/%d")


def build_reply_recipients(
    replying_to: EmailOutput, current_user_email_address: str, reply_to_whom: GmailReplyToWhom
) -> str:
    if reply_to_whom == GmailReplyToWhom.ONLY_THE_SENDER:
        recipients = [replying_to.get("from_", "")]
    elif reply_to_whom == GmailReplyToWhom.EVERY_RECIPIENT:
        recipients = [replying_to.get("from_", ""), *replying_to.get("to", "").split(",")]
    else:
        raise ValueError(f"Unsupported reply_to_whom value: {reply_to_whom}")

    recipients = [
        email_address.strip()
        for email_address in recipients
        if email_address.strip().lower() != current_user_email_address.lower().strip()
    ]

    return ", ".join(recipients)


def get_draft_url(draft_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#drafts/{draft_id}"


def get_sent_email_url(sent_email_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#sent/{sent_email_id}"


def get_email_in_trash_url(email_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#trash/{email_id}"


def format_internal_date(internal_date: str | None) -> str:
    """
    Convert Gmail internalDate to a descriptive date string with weekday and month.

    Args:
        internal_date: Unix timestamp in milliseconds as a string, or None.

    Returns:
        Formatted date string with weekday, month, and UTC info.
    """
    if not internal_date:
        return ""
    try:
        timestamp_ms = int(internal_date)
        timestamp_s = timestamp_ms / 1000
        dt = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
        return dt.strftime("%A, %B %d, %Y at %H:%M:%S UTC")
    except (ValueError, TypeError, OSError):
        logger.warning(f"Failed to parse internalDate: {internal_date}")
        return ""


def remove_none_values(params: dict) -> dict:
    """
    Remove None values from a dictionary.
    :param params: The dictionary to clean
    :return: A new dictionary with None values removed
    """
    return {k: v for k, v in params.items() if v is not None}
