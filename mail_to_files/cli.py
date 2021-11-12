import click
from pathlib import Path
from .mailing import get_mails, MailFilter
from .config import Config
from logging import getLogger, log

logger = getLogger(__name__)


@click.command()
@click.option(
    "--config-file",
    "-c",
    help="Please specify path to config file. Default is cwd.",
    type=click.Path(dir_okay=False, file_okay=True, path_type=Path, resolve_path=True),
)
def cli(config_file: Path):
    config: Config = Config.from_config_file(config_file)

    logger.info("Retrieving mails...")
    mails = get_mails(
        config.imap,
        filters=[MailFilter.ONLY_WITH_PDF_ATTACHMENT, MailFilter.HAS_DA_SUBJECT],
    )
    logger.info(f">> Total: {len(mails)} mails received")

    logger.info("Iterating through mails...")
    for mail in mails:
        sender_address = mail.sender
        content = mail.content
        attachment = mail.attachment
        received_date = mail.received

        person = config.person_email.get(sender_address, "unknown")
        description = content[0].strip()
        tags = content[1].strip().replace(" ", ",")

        # Overwrite person if person was specified within third line
        if content.third_line.exists():
            person = content[2]

        if person not in tags:
            tags.append(person)

        target_filename = config.target_filename_pattern.format(
            date=received_date,
            description=description,
            tags=tags,
        )
        nexus.add_to_archive(target_filename, data=attachment.bytes)

    delete_all_mails(config.imap)
