import io
import shutil
from pathlib import Path
from typing import Any, Iterator, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from gverify import GoogleDriveScopes, GoogleOAuth
from gverify.exceptions import InvalidSecretsFileException
from pydantic import BaseModel

from .exceptions import InvalidSecretsFileError, MissingClientSecretsFile


class GoogleDrive:
    """Provides methods for interacting with the GoogleDrive API.

    This class acts as an interface to the GoogleDrive API, providing methods for interacting with
    the GoogleDrive V3 API.

    Attributes
    ----------
    client_secret_file: str
        The path to the json file containing your authentication information.
    """

    def __init__(self, client_secret_file: Optional[str] = None) -> None:
        """Initialize the GoogleDrive instance."""
        self.client_secret_file: Optional[str] = client_secret_file
        self.drive_client: Optional[Any] = None

    def authenticate(self, client_secret_file: Optional[str] = None) -> None:
        """Authenticate the requests made to youtube.

        Used to generate the credentials that are used when authenticating requests to youtube.

        Parameters
        ----------
        client_secret_file: str
            The path to clients secret json file from Google

        Raises
        ------
        ValueError:
            When the client secrets file is not provided
        FileNotFoundError:
            When the secrets file path is not found
        """
        if client_secret_file:
            self.client_secret_file = client_secret_file
        if not self.client_secret_file:
            raise MissingClientSecretsFile("The client secret file must be provided.")
        if not Path(self.client_secret_file).exists():
            raise FileNotFoundError("The client secret file was not found.")
        api_service_name: str = "drive"
        api_version: str = "v3"
        credentials_dir: str = ".drive"
        scopes: list[str] = [
            GoogleDriveScopes.drive.value,
        ]
        oauth: GoogleOAuth = GoogleOAuth(
            secrets_file=self.client_secret_file,
            scopes=scopes,
            api_service_name=api_service_name,
            api_version=api_version,
            credentials_dir=credentials_dir,
        )
        try:
            self.drive_client = oauth.authenticate_google_server()
        except InvalidSecretsFileException as e:
            raise InvalidSecretsFileError(e)

    def authenticate_from_credentials(self, credentials_path: str) -> None:
        api_service_name: str = "drive"
        api_version: str = "v3"
        credentials_dir: str = ".drive"
        scopes: list[str] = [
            GoogleDriveScopes.drive.value,
        ]
        oauth: GoogleOAuth = GoogleOAuth(
            scopes=scopes,
            api_service_name=api_service_name,
            api_version=api_version,
            credentials_dir=credentials_dir,
        )
        credentials: Credentials = oauth.load_credentials(credentials_path)
        self.drive_client = oauth.authenticate_from_credentials(credentials)

    def list_files(
        self, page_size: int = 10, query: Optional[str] = None
    ) -> Iterator[dict]:
        """List files in the Google Drive.

        Parameters
        ----------
        page_size: int
            The number of files to return per page.
        query: str
            The query to filter the files.

        Returns
        -------
        Iterator[dict]
            An iterator of file metadata dictionaries.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        results = (
            self.drive_client.files()
            .list(pageSize=100, fields="files(id, name)")
            .execute()
        )
        items = results.get("files", [])
        if not items:
            return iter([])
        for item in items:
            yield {
                "id": item["id"],
                "name": item["name"],
                "size": item.get("size", 0),  # Size may not be available for all files
            }

    def upload_file(self, file_path: str, mime_type: str) -> dict:
        """Upload a file to Google Drive.

        Parameters
        ----------
        file_path: str
            The path to the file to upload.
        mime_type: str
            The MIME type of the file.

        Returns
        -------
        dict
            The metadata of the uploaded file.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        file_metadata = {"name": Path(file_path).name}
        media = MediaFileUpload(file_path, mimetype=mime_type)
        file = (
            self.drive_client.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        return file
        # return {'id': file.get('id'), 'name': file_metadata['name']}

    def get_file_metadata(self, file_id: str) -> dict:
        """Get metadata of a file by its ID.

        Parameters
        ----------
        file_id: str
            The ID of the file.

        Returns
        -------
        dict
            The metadata of the file.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        file = self.drive_client.files().get(fileId=file_id, fields="*").execute()
        return file

    def update_file_permissions(self, file_id: str, permissions: list[dict]) -> None:
        """Update permissions of a file.

        Parameters
        ----------
        file_id: str
            The ID of the file.
        permissions: list[dict]
            A list of permission dictionaries to apply to the file.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        for permission in permissions:
            self.drive_client.permissions().create(
                fileId=file_id,
                body=permission,
                fields="id",
            ).execute()

    def download_file(self, file_id: str, file_path: str) -> bool:
        """Download a file from Google Drive.

        Parameters
        ----------
        file_id: str
            The ID of the file to download.

        Returns
        -------
        bytes
            The content of the downloaded file.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        request = self.drive_client.files().get_media(fileId=file_id)
        fh = io.BytesIO()

        # Initialise a downloader object to download the file
        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        done = False

        try:
            # Download the data in chunks
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)

            # Write the received data to the file
            with open(file_path, "wb") as f:
                shutil.copyfileobj(fh, f)

            print("File Downloaded")
            # Return True if file Downloaded successfully
            return True
        except:

            # Return False if something went wrong
            print("Something went wrong.")
            return False

    def download_file_content(self, file_id: str) -> bytes:
        """Download a file from Google Drive.

        Parameters
        ----------
        file_id: str
            The ID of the file to download.

        Returns
        -------
        bytes
            The content of the downloaded file.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        request = self.drive_client.files().get_media(fileId=file_id)
        fh = io.BytesIO()

        # Initialise a downloader object to download the file
        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        done = False

        try:
            # Download the data in chunks
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)
            return fh.read()
        except Exception as e:
            print(f"Something went wrong: {e}")
            return b""

    def move_file(self, file_id: str, new_folder_id: str) -> dict:
        """Move a file to a new folder.

        Parameters
        ----------
        file_id: str
            The ID of the file to move.
        new_folder_id: str
            The ID of the folder to move the file to.

        Returns
        -------
        dict
            The updated metadata of the moved file.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        # Retrieve the existing parents to remove
        file = self.drive_client.files().get(fileId=file_id, fields="parents").execute()
        previous_parents = ",".join(file.get("parents"))
        # Move the file to the new folder
        file = (
            self.drive_client.files()
            .update(
                fileId=file_id,
                addParents=new_folder_id,
                removeParents=previous_parents,
                fields="id, parents",
            )
            .execute()
        )
        return file

    def create_folder(
        self, folder_name: str, parent_folder_id: Optional[str] = None
    ) -> dict:
        """Create a new folder in Google Drive.

        Parameters
        ----------
        folder_name: str
            The name of the folder to create.
        parent_folder_id: str, optional
            The ID of the parent folder to create the new folder in.

        Returns
        -------
        dict
            The metadata of the created folder.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]
        folder = (
            self.drive_client.files().create(body=file_metadata, fields="id").execute()
        )
        return folder

    def search_folders(self, folder_name: str) -> Iterator[dict]:
        """Search for folders by name.

        Parameters
        ----------
        folder_name: str
            The name of the folder to search for.
        Returns
        -------
        Iterator[dict]
            An iterator of folder metadata dictionaries.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
        results = (
            self.drive_client.files().list(q=query, fields="files(id, name)").execute()
        )
        items = results.get("files", [])
        if not items:
            return iter([])
        for item in items:
            yield {
                "id": item["id"],
                "name": item["name"],
            }

    def list_folders(self, page_size: int = 10) -> Iterator[dict]:
        """List folders in the Google Drive.

        Parameters
        ----------
        page_size: int
            The number of folders to return per page.

        Returns
        -------
        Iterator[dict]
            An iterator of folder metadata dictionaries.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        query = "mimeType = 'application/vnd.google-apps.folder'"
        results = (
            self.drive_client.files()
            .list(q=query, pageSize=page_size, fields="files(id, name)")
            .execute()
        )
        items = results.get("files", [])
        if not items:
            return iter([])
        for item in items:
            yield {
                "id": item["id"],
                "name": item["name"],
            }

    def list_files_in_folder(self, folder_id: str) -> Iterator[dict]:
        """List files in a folder in the Google Drive.

        Parameters
        ----------
        folder_id: str
            The ID of the folder.

        Returns
        -------
        Iterator[dict]
            An iterator of file metadata dictionaries.
        """
        if not self.drive_client:
            raise ValueError("Drive client is not authenticated.")
        results = (
            self.drive_client.files()
            .list(q=f"'{folder_id}' in parents", fields="files(id, name)")
            .execute()
        )
        items = results.get("files", [])
        if not items:
            return iter([])
        for item in items:
            yield {
                "id": item["id"],
                "name": item["name"],
            }
