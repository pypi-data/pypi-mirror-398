from typing import Callable
from pydantic import BaseModel
from scoutsdk import scout
from ..indexers_impl.utils.assistant_data_utils import need_to_index
from ..crawlers import CrawlerConfiguration, Crawler

import fnmatch
import requests


class SharepointCrawlerConfiguration(CrawlerConfiguration):
    tenant_id: str
    client_id: str
    tenant_name: str
    site_name: str
    client_secret_key: str
    folder_path: str = "/"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }


class SharepointCrawler(Crawler):
    configuration: SharepointCrawlerConfiguration

    def __init__(
        self,
        configuration: CrawlerConfiguration,
        on_url_found: Callable[[str, bool], None],
    ):
        super().__init__(configuration, on_url_found)
        self._configuration = SharepointCrawlerConfiguration(
            **configuration.model_dump()
        )
        self._on_url_found = on_url_found

    def get_access_token(self) -> TokenResponse:
        # Les informations d'identification
        tenant_id = self._configuration.tenant_id
        client_id = self._configuration.client_id
        client_secret = scout.context[self._configuration.client_secret_key]

        # URL pour obtenir le token
        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }

        response = requests.post(url, data=payload)
        response.raise_for_status()
        token_data = response.json()
        return TokenResponse(**token_data)

    def get_site_id(
        self, tenant_name: str, site_name: str, token: TokenResponse
    ) -> str:
        site_url = f"https://graph.microsoft.com/v1.0/sites/{tenant_name}.sharepoint.com:/sites/{site_name}"
        site_response = requests.get(site_url, headers=token.headers).json()
        return site_response.get("id") or ""

    def download_url(self, folder_relative_path: str, local_filename: str) -> str:
        token = self.get_access_token()
        site_id = self.get_site_id(
            self._configuration.tenant_name, self._configuration.site_name, token
        )
        path = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{folder_relative_path}"

        response = requests.get(path, headers=token.headers)
        item_response = response.json()
        download_url = item_response.get("@microsoft.graph.downloadUrl")
        response = requests.get(download_url, headers=token.headers)
        response.raise_for_status()
        with open(local_filename, "wb") as file:
            file.write(response.content)
        return item_response.get("webUrl") or ""

    def crawl(self) -> None:
        token = self.get_access_token()
        site_id = self.get_site_id(
            self._configuration.tenant_name, self._configuration.site_name, token
        )
        self.get_items_in_folder(site_id, self._configuration.folder_path, token)

    def on_file_found(
        self, item: dict, full_path: str, folder_relative_path: str
    ) -> None:
        if any(
            fnmatch.fnmatch(full_path, mask)
            for mask in self._configuration.included_masks
        ) and item.get("fileSystemInfo"):
            item["folderPath"] = folder_relative_path
            last_modified = item["fileSystemInfo"]["lastModifiedDateTime"]
            public_url = item["webUrl"]
            if need_to_index(public_url, last_modified):
                is_important = any(
                    fnmatch.fnmatch(full_path, mask)
                    for mask in self._configuration.important_document_masks
                )
                self._on_url_found(full_path, is_important)

    def get_items_in_folder(
        self, site_id: str, folder_relative_path: str, token: TokenResponse
    ) -> None:
        if folder_relative_path == "/":
            drive_items_url = (
                f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root/children"
            )
        else:
            # Enlever le premier slash pour le chemin relatif
            if folder_relative_path.startswith("/"):
                folder_relative_path = folder_relative_path[1:]

            drive_items_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{folder_relative_path}"
            import os

            if len(os.path.splitext(drive_items_url)[1]) == 0:
                # This is a folder
                drive_items_url += ":/children"

        if any(
            fnmatch.fnmatch(folder_relative_path, mask)
            for mask in self._configuration.excluded_masks
        ):
            return

        items_response = requests.get(drive_items_url, headers=token.headers).json()
        if isinstance(items_response, dict) and "value" not in items_response:
            # This is a single item (folder or file), check if it's a folder
            if "folder" in items_response:
                # This is a folder, get its children
                folder_children_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{items_response['id']}/children"
                items_response = requests.get(
                    folder_children_url, headers=token.headers
                ).json()
            else:
                # This is a file
                self.on_file_found(
                    items_response, folder_relative_path, folder_relative_path
                )
        while "value" in items_response:
            if "value" in items_response:
                for item in items_response["value"]:
                    item_name = item["name"]
                    if any(
                        fnmatch.fnmatch(item["name"], mask)
                        for mask in self._configuration.excluded_masks
                    ):
                        continue

                    full_path = (
                        folder_relative_path + "/" + item_name
                        if folder_relative_path != "/"
                        else "/" + item_name
                    )

                    if "folder" in item:
                        self.get_items_in_folder(site_id, full_path, token)
                    elif item.get("@microsoft.graph.downloadUrl") is not None:
                        self.on_file_found(item, full_path, folder_relative_path)

            if "@odata.nextLink" in items_response:
                next_page_url = items_response["@odata.nextLink"]
                items_response = requests.get(
                    next_page_url, headers=token.headers
                ).json()
                if (
                    items_response.get("@odata.nextLink") is None
                    or items_response.get("@odata.nextLink") == next_page_url
                ):
                    break
            else:
                break
