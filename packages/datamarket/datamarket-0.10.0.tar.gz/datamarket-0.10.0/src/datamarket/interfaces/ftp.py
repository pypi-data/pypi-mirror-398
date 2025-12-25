########################################################################################################################
# IMPORTS

import logging
from ftplib import FTP, FTP_TLS
from pathlib import Path
from typing import Any, Dict, List, Optional

########################################################################################################################
# CLASSES

logger = logging.getLogger(__name__)


class FTPInterface:
    def __init__(self, config):
        self.profiles: List[Dict[str, Any]] = []
        self.config = config
        for section in getattr(self.config, "sections", lambda: [])():
            if section.startswith("ftp:"):
                profile_name = section.split(":", 1)[1]
                ftps = self.config[section]["ftps"].lower() == "true"
                ftp_conn = FTP_TLS(self.config[section]["server"]) if ftps else FTP(self.config[section]["server"])  # noqa: S321
                ftp_conn.login(self.config[section]["username"], self.config[section]["password"])
                self.profiles.append({"profile": profile_name, "session": ftp_conn})

        if not self.profiles:
            logger.warning("no ftp section in config")

        self.current_profile: Optional[Dict[str, Any]] = self.profiles[0] if self.profiles else None
        self.ftp = self.current_profile["session"] if self.current_profile else None

    def switch_profile(self, profile_name: str) -> None:
        for profile in self.profiles:
            if profile["profile"] == profile_name:
                self.current_profile = profile
                self.ftp = profile["session"]
                return
        logger.warning(f"Profile {profile_name} not found")

    def upload_file(self, local_file, remote_folder, remote_file=None):
        if not remote_file:
            remote_file = Path(local_file).name

        self._create_remote_dir_tree(full_path=f"/{remote_folder}{remote_file}")

        self.ftp.cwd(f"/{remote_folder}")

        with open(local_file, "rb") as f:
            self.ftp.storbinary(f"STOR {remote_file}", f)

    def download_file(self, local_file, remote_file):
        with open(local_file, "wb") as f:
            self.ftp.retrbinary(f"RETR {remote_file}", f.write)

    def _create_remote_dir_tree(self, full_path):
        dir_tree = full_path.split("/")[0:-1]  # Exclude filename

        for part in dir_tree:
            if not part:
                continue

            try:
                self.ftp.cwd(part)
            except Exception as e:
                logger.warning(f"Error while creating remote directory: {e}")
                self.ftp.mkd(part)
                self.ftp.cwd(part)
