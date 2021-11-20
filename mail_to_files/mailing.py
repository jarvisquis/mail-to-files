import email
import email.policy
from dataclasses import dataclass, field
from datetime import datetime
from email.message import EmailMessage
from imaplib import IMAP4, IMAP4_SSL
from typing import List, Optional, Union

from .config import ImapConfig

DATE_FMT = "%a, %d %b %Y %H:%M:%S %z"


@dataclass
class DataArchiveMail:
    mail_id: Union[int, str]
    sender: str
    body: str
    attachment: bytes
    received_date: datetime
    person: Optional[str] = field(init=False)
    description: str = field(init=False)
    tags: List[str] = field(init=False)
    _body_lines: List[str] = field(init=False)

    def __post_init__(self) -> None:
        self._body_lines = self.body.splitlines()
        self.person = self._get_person()
        self.description = self._get_description()
        self.tags = self._get_tags()

    @staticmethod
    def _str_prepare(value: str) -> str:
        return value.lower().strip().replace(" ", "-")

    def _get_tags(self) -> List[str]:
        return [self._str_prepare(t) for t in self._body_lines[1].split(" ")]

    def _get_description(self) -> Optional[str]:
        try:
            return self._str_prepare(self._body_lines[0])
        except IndexError:
            return

    def _get_person(self) -> Optional[str]:
        try:
            return self._str_prepare(self._body_lines[2])
        except IndexError:
            return


def _get_pdf_attachments(message: EmailMessage) -> Optional[tuple]:
    return [
        part
        for part in message.iter_attachments()
        if part.get_content_type() == "application/pdf"
    ]


def _get_mail_ids(M: IMAP4, data_archive_subject: str) -> list:
    _, data = M.search(None, "SUBJECT", f'"{data_archive_subject}"')
    return data[0].split()


def _get_message(M: IMAP4, mail_id: str) -> Optional[EmailMessage]:
    _, response = M.fetch(mail_id, "(RFC822)")
    (_, message_bytes), _ = response
    return email.message_from_bytes(message_bytes, policy=email.policy.default)


def get_mails(config: ImapConfig) -> List[DataArchiveMail]:
    da_mails = []

    with IMAP4_SSL(config.host, port=config.port) as M:
        # Login and select inbox
        M.login(config.user, config.password)
        M.select(config.mailbox)

        # Query all message ids having in subject the da_subject
        mail_ids = _get_mail_ids(M, config.da_subject)

        # Process all emails...
        for mail_id in mail_ids:

            # ...find main message part...
            message = _get_message(M, mail_id)
            sender = message.get("from").split("<")[-1][:-1]
            received_date = datetime.strptime(message.get("date"), DATE_FMT)
            body = message.get_body(preferencelist=("plain",))
            attachments = _get_pdf_attachments(message)

            if len(attachments) == 0 or body is None:
                continue

            da_mails.append(
                DataArchiveMail(
                    mail_id=mail_id,
                    sender=sender,
                    received_date=received_date,
                    attachment=attachments[0].get_payload(decode=True),
                    body=body.get_payload(),
                )
            )
    return da_mails


def delete_mails(config: ImapConfig, mail_ids: List[Union[int, str]]):
    with IMAP4_SSL(config.host, port=config.port) as M:
        M.login(config.user, config.password)
        M.select(config.mailbox)

        for mail_id in mail_ids:
            M.store(mail_id, '+X-GM-LABELS', '\\Trash')
            M.store(mail_id, "+FLAGS", "\\Deleted")
        M.expunge()
