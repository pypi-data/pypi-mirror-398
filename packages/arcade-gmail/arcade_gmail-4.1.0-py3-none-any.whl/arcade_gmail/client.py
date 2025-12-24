import logging
from typing import Any

from arcade_mcp_server import Context
from arcade_mcp_server.exceptions import ToolExecutionError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from arcade_gmail.models.api_responses import (
    Draft,
    Label,
    Message,
    Thread,
    ThreadListResponse,
    UserProfile,
)

logger = logging.getLogger(__name__)


class GmailClient:
    def __init__(self, context: Context):
        self.context = context
        self._service = None

    @property
    def service(self) -> Any:
        if not self._service:
            self._service = self._build_service()
        return self._service

    def _build_service(self) -> Any:
        try:
            credentials = Credentials(
                self.context.authorization.token
                if self.context.authorization and self.context.authorization.token
                else ""
            )
            return build("gmail", "v1", credentials=credentials)
        except Exception as e:
            raise ToolExecutionError(
                message="Failed to build Gmail service.", developer_message=str(e)
            )

    def list_messages(self, query: str, limit: int = 100) -> list[Message]:
        response = (
            self.service.users().messages().list(userId="me", q=query, maxResults=limit).execute()
        )
        return response.get("messages", [])  # type: ignore[no-any-return]

    def list_drafts(self, limit: int = 100) -> list[Draft]:
        response = self.service.users().drafts().list(userId="me", maxResults=limit).execute()
        return response.get("drafts", [])  # type: ignore[no-any-return]

    def get_messages_batch(self, message_ids: list[str]) -> list[Message]:
        if not message_ids:
            return []

        results: dict[str, Any] = {}

        def callback(request_id: str, response: Any, exception: Exception | None) -> None:
            if exception:
                logger.warning(f"Failed to fetch message {request_id}: {exception}")
            else:
                results[request_id] = response

        batch = self.service.new_batch_http_request(callback=callback)

        for i, msg_id in enumerate(message_ids):
            batch.add(
                self.service.users().messages().get(userId="me", id=msg_id),
                request_id=str(i),
            )

        batch.execute()

        ordered_messages = []
        for i in range(len(message_ids)):
            if str(i) in results:
                ordered_messages.append(results[str(i)])

        return ordered_messages

    def get_drafts_batch(self, draft_ids: list[str]) -> list[Draft]:
        if not draft_ids:
            return []

        results: dict[str, Any] = {}

        def callback(request_id: str, response: Any, exception: Exception | None) -> None:
            if exception:
                logger.warning(f"Failed to fetch draft {request_id}: {exception}")
            else:
                results[request_id] = response

        batch = self.service.new_batch_http_request(callback=callback)

        for i, draft_id in enumerate(draft_ids):
            batch.add(
                self.service.users().drafts().get(userId="me", id=draft_id),
                request_id=str(i),
            )

        batch.execute()

        ordered_drafts = []
        for i in range(len(draft_ids)):
            if str(i) in results:
                ordered_drafts.append(results[str(i)])

        return ordered_drafts

    def send_message(self, body: dict[str, Any]) -> Message:
        return self.service.users().messages().send(userId="me", body=body).execute()  # type: ignore[no-any-return]

    def create_draft(self, draft: dict[str, Any]) -> Draft:
        return self.service.users().drafts().create(userId="me", body=draft).execute()  # type: ignore[no-any-return]

    def update_draft(self, draft_id: str, draft: dict[str, Any]) -> Draft:
        return self.service.users().drafts().update(userId="me", id=draft_id, body=draft).execute()  # type: ignore[no-any-return]

    def send_draft(self, draft_id: str) -> Message:
        return self.service.users().drafts().send(userId="me", body={"id": draft_id}).execute()  # type: ignore[no-any-return]

    def delete_draft(self, draft_id: str) -> None:
        self.service.users().drafts().delete(userId="me", id=draft_id).execute()

    def trash_message(self, message_id: str) -> Message:
        return self.service.users().messages().trash(userId="me", id=message_id).execute()  # type: ignore[no-any-return]

    def get_message(self, message_id: str) -> Message:
        return self.service.users().messages().get(userId="me", id=message_id).execute()  # type: ignore[no-any-return]

    def list_threads(
        self,
        query: str | None,
        limit: int = 100,
        page_token: str | None = None,
        include_spam_trash: bool = False,
        label_ids: list[str] | None = None,
    ) -> ThreadListResponse:
        params = {
            "userId": "me",
            "maxResults": limit,
            "pageToken": page_token,
            "includeSpamTrash": include_spam_trash,
            "q": query,
            "labelIds": label_ids,
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        return self.service.users().threads().list(**params).execute()  # type: ignore[no-any-return]

    def get_thread(self, thread_id: str) -> Thread:
        result: Thread = (
            self.service.users().threads().get(userId="me", id=thread_id, format="full").execute()
        )
        return result

    def list_labels(self) -> list[Label]:
        return self.service.users().labels().list(userId="me").execute().get("labels", [])  # type: ignore[no-any-return]

    def create_label(self, name: str) -> Label:
        return self.service.users().labels().create(userId="me", body={"name": name}).execute()  # type: ignore[no-any-return]

    def get_label_ids(self, label_names: list[str]) -> tuple[dict[str, str], list[str]]:
        """
        Retrieve label IDs for given label names.
        Returns a tuple containing:
        1. A dictionary mapping found label names to their corresponding IDs.
        2. A list of all available label names.
        """
        # Fetch all existing labels from Gmail
        labels = self.list_labels()

        # Create a mapping from label names to their IDs
        label_id_map = {label["name"]: label["id"] for label in labels}
        all_label_names = list(label_id_map.keys())

        found_labels = {}
        for name in label_names:
            label_id = label_id_map.get(name)
            if label_id:
                found_labels[name] = label_id
            else:
                logger.warning(f"Label '{name}' does not exist")

        return found_labels, all_label_names

    def modify_message(self, message_id: str, body: dict[str, Any]) -> Message:
        result: Message = (
            self.service.users().messages().modify(userId="me", id=message_id, body=body).execute()
        )
        return result

    def get_profile(self) -> UserProfile:
        result: UserProfile = self.service.users().getProfile(userId="me").execute()
        return result
