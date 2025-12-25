########################################################################################################################
# IMPORTS

import logging

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

########################################################################################################################
# CLASSES

logger = logging.getLogger(__name__)
logging.getLogger("googleapicliet.discovery_cache").setLevel(logging.ERROR)


class DriveInterface:
    def __init__(self, config):
        if "drive" in config:
            self.config = config["drive"]

            GoogleAuth.DEFAULT_SETTINGS["client_config_file"] = f"{self.config['config_path']}/credentials.json"

            self.gauth = GoogleAuth(settings_file=f"{self.config['config_path']}/settings.yaml")
            self.gauth.LocalWebserverAuth()

            self.drive = GoogleDrive(self.gauth)

            self.team_id = self.config["team_id"]

        else:
            logger.warning("no drive section in config")

    def delete_old_files(self, filename, folder_id):
        for drive_file in self.drive.ListFile(
            {
                "q": f"'{folder_id}' in parents and trashed=false",
                "corpora": "teamDrive",
                "teamDriveId": self.team_id,
                "includeTeamDriveItems": True,
                "supportsTeamDrives": True,
            }
        ).GetList():
            if drive_file["title"] == filename:
                logger.info(f"deleting old {filename}...")
                drive_file.Delete(param={"supportsTeamDrives": True})

    def _create_remote_dir_tree(self, base_folder_id, path_parts):
        """
        Ensure the nested folders described by path_parts exist under base_folder_id.
        Returns the folder_id of the deepest folder (or base_folder_id if path_parts is empty).
        """
        parent_id = base_folder_id
        for part in path_parts:
            part = part.strip()
            if not part:
                continue

            query = (
                f"'{parent_id}' in parents and title = '{part}'"
                " and mimeType = 'application/vnd.google-apps.folder' and trashed=false"
            )
            results = self.drive.ListFile(
                {
                    "q": query,
                    "corpora": "teamDrive",
                    "teamDriveId": self.team_id,
                    "includeTeamDriveItems": True,
                    "supportsTeamDrives": True,
                }
            ).GetList()

            if results:
                parent_id = results[0]["id"]
            else:
                folder_metadata = {
                    "title": part,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [
                        {
                            "kind": "drive#fileLink",
                            "teamDriveId": self.team_id,
                            "id": parent_id,
                        }
                    ],
                }
                folder = self.drive.CreateFile(folder_metadata)
                folder.Upload(param={"supportsTeamDrives": True})
                parent_id = folder["id"]

        return parent_id

    def upload_file(self, local_filename, drive_filename, folder_id):
        drive_filename = drive_filename.strip("/")
        parts = drive_filename.split("/")
        if len(parts) > 1:
            *folders, filename = parts
            target_folder_id = self._create_remote_dir_tree(folder_id, folders)
        else:
            filename = parts[0]
            target_folder_id = folder_id

        self.delete_old_files(filename, target_folder_id)

        f = self.drive.CreateFile(
            {
                "title": filename,
                "parents": [
                    {
                        "kind": "drive#fileLink",
                        "teamDriveId": self.team_id,
                        "id": target_folder_id,
                    }
                ],
            }
        )
        f.SetContentFile(local_filename)

        logger.info(f"uploading {drive_filename} to folder: {target_folder_id}...")
        f.Upload(param={"supportsTeamDrives": True})

    def validate_file(self, filename, folder_id):
        for drive_file in self.drive.ListFile(
            {
                "q": f"'{folder_id}' in parents and trashed=false",
                "corpora": "teamDrive",
                "teamDriveId": self.team_id,
                "includeTeamDriveItems": True,
                "supportsTeamDrives": True,
            }
        ).GetList():
            if drive_file["title"] == filename:
                logger.info(f"{filename} correctly uploaded.")
                return

        raise FileNotFoundError(f"{filename} has not been correctly uploaded.")
