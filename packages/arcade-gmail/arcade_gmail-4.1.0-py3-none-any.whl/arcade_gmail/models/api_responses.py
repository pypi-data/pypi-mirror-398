from typing_extensions import TypedDict


class Header(TypedDict, total=False):
    name: str
    value: str


class Body(TypedDict, total=False):
    attachmentId: str
    size: int
    data: str


class MessagePart(TypedDict, total=False):
    partId: str
    mimeType: str
    filename: str
    headers: list[Header]
    body: Body
    parts: list["MessagePart"]


class Message(TypedDict, total=False):
    id: str
    threadId: str
    labelIds: list[str]
    snippet: str
    historyId: str
    internalDate: str
    payload: MessagePart
    sizeEstimate: int
    raw: str


class MessageListResponse(TypedDict, total=False):
    messages: list[Message]
    nextPageToken: str
    resultSizeEstimate: int


class Draft(TypedDict, total=False):
    id: str
    message: Message


class DraftListResponse(TypedDict, total=False):
    drafts: list[Draft]
    nextPageToken: str
    resultSizeEstimate: int


class Thread(TypedDict, total=False):
    id: str
    snippet: str
    historyId: str
    messages: list[Message]


class ThreadListResponse(TypedDict, total=False):
    threads: list[Thread]
    nextPageToken: str
    resultSizeEstimate: int


class Label(TypedDict, total=False):
    id: str
    name: str
    messageListVisibility: str
    labelListVisibility: str
    type: str
    messagesTotal: int
    messagesUnread: int
    threadsTotal: int
    threadsUnread: int
    color: dict[str, str]


class LabelListResponse(TypedDict, total=False):
    labels: list[Label]


class UserProfile(TypedDict, total=False):
    emailAddress: str
    messagesTotal: int
    threadsTotal: int
    historyId: str
