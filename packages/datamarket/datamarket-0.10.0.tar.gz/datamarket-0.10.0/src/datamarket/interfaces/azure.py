########################################################################################################################
# IMPORTS

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from azure.storage.blob import BlobServiceClient, ContainerClient
from pendulum import now

########################################################################################################################
# CLASSES

logger = logging.getLogger(__name__)


class AzureBlobInterface:
    def __init__(self, config):
        self.profiles: List[Dict[str, Any]] = []
        self.config = config

        for section in getattr(self.config, "sections", lambda: [])():
            if section.startswith("azure:"):
                profile_name = section.split(":", 1)[1]
                connection_string = self.config[section].get("connection_string")
                container_name = self.config[section].get("container_name")
                sas_container_url = self.config[section].get("sas_container_url")

                if sas_container_url:
                    session = ContainerClient.from_container_url(sas_container_url)
                elif connection_string and container_name:
                    session = BlobServiceClient.from_connection_string(connection_string).get_container_client(
                        container_name
                    )

                self.profiles.append(
                    {
                        "profile": profile_name,
                        "container_name": container_name,
                        "session": session,
                    }
                )

        if not self.profiles:
            logger.warning("No Azure profiles found in config file")
        self.current_profile: Optional[Dict[str, Any]] = self.profiles[0] if self.profiles else None

    def switch_profile(self, profile_name: str) -> None:
        for profile in self.profiles:
            if profile["profile"] == profile_name:
                self.current_profile = profile
                return
        logger.warning(f"Profile {profile_name} not found")

    def upload_file(
        self,
        local_file,
        remote_folder,
        remote_file=None,
        upload_file_info=False,
        **file_info_data,
    ):
        if not remote_file:
            remote_file = Path(local_file).name

        remote_path = f"{remote_folder}/{remote_file}" if remote_folder else remote_file

        blob_client = self.current_profile["session"].get_blob_client(remote_path)
        with open(local_file, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        if upload_file_info:
            self.upload_file_info(remote_path, **file_info_data)

    def upload_file_info(self, remote_path, **file_info_data):
        summary_file = remote_path.split(".")[0] + "_resumen.csv"
        blob_client = self.current_profile["session"].get_blob_client(summary_file)

        new_record = {
            "file": remote_path,
            "num_rows": file_info_data.get("num_rows"),
            "schema_version": file_info_data.get("schema_version"),
            "upload_date": now(tz="Europe/Madrid").to_datetime_string(),
        }

        new_record_str = "file,num_rows,schema_version,upload_date\n"
        new_record_str += ",".join([str(v) for v in new_record.values()]) + "\n"

        blob_client.upload_blob(new_record_str, overwrite=True)

    def download_file(self, local_file, remote_path):
        blob_client = self.current_profile["session"].get_blob_client(remote_path)
        blob_data = blob_client.download_blob()
        with open(local_file, "wb") as f:
            blob_data.readinto(f)

    def check_file_exists_and_not_empty(self, remote_file, remote_folder):
        """
        Checks if a blob exists in the specified folder and has a size greater than 100 bytes.

        Args:
            remote_file (str): The name of the file (blob) to check.
            remote_folder (str): The folder (prefix) where the file is located.

        Returns:
            bool: True if the blob exists and has a size greater than 100, False otherwise.
        """

        remote_path = f"{remote_folder}/{remote_file}" if remote_folder else remote_file

        try:
            blob_client = self.current_profile["session"].get_blob_client(remote_path)
            if blob_client.exists():
                properties = blob_client.get_blob_properties()
                if properties.size > 100:  # Check if size is greater than 100 bytes
                    logger.debug(f"Blob '{remote_path}' exists and is not empty (size: {properties.size}).")
                    return True
                else:
                    logger.debug(f"Blob '{remote_path}' exists but size ({properties.size}) is not > 100 bytes.")
                    return False
            else:
                logger.debug(f"Blob '{remote_path}' does not exist.")
                return False
        except Exception as e:
            logger.error(f"Error checking blob '{remote_path}': {e}")
            # In case of error, assume it doesn't exist or is empty to allow upload attempt
            return False
