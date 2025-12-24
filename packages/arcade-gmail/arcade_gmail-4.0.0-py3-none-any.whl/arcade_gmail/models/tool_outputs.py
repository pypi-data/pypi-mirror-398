from typing import TypedDict


class EmailOutput(TypedDict, total=False):
    """Output model for an email message."""

    id: str
    """The unique ID of the email."""

    thread_id: str
    """The ID of the thread the email belongs to."""

    label_ids: list[str]
    """List of label IDs applied to the email."""

    snippet: str
    """A short snippet of the email content."""

    to: str
    """The recipient(s) of the email."""

    cc: str
    """The CC recipient(s) of the email."""

    from_: str  # 'from' is a reserved keyword
    """The sender of the email."""

    reply_to: str
    """The reply-to address."""

    subject: str
    """The subject of the email."""

    body: str
    """The plain text body of the email."""

    html_body: str
    """The HTML body of the email (if available/requested)."""

    date: str
    """The creation date of the email in UTC."""

    header_message_id: str
    """The Message-ID header value."""

    references: str
    """The References header value."""


class DraftOutput(TypedDict, total=False):
    """Output model for a draft email."""

    id: str
    """The unique ID of the draft."""

    thread_id: str
    """The ID of the thread the draft belongs to."""

    message: EmailOutput
    """The message content of the draft."""

    url: str
    """URL to view the draft."""


class ListEmailsOutput(TypedDict, total=False):
    """Output model for listing emails."""

    emails: list[EmailOutput]
    """List of emails."""


class ListDraftsOutput(TypedDict, total=False):
    """Output model for listing drafts."""

    emails: list[DraftOutput]
    """List of draft emails."""


class ThreadSummary(TypedDict, total=False):
    """Summary information for a thread from list operations.

    Note: This is a simplified view without the full messages array,
    avoiding recursive type definitions that cause MCP serialization issues.
    """

    id: str
    """The unique ID of the thread."""

    snippet: str
    """A short snippet of the thread content."""

    historyId: str
    """The history ID of the thread."""


class ThreadListOutput(TypedDict, total=False):
    """Output model for listing threads."""

    threads: list[ThreadSummary]
    """List of thread summaries with IDs and snippets."""

    num_threads: int
    """Number of threads returned."""

    next_page_token: str | None
    """Token for fetching the next page of results."""


class ThreadOutput(TypedDict, total=False):
    """Output model for an email thread."""

    id: str
    """The unique ID of the thread."""

    snippet: str
    """A short snippet of the thread content."""

    messages: list[EmailOutput]
    """List of messages in the thread."""


class LabelOutput(TypedDict, total=False):
    """Output model for a Gmail label."""

    id: str
    """The unique ID of the label."""

    name: str
    """The display name of the label."""

    type: str
    """The owner type for the label (system or user)."""


class ListLabelsOutput(TypedDict, total=False):
    """Output model for listing labels."""

    labels: list[LabelOutput]
    """List of labels."""


class ChangeLabelsOutput(TypedDict, total=False):
    """Output model for changing email labels."""

    confirmation: dict
    """Confirmation details including added and removed labels."""


class SendEmailOutput(TypedDict, total=False):
    """Output model for sending an email."""

    id: str
    """The ID of the sent message."""

    thread_id: str
    """The thread ID of the sent message."""

    label_ids: list[str]
    """List of label IDs applied to the sent message."""

    url: str
    """URL to view the sent email."""


class TrashEmailOutput(TypedDict, total=False):
    """Output model for trashing an email."""

    id: str
    """The ID of the trashed message."""

    thread_id: str
    """The thread ID of the trashed message."""

    label_ids: list[str]
    """List of label IDs applied to the trashed message."""

    url: str
    """URL to view the trashed email in Gmail."""


class CreateLabelOutput(TypedDict, total=False):
    """Output model for creating a label."""

    label: LabelOutput
    """The created label details."""


class GenericConfirmationOutput(TypedDict, total=False):
    """Output model for generic confirmation messages."""

    confirmation: str
    """A confirmation message."""
