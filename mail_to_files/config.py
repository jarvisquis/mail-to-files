from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import dacite
import yaml


@dataclass
class ImapConfig:
    host: str
    port: int
    user: str
    password: str
    mailbox: str
    da_subject: Optional[str] = "da"


@dataclass
class NextCloudConfig:
    url: str
    user: str
    password: str
    archive_path: str

    def as_webdav_options(self) -> Dict[str, str]:
        return {
            "webdav_hostname": self.url,
            "webdav_login": self.user,
            "webdav_password": self.password,
        }


@dataclass()
class Config:
    imap: ImapConfig
    next_cloud: NextCloudConfig
    person_email: dict
    target_filename_pattern: Optional[str] = "{date:%Y-%m-%d}_{description}_[{tags}].pdf"

    @classmethod
    def from_config_file(cls, config_file: Path):
        with config_file.open("r") as config_fp:
            data = yaml.safe_load(config_fp)

        return dacite.from_dict(cls, data)
