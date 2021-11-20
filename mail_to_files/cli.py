import logging
import click
from pathlib import Path
from .mailing import delete_mails, get_mails
from .config import Config
from logging import getLogger, log
from webdav3.client import Client
from io import BytesIO, StringIO
import sys

logger = getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


@click.command()
@click.option(
    "--config-file",
    "-c",
    help="Please specify path to config file. Default is cwd.",
    type=click.Path(dir_okay=False, file_okay=True, path_type=Path, resolve_path=True),
    required=True,
)
@click.option(
    "--keep-mails", "-k", help="Add this flag to avoid deletion of emails", is_flag=True
)
@click.option(
    "--dry-run",
    "-d",
    help="Add this flag to avoid deletion of emails and uploading of files",
    is_flag=True,
)
def cli(config_file: Path, keep_mails: bool, dry_run: bool):
    if dry_run:
        click.echo(click.style("Running in Dry Run Mode",fg="green"))
    config: Config = Config.from_config_file(config_file)

    click.echo("Retrieving mails...", nl=False)
    mails = get_mails(config.imap)
    n_mails = len(mails)
    click.echo(f"[OK] ({n_mails} mails)")

    click.echo("Connecting to Nextcloud...", nl=False)
    nx_client = Client(config.next_cloud.as_webdav_options())
    click.echo("[OK]")

    click.echo("Uploading emails...")
    successful_mail_ids = []
    for i, mail in enumerate(mails, start=1):
        click.echo(f"====> Mail: {i}/{n_mails} <====")
        person = (
            mail.person
            if mail.person
            else config.person_email.get(mail.sender.lower(), "unknown")
        )
        tags = mail.tags if person in mail.tags else [person, *mail.tags]

        target_filename = config.target_filename_pattern.format(
            date=mail.received_date,
            description=mail.description,
            tags=" ".join(tags),
        )
        click.echo(f">> Derived information:")
        click.echo(f"\t>> Person: {person}")
        click.echo(f"\t>> Tags: {tags}")
        click.echo(f"\t>> Filename: {target_filename}")

        click.echo(f">> Uploading...", nl=False)
        if not dry_run:
            nx_client.upload_to(
                BytesIO(mail.attachment),
                f"{config.next_cloud.archive_path}/{target_filename}",
            )
        successful_mail_ids.append(mail.mail_id)
        click.echo("[OK]")

    if not keep_mails:
        click.echo(f"Deleting all successfully parsed emails...", nl=False)

        if not dry_run:
            delete_mails(config.imap, successful_mail_ids)

        click.echo("[OK]")
