import base64
from email.mime.text import MIMEText
from typing import Annotated

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google
from arcade_mcp_server.exceptions import RetryableToolError

from arcade_gmail.client import GmailClient
from arcade_gmail.constants import GMAIL_DEFAULT_REPLY_TO
from arcade_gmail.models.enums import (
    DateRange,
    GmailAction,
    GmailContentType,
    GmailReplyToWhom,
)
from arcade_gmail.models.mappers import (
    map_draft_to_draft_output,
    map_label_to_label_output,
    map_message_to_email_output,
    map_thread_to_thread_output,
)
from arcade_gmail.models.tool_outputs import (
    ChangeLabelsOutput,
    CreateLabelOutput,
    DraftOutput,
    ListDraftsOutput,
    ListEmailsOutput,
    ListLabelsOutput,
    SendEmailOutput,
    ThreadListOutput,
    ThreadOutput,
    TrashEmailOutput,
)
from arcade_gmail.utils.helpers import (
    DEFAULT_RESULTS,
    MAX_RESULTS,
    MIN_RESULTS,
    build_email_message,
    build_gmail_query_string,
    build_reply_recipients,
    get_draft_url,
    get_email_in_trash_url,
    get_sent_email_url,
)


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
)
async def send_email(
    context: Context,
    subject: Annotated[str, "The subject of the email"],
    body: Annotated[str, "The body of the email"],
    recipient: Annotated[str, "The recipient of the email"],
    cc: Annotated[list[str] | None, "CC recipients of the email"] = None,
    bcc: Annotated[list[str] | None, "BCC recipients of the email"] = None,
    content_type: Annotated[
        GmailContentType,
        "The content type of the email body. Defaults to 'plain'",
    ] = GmailContentType.PLAIN,
) -> Annotated[
    SendEmailOutput,
    "A dictionary containing the sent email details with date in descriptive UTC format",
]:
    """
    Send an email using the Gmail API.
    """
    client = GmailClient(context)
    email = build_email_message(recipient, subject, body, cc, bcc, content_type=content_type)

    sent_message = client.send_message(email)

    output = map_message_to_email_output(sent_message)
    return {
        "id": output.get("id", ""),
        "thread_id": output.get("thread_id", ""),
        "label_ids": output.get("label_ids", []),
        "url": get_sent_email_url(output.get("id", "")),
    }


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
)
async def send_draft_email(
    context: Context, email_id: Annotated[str, "The ID of the draft to send"]
) -> Annotated[
    SendEmailOutput,
    "A dictionary containing the sent email details with date in descriptive UTC format",
]:
    """
    Send a draft email using the Gmail API.
    """
    client = GmailClient(context)
    sent_message = client.send_draft(email_id)

    output = map_message_to_email_output(sent_message)
    return {
        "id": output.get("id", ""),
        "thread_id": output.get("thread_id", ""),
        "label_ids": output.get("label_ids", []),
        "url": get_sent_email_url(output.get("id", "")),
    }


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
)
async def reply_to_email(
    context: Context,
    body: Annotated[str, "The body of the email"],
    reply_to_message_id: Annotated[str, "The ID of the message to reply to"],
    reply_to_whom: Annotated[
        GmailReplyToWhom,
        "Whether to reply to every recipient (including cc) or only to the original sender. "
        f"Defaults to '{GMAIL_DEFAULT_REPLY_TO}'.",
    ] = GMAIL_DEFAULT_REPLY_TO,
    bcc: Annotated[list[str] | None, "BCC recipients of the email"] = None,
    content_type: Annotated[
        GmailContentType,
        "The content type of the email body. Defaults to 'plain'",
    ] = GmailContentType.PLAIN,
) -> Annotated[
    SendEmailOutput,
    "A dictionary containing the sent email details with date in descriptive UTC format",
]:
    """
    Send a reply to an email message.
    """
    if isinstance(reply_to_whom, str):
        reply_to_whom = GmailReplyToWhom(reply_to_whom)

    client = GmailClient(context)
    current_user = client.get_profile()
    replying_to_email_data = client.get_message(reply_to_message_id)
    replying_to_email = map_message_to_email_output(replying_to_email_data)

    recipients = build_reply_recipients(
        replying_to_email,
        current_user["emailAddress"],
        reply_to_whom,
    )

    cc_recipients = None
    if reply_to_whom == GmailReplyToWhom.EVERY_RECIPIENT:
        cc_str = replying_to_email.get("cc", "")
        cc_recipients = [c.strip() for c in cc_str.split(",") if c.strip()] if cc_str else None

    email = build_email_message(
        recipient=recipients,
        subject=f"Re: {replying_to_email.get('subject')}",
        body=body,
        cc=cc_recipients,
        bcc=bcc,
        replying_to=replying_to_email,
        content_type=content_type,
    )

    sent_message = client.send_message(email)
    output = map_message_to_email_output(sent_message)
    return {
        "id": output.get("id", ""),
        "thread_id": output.get("thread_id", ""),
        "label_ids": output.get("label_ids", []),
        "url": get_sent_email_url(output.get("id", "")),
    }


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def write_draft_email(
    context: Context,
    subject: Annotated[str, "The subject of the draft email"],
    body: Annotated[str, "The body of the draft email"],
    recipient: Annotated[str, "The recipient of the draft email"],
    cc: Annotated[list[str] | None, "CC recipients of the draft email"] = None,
    bcc: Annotated[list[str] | None, "BCC recipients of the draft email"] = None,
    content_type: Annotated[
        GmailContentType,
        "The content type of the email body. Defaults to 'plain'",
    ] = GmailContentType.PLAIN,
) -> Annotated[
    DraftOutput,
    "A dictionary containing the created draft email details with date in descriptive UTC format",
]:
    """
    Compose a new email draft using the Gmail API.
    """
    client = GmailClient(context)

    draft_body = {
        "message": build_email_message(
            recipient,
            subject,
            body,
            cc,
            bcc,
            action=GmailAction.DRAFT,
            content_type=content_type,
        )
    }

    draft_message = client.create_draft(draft_body)
    output = map_draft_to_draft_output(draft_message)
    output["url"] = get_draft_url(output["id"])
    return output


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def write_draft_reply_email(
    context: Context,
    body: Annotated[str, "The body of the draft reply email"],
    reply_to_message_id: Annotated[str, "The Gmail message ID of the message to draft a reply to"],
    reply_to_whom: Annotated[
        GmailReplyToWhom,
        "Whether to reply to every recipient (including cc) or only to the original sender. "
        f"Defaults to '{GMAIL_DEFAULT_REPLY_TO}'.",
    ] = GMAIL_DEFAULT_REPLY_TO,
    bcc: Annotated[list[str] | None, "BCC recipients of the draft reply email"] = None,
    content_type: Annotated[
        GmailContentType,
        "The content type of the email body. Defaults to 'plain'",
    ] = GmailContentType.PLAIN,
) -> Annotated[
    DraftOutput,
    "A dictionary containing draft reply email details with dates in descriptive UTC format",
]:
    """
    Compose a draft reply to an email message.
    """
    if isinstance(reply_to_whom, str):
        reply_to_whom = GmailReplyToWhom(reply_to_whom)

    client = GmailClient(context)
    current_user = client.get_profile()
    replying_to_email_data = client.get_message(reply_to_message_id)
    replying_to_email = map_message_to_email_output(replying_to_email_data)

    recipients = build_reply_recipients(
        replying_to_email,
        current_user["emailAddress"],
        reply_to_whom,
    )

    cc_recipients = None
    if reply_to_whom == GmailReplyToWhom.EVERY_RECIPIENT:
        cc_str = replying_to_email.get("cc", "")
        cc_recipients = [c.strip() for c in cc_str.split(",") if c.strip()] if cc_str else None

    draft_message_body = {
        "message": build_email_message(
            recipient=recipients,
            subject=f"Re: {replying_to_email.get('subject')}",
            body=body,
            cc=cc_recipients,
            bcc=bcc,
            replying_to=replying_to_email,
            action=GmailAction.DRAFT,
            content_type=content_type,
        ),
    }

    draft = client.create_draft(draft_message_body)
    output = map_draft_to_draft_output(draft)
    output["url"] = get_draft_url(output["id"])
    return output


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def update_draft_email(
    context: Context,
    draft_email_id: Annotated[str, "The ID of the draft email to update."],
    subject: Annotated[str, "The subject of the draft email"],
    body: Annotated[str, "The body of the draft email"],
    recipient: Annotated[str, "The recipient of the draft email"],
    cc: Annotated[list[str] | None, "CC recipients of the draft email"] = None,
    bcc: Annotated[list[str] | None, "BCC recipients of the draft email"] = None,
) -> Annotated[
    DraftOutput,
    "A dictionary containing the updated draft email details with date in descriptive UTC format",
]:
    """
    Update an existing email draft using the Gmail API.
    """
    client = GmailClient(context)

    message = MIMEText(body)
    message["to"] = recipient
    message["subject"] = subject
    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft_body = {"id": draft_email_id, "message": {"raw": raw_message}}

    updated_draft_message = client.update_draft(draft_email_id, draft_body)
    output = map_draft_to_draft_output(updated_draft_message)
    output["url"] = get_draft_url(output["id"])
    return output


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def delete_draft_email(
    context: Context,
    draft_email_id: Annotated[str, "The ID of the draft email to delete"],
) -> Annotated[str, "A confirmation message indicating successful deletion"]:
    """
    Delete a draft email using the Gmail API.
    """
    client = GmailClient(context)
    client.delete_draft(draft_email_id)
    return f"Draft email with ID {draft_email_id} deleted successfully."


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    )
)
async def trash_email(
    context: Context, email_id: Annotated[str, "The ID of the email to trash"]
) -> Annotated[
    TrashEmailOutput,
    "Details of the trashed email with URL to view in Gmail trash folder",
]:
    """
    Move an email to the trash folder using the Gmail API.
    """
    client = GmailClient(context)
    trashed_email = client.trash_message(email_id)
    output = map_message_to_email_output(trashed_email)
    return {
        "id": output.get("id", ""),
        "thread_id": output.get("thread_id", ""),
        "label_ids": output.get("label_ids", []),
        "url": get_email_in_trash_url(output.get("id", "")),
    }


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_draft_emails(
    context: Context,
    n_drafts: Annotated[
        int,
        f"Number of draft emails to read (Min {MIN_RESULTS}, Max {MAX_RESULTS})",
    ] = DEFAULT_RESULTS,
) -> Annotated[
    ListDraftsOutput,
    "A dictionary containing a list of draft email details with dates in descriptive UTC format",
]:
    """
    Lists draft emails in the user's draft mailbox using the Gmail API.
    """
    client = GmailClient(context)
    n_drafts = min(max(n_drafts, MIN_RESULTS), MAX_RESULTS)

    listed_drafts = client.list_drafts(limit=n_drafts)
    if not listed_drafts:
        return {"emails": []}

    draft_ids = [d["id"] for d in listed_drafts]
    drafts_data = client.get_drafts_batch(draft_ids)

    drafts = []
    for d in drafts_data:
        output = map_draft_to_draft_output(d)
        output["url"] = get_draft_url(output["id"])
        drafts.append(output)

    return {"emails": drafts}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_emails_by_header(
    context: Context,
    sender: Annotated[str | None, "The name or email address of the sender of the email"] = None,
    recipient: Annotated[str | None, "The name or email address of the recipient"] = None,
    subject: Annotated[str | None, "Words to find in the subject of the email"] = None,
    body: Annotated[str | None, "Words to find in the body of the email"] = None,
    date_range: Annotated[DateRange | None, "The date range of the email"] = None,
    label: Annotated[str | None, "The label name to filter by"] = None,
    max_results: Annotated[
        int,
        f"The maximum number of emails to return (Min {MIN_RESULTS}, Max {MAX_RESULTS}",
    ] = DEFAULT_RESULTS,
) -> Annotated[
    ListEmailsOutput,
    "A dictionary containing a list of email details with dates in descriptive UTC format",
]:
    """
    Search for emails by header using the Gmail API.
    """
    client = GmailClient(context)
    if not any([sender, recipient, subject, body, label, date_range]):
        raise RetryableToolError(
            message="At least one search parameter must be provided.",
            developer_message="Missing search parameters.",
            additional_prompt_content=(
                "Please provide at least one search parameter: "
                "sender, recipient, subject, body, label, or date_range."
            ),
        )

    if label:
        label_ids, all_labels = client.get_label_ids([label])
        if not label_ids:
            raise RetryableToolError(
                message=f"Invalid label: {label}",
                developer_message=f"Invalid label: {label}",
                additional_prompt_content=f"List of valid labels: {all_labels}",
            )

    query = build_gmail_query_string(sender, recipient, subject, body, date_range, label)
    max_results = min(max(max_results, MIN_RESULTS), MAX_RESULTS)

    messages = client.list_messages(query, limit=max_results)
    if not messages:
        return {"emails": []}

    message_ids = [m["id"] for m in messages]
    messages_data = client.get_messages_batch(message_ids)

    emails = [map_message_to_email_output(m) for m in messages_data]
    return {"emails": emails}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_emails(
    context: Context,
    n_emails: Annotated[
        int,
        f"Number of emails to read (Min {MIN_RESULTS}, Max {MAX_RESULTS})",
    ] = DEFAULT_RESULTS,
) -> Annotated[
    ListEmailsOutput,
    "A dictionary containing a list of email details with dates in descriptive UTC format",
]:
    """
    Read emails from a Gmail account and extract plain text content.
    """
    client = GmailClient(context)
    n_emails = min(max(n_emails, MIN_RESULTS), MAX_RESULTS)

    # Empty query lists all messages
    messages = client.list_messages(query="", limit=n_emails)
    if not messages:
        return {"emails": []}

    message_ids = [m["id"] for m in messages]
    messages_data = client.get_messages_batch(message_ids)

    emails = [map_message_to_email_output(m) for m in messages_data]
    return {"emails": emails}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def search_threads(
    context: Context,
    page_token: Annotated[
        str | None, "Page token to retrieve a specific page of results in the list"
    ] = None,
    max_results: Annotated[
        int,
        "The maximum number of threads to return (Min {MIN_RESULTS}, Max {MAX_RESULTS})",
    ] = DEFAULT_RESULTS,
    include_spam_trash: Annotated[bool, "Whether to include spam and trash in the results"] = False,
    label_ids: Annotated[list[str] | None, "The IDs of labels to filter by"] = None,
    sender: Annotated[str | None, "The name or email address of the sender of the email"] = None,
    recipient: Annotated[str | None, "The name or email address of the recipient"] = None,
    subject: Annotated[str | None, "Words to find in the subject of the email"] = None,
    body: Annotated[str | None, "Words to find in the body of the email"] = None,
    date_range: Annotated[DateRange | None, "The date range of the email"] = None,
) -> Annotated[ThreadListOutput, "A dictionary containing a list of thread details"]:
    """Search for threads in the user's mailbox"""
    client = GmailClient(context)
    query = (
        build_gmail_query_string(sender, recipient, subject, body, date_range)
        if any([sender, recipient, subject, body, date_range])
        else None
    )
    max_results = min(max(max_results, MIN_RESULTS), MAX_RESULTS)

    response = client.list_threads(
        query=query,
        limit=max_results,
        page_token=page_token,
        include_spam_trash=include_spam_trash,
        label_ids=label_ids,
    )

    threads = response.get("threads", [])
    next_page_token = response.get("nextPageToken")

    return {
        "threads": threads,  # type: ignore[typeddict-item]
        "num_threads": len(threads),
        "next_page_token": next_page_token,
    }


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_threads(
    context: Context,
    page_token: Annotated[
        str | None, "Page token to retrieve a specific page of results in the list"
    ] = None,
    max_results: Annotated[
        int,
        "The maximum number of threads to return (Min {MIN_RESULTS}, Max {MAX_RESULTS})",
    ] = DEFAULT_RESULTS,
    include_spam_trash: Annotated[bool, "Whether to include spam and trash in the results"] = False,
) -> Annotated[ThreadListOutput, "A dictionary containing a list of thread details"]:
    """List threads in the user's mailbox."""
    result: ThreadListOutput = await search_threads(
        context, page_token, max_results, include_spam_trash
    )
    return result


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def get_thread(
    context: Context,
    thread_id: Annotated[str, "The ID of the thread to retrieve"],
) -> Annotated[
    ThreadOutput,
    "A dictionary containing the thread details with dates in descriptive UTC format",
]:
    """
    Get the specified thread by ID.
    """
    client = GmailClient(context)
    thread_data = client.get_thread(thread_id)
    return map_thread_to_thread_output(thread_data)


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    )
)
async def change_email_labels(
    context: Context,
    email_id: Annotated[str, "The ID of the email to modify labels for"],
    labels_to_add: Annotated[list[str], "List of label names to add"],
    labels_to_remove: Annotated[list[str], "List of label names to remove"],
) -> Annotated[ChangeLabelsOutput, "Confirmation with labels that were added and removed"]:
    """
    Add and remove labels from an email using the Gmail API.
    """
    client = GmailClient(context)

    all_target_labels = list(set(labels_to_add + labels_to_remove))
    found_labels_map, all_labels = client.get_label_ids(all_target_labels)

    invalid_labels = set(all_target_labels) - set(found_labels_map.keys())

    if invalid_labels:
        raise RetryableToolError(
            message=f"Invalid labels: {invalid_labels}",
            developer_message=f"Invalid labels: {invalid_labels}",
            additional_prompt_content=f"List of valid labels: {all_labels}",
        )

    body = {
        "addLabelIds": [
            found_labels_map[name] for name in labels_to_add if name in found_labels_map
        ],
        "removeLabelIds": [
            found_labels_map[name] for name in labels_to_remove if name in found_labels_map
        ],
    }

    client.modify_message(email_id, body)

    return {
        "confirmation": {
            "addedLabels": labels_to_add,
            "removedLabels": labels_to_remove,
        }
    }


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_labels(
    context: Context,
) -> Annotated[ListLabelsOutput, "A dictionary containing a list of label details"]:
    """List all the labels in the user's mailbox."""
    client = GmailClient(context)
    labels = client.list_labels()

    mapped_labels = [map_label_to_label_output(label) for label in labels]
    return {"labels": mapped_labels}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.labels"],
    )
)
async def create_label(
    context: Context,
    label_name: Annotated[str, "The name of the label to create"],
) -> Annotated[CreateLabelOutput, "The created label wrapped in label key"]:
    """Create a new label in the user's mailbox."""
    client = GmailClient(context)
    label = client.create_label(label_name)
    return {"label": map_label_to_label_output(label)}
