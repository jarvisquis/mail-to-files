from enum import Enum
from .config import ImapConfig
import imaplib


class MailFilter(Enum):
    ALL = 0
    ONLY_WITH_PDF_ATTACHMENT = 1
    HAS_DA_SUBJECT = 2


def __is_valid(mail):
    pass


def get_mails(config: ImapConfig, filters: List[MailFilter]) -> list:
    with imaplib.IMAP4_SSL(host=config.host, port=config.port) as M:
        M.login(config.user, config.password)
        M.select(config.mailbox)
        type, data = M.search(None, "ALL")
