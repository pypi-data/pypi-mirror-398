from enum import Enum


class GmailReplyToWhom(str, Enum):
    EVERY_RECIPIENT = "every_recipient"
    ONLY_THE_SENDER = "only_the_sender"


class GmailAction(str, Enum):
    SEND = "send"
    DRAFT = "draft"


class GmailContentType(str, Enum):
    """The content type of the email body."""

    PLAIN = "plain"
    HTML = "html"


class DateRange(str, Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
