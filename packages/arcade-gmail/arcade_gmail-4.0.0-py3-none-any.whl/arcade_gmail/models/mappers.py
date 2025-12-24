from typing import cast

from arcade_gmail.models.api_responses import Draft, Label, Message, Thread
from arcade_gmail.models.tool_outputs import (
    DraftOutput,
    EmailOutput,
    LabelOutput,
    ThreadOutput,
)
from arcade_gmail.utils.helpers import format_internal_date
from arcade_gmail.utils.parsing import (
    clean_email_body,
    get_email_html_body,
    get_email_plain_text_body,
)


def map_message_to_email_output(message_data: Message) -> EmailOutput:
    """
    Map a Gmail API Message response to a structured EmailOutput.

    Extracts and transforms message data from the Gmail API format into a clean,
    LLM-friendly output format. Handles both plain text and HTML bodies, with
    automatic fallback from plain text to cleaned HTML when necessary.

    Args:
        message_data: Raw message data from Gmail API containing payload, headers,
                     and metadata.

    Returns:
        EmailOutput with all message fields populated, including:
        - Message identifiers (id, thread_id)
        - Headers (to, from, subject, cc, etc.)
        - Body content (both plain text and HTML)
        - Formatted date in UTC
        - Label IDs

    Note:
        If plain text body is not available, falls back to cleaned HTML body.
        Date is converted from Gmail's internalDate (milliseconds) to human-readable UTC format.
    """
    payload = message_data.get("payload", {})
    headers = {d["name"].lower(): d["value"] for d in payload.get("headers", [])}

    # Extract different parts of the email
    plain_text_body = get_email_plain_text_body(payload)  # type: ignore[arg-type]
    html_body = get_email_html_body(payload)  # type: ignore[arg-type]

    internal_date = message_data.get("internalDate")

    return cast(
        EmailOutput,
        {
            "id": message_data.get("id", ""),
            "thread_id": message_data.get("threadId", ""),
            "label_ids": message_data.get("labelIds", []),
            "snippet": message_data.get("snippet", ""),
            "to": headers.get("to", ""),
            "cc": headers.get("cc", ""),
            "from_": headers.get("from", ""),
            "reply_to": headers.get("reply-to", ""),
            "subject": headers.get("subject", ""),
            "date": format_internal_date(internal_date),
            "body": plain_text_body or clean_email_body(html_body),
            "html_body": html_body or "",
            "header_message_id": headers.get("message-id", ""),
            "references": headers.get("references", ""),
        },
    )


def map_draft_to_draft_output(draft_data: Draft) -> DraftOutput:
    """
    Map a Gmail API Draft response to a structured DraftOutput.

    Extracts draft metadata and the underlying message data, transforming
    them into a clean output format suitable for LLM consumption.

    Args:
        draft_data: Raw draft data from Gmail API containing draft ID and
                   embedded message data.

    Returns:
        DraftOutput containing draft ID, thread ID, and fully mapped message
        content (via map_message_to_email_output).

    Note:
        The message field contains all email details (subject, body, recipients, etc.)
        mapped through map_message_to_email_output.
    """
    message = draft_data.get("message", {})
    email_output = map_message_to_email_output(message)

    return cast(
        DraftOutput,
        {
            "id": draft_data.get("id", ""),
            "thread_id": message.get("threadId", ""),
            "message": email_output,
        },
    )


def map_thread_to_thread_output(thread_data: Thread) -> ThreadOutput:
    """
    Map a Gmail API Thread response to a structured ThreadOutput.

    Transforms thread data including all messages in the conversation into
    a structured format with fully mapped message content.

    Args:
        thread_data: Raw thread data from Gmail API containing thread ID,
                    snippet, and list of messages.

    Returns:
        ThreadOutput containing thread metadata and list of fully mapped
        EmailOutput objects for all messages in the thread.

    Note:
        All messages are mapped through map_message_to_email_output, providing
        complete details for each message in the conversation.
    """
    messages = [map_message_to_email_output(msg) for msg in thread_data.get("messages", [])]

    return cast(
        ThreadOutput,
        {
            "id": thread_data.get("id", ""),
            "snippet": thread_data.get("snippet", ""),
            "messages": messages,
        },
    )


def map_label_to_label_output(label_data: Label) -> LabelOutput:
    """
    Map a Gmail API Label response to a structured LabelOutput.

    Extracts essential label information from Gmail API format into a
    simplified structure for LLM consumption.

    Args:
        label_data: Raw label data from Gmail API containing label metadata.

    Returns:
        LabelOutput with label ID, display name, and type (system/user).

    Note:
        Type field indicates whether the label is a Gmail system label
        (e.g., INBOX, SENT) or a user-created label.
    """
    return cast(
        LabelOutput,
        {
            "id": label_data.get("id", ""),
            "name": label_data.get("name", ""),
            "type": label_data.get("type", ""),
        },
    )
