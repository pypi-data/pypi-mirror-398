import logging
import re
from typing import Any

import msal
import requests
from io import BytesIO
import concurrent.futures
from openpyxl.utils import get_column_letter

logging.basicConfig(
    level=logging.INFO,  # 设置日志级别，INFO 以上都会显示
    format="%(asctime)s - %(levelname)s - %(message)s"
)

BATCH_DOWNLOAD_LIMIT = 20
UPLOAD_FILE_CHUNK_SIZE = 5 * 1024 * 1024


class SharePointManager:
    def __init__(self, public_service_user_name, public_service_user_password, token_name, service_url, site_name, site_domain='bosch.sharepoint.com', verify_ssl=False):
        """ This function is used to initialize SharePointManager class.

        Args:
            public_service_user_name(str): Public service username
            public_service_user_password(str): Public service user password
            token_name(str): Token name in public service
            service_url(str): Public service URL
            site_name(str): SharePoint site name. e.g. msteams_3167868-OIS2Teamchannel
            site_domain(str): SharePoint site domain, default is 'bosch.sharepoint.com'
            verify_ssl(bool|str): Whether to verify SSL certificate
        """
        self.public_service_user_name = public_service_user_name
        self.public_service_user_password = public_service_user_password
        self.token_name = token_name
        self.verify_ssl = verify_ssl
        self.service_url = service_url
        self.site_domain = site_domain
        self.site_name = site_name
        self.site_id = None
        self.client_id, self.tenant_id, self.client_secret, self.cache_token = self._prepare_outlook_reader_config()
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]

        self.cache = msal.SerializableTokenCache()
        self.app = None
        self.result = None
        self._drive_cache = {}
        self._load_cache()
        self._initialize_app()
        # self._authenticate()
        self._get_site_id()

    def _prepare_sharepoint_site_url(self):
        """ Prepare SharePoint site URL

        Returns:
            str: SharePoint site URL
        """
        if not re.match(r'^[\w\-\s]+$', self.site_name):
            raise ValueError(f"Invalid site name: {self.site_name}. Only letters, numbers, spaces, hyphens, and underscores are allowed.")
        site_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_domain}:/sites/{self.site_name}"
        return site_url

    def _get_public_service_data(self, password_name):
        """ Get password from public service

        Args:
            password_name(str): password name
        """
        data = {
            "query_type": 'get_password',
            "password_name": password_name,
            "username": self.public_service_user_name,
            "password": self.public_service_user_password,
        }
        res = requests.post(self.service_url, data=data, verify=self.verify_ssl)
        res_json = res.json()
        is_login = res_json['isLogin']
        is_auth = res_json['isAuth']
        is_valid = res_json['isValid']
        if is_login != 1 or is_auth != 1 or is_valid != 1:
            logging.error("You do not have permission to access this service or invalid username or password!")
            return None
        return res_json.get('passwordData', {}).get('password_value', '')

    def _update_public_service_data(self, password_name, password_value):
        """ Update password from public service

        Args:
            password_name(str): password name
            password_value(str): new password value
        """
        data = {
            "query_type": 'update_password',
            "password_name": password_name,
            'password_value': password_value,
            "username": self.public_service_user_name,
            "password": self.public_service_user_password,
        }
        res = requests.post(self.service_url, data=data, verify=self.verify_ssl)
        res_json = res.json()
        is_login = res_json['isLogin']
        is_auth = res_json['isAuth']
        is_valid = res_json['isValid']
        if is_login != 1 or is_auth != 1 or is_valid != 1:
            logging.error("Update password failed! You do not have permission to access this service or invalid username or password!")
        else:
            logging.info("Update password successfully!")

    def _prepare_outlook_reader_config(self):
        """ Prepare configuration for Outlook reader

        """
        client_id = self._get_public_service_data('SHAREPOINT_MANAGER_CLIENT_ID')
        tenant_id = self._get_public_service_data('SHAREPOINT_MANAGER_TENANT_ID')
        client_secret = self._get_public_service_data('SHAREPOINT_MANAGER_CLIENT_SECRET')
        cache_token = self._get_public_service_data(self.token_name)
        return client_id, tenant_id, client_secret, cache_token

    def _load_cache(self):
        """ Load token cache from public service

        """
        self.cache.deserialize(self.cache_token)

    def _initialize_app(self):
        """ Initialize MSAL ConfidentialClientApplication

        """
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
            token_cache=self.cache,
        )
        accounts = self.app.get_accounts()
        if accounts:
            logging.info(f"Found existing account: {accounts[0]['username']}")
            self.result = self.app.acquire_token_silent(self.scopes, account=accounts[0], force_refresh=True)
            if self.cache.has_state_changed:
                self._update_public_service_data(self.token_name, self.cache.serialize())
        else:
            self.result = None

    # def _authenticate(self):
    #     """ Authenticate and acquire token
    #
    #     """
    #     if not self.result:
    #         logging.info("No valid token in cache, need to log in via browser.")
    #         flow = self.app.initiate_auth_code_flow(scopes=self.scopes, redirect_uri="http://localhost:8090")
    #         print("Please open the following URL in your browser and log in:")
    #         print(flow["auth_uri"])
    #         auth_response_url = input("Enter the full redirect URL from your browser: ")
    #         from urllib.parse import urlparse, parse_qsl
    #         parsed = urlparse(auth_response_url)
    #         auth_response = dict(parse_qsl(parsed.query))
    #         self.result = self.app.acquire_token_by_auth_code_flow(flow, auth_response)
    #
    #     if self.cache.has_state_changed:
    #         self._update_public_service_data(self.token_name, self.cache.serialize())

    def _get_access_token(self):
        """ Get access token

        """
        # if "access_token" in self.result:
        #     return self.result["access_token"]
        # else:
        #     raise Exception("Failed to obtain access token.")
        accounts = self.app.get_accounts()
        if accounts:
            refreshed = self.app.acquire_token_silent(
                self.scopes,
                account=accounts[0],
                force_refresh=True
            )
            if refreshed:
                self.result = refreshed
                if self.cache.has_state_changed:
                    self._update_public_service_data(self.token_name, self.cache.serialize())

        return self.result["access_token"]

    def _get_headers(self):
        """ Prepare headers for requests"""
        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        return headers

    def _get_site_id(self):
        """ Get SharePoint site ID

        Returns:
            str: SharePoint site ID
        """
        headers = self._get_headers()

        sharepoint_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_domain}:/sites/{self.site_name}"
        response = requests.get(sharepoint_url, headers=headers)
        response.raise_for_status()
        site_info = response.json()
        self.site_id = site_info["id"]

    def _get_drive_id(self, drive_name: str | None = None):
        """ Get drive ID by drive name

        Args:
            drive_name(str): Document library name. e.g. 'Documents'

        """
        if not drive_name:
            drive_name = "Documents"

        # 优先从缓存取
        if drive_name in self._drive_cache:
            return self._drive_cache[drive_name]

        drive_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives"
        response = requests.get(drive_url, headers=self._get_headers())
        response.raise_for_status()

        drives = response.json().get("value", [])
        for drive in drives:
            self._drive_cache[drive["name"].lower()] = drive["id"]

        return self._drive_cache.get(drive_name.lower())

    def _get_item_id_by_path(self, folder_path: list[str], drive_name: str | None = None):
        """
        Traverse a folder path (as list) and return the final item_id.
        Example: ["Reports", "2025", "January"]

        Args:
            drive_name(str): Document library name. e.g. 'Documents'
            folder_path(list[str]): List of folder names representing the path. It could be folder items or folder + file items.
        """
        if drive_name is None:
            drive_name = "Documents"

        drive_id = self._get_drive_id(drive_name)
        if not drive_id:
            return None

        # 拼接成完整路径
        relative_path = "/".join(folder_path)
        item_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{drive_id}/root:/{relative_path}"

        response = requests.get(item_url, headers=self._get_headers())
        if response.status_code == 404:
            return None
        response.raise_for_status()

        return response.json()["id"]

    def _prepare_drive_id_item_id(self, folder_path: list[str], drive_name: str | None = None):
        """ Prepare drive_id and item_id for a given folder path.

        Args:
            drive_name(str): Document library name. e.g. 'Documents'
            folder_path(list[str]): List of folder names representing the path. It could be folder items or folder + file items.
        """
        has_drive = True
        has_item = True

        drive_id = self._get_drive_id(drive_name)
        if not drive_id:
            has_drive = False
            logging.error(f"Failed to get drive id for {drive_name}")

        if folder_path:
            item_id = self._get_item_id_by_path(folder_path, drive_name)
            if not item_id:
                has_item = False
                logging.error(f"Path '{'/'.join(folder_path)}' not found in drive '{drive_name}'")
        else:
            item_id = "root"

        return has_drive, has_item, drive_id, item_id

    def check_item_exists(self, item_path_list: list[str], drive_name: str | None = None) -> bool:
        """ Check if an item (file/folder) exists in SharePoint.

        Args:
            item_path_list(list[str]): List of folder names + filename, e.g. ["Reports","2025","budget.xlsx"]
            drive_name(str): Document library name. e.g. 'Documents'
        """
        if not item_path_list:
            logging.error(f"Please provide a valid item path list.")
            return False

        has_drive, has_item, _, _ = self._prepare_drive_id_item_id(item_path_list, drive_name)
        return has_drive and has_item

    def list_folder_items(self, folder_path: list[str], drive_name: str | None = None):
        """
        List items in a folder.

        Args:
            folder_path(list[str]): List of folder names representing the path.
            drive_name(str): Document library name. e.g. 'Documents'

        Returns:
            List[Dict]: A list of items with id, name, is_file, is_folder
        """
        has_drive, has_item, drive_id, item_id = self._prepare_drive_id_item_id(folder_path, drive_name)
        if has_drive and has_item:
            folder_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{drive_id}/items/{item_id}/children"
            response = requests.get(folder_url, headers=self._get_headers())
            response.raise_for_status()

            items_list = []
            for entry in response.json().get("value", []):
                items_list.append({
                    "id": entry["id"],
                    "name": entry["name"],
                    "is_file": "file" in entry,
                    "is_folder": "folder" in entry
                })
            return items_list
        else:
            return []

    def download_file_as_bytes(self, file_path: list[str], drive_name: str | None = None) -> BytesIO | None:
        """
        Download a file from SharePoint into memory as BytesIO.

        Args:
            file_path (list[str]): List of folder names + filename.
                                   Example: ["Reports", "2025", "budget.xlsx"]
            drive_name (str): Document library name. e.g. 'Documents'

        Returns:
            BytesIO | None: In-memory file object
        """
        has_drive, has_item, drive_id, item_id = self._prepare_drive_id_item_id(file_path, drive_name)
        if not has_drive or not has_item:
            return None

        file_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{drive_id}/items/{item_id}/content"
        response = requests.get(file_url, headers=self._get_headers(), stream=True)
        response.raise_for_status()

        file_obj = BytesIO(response.content)
        file_obj.seek(0)
        return file_obj

    @staticmethod
    def fetch_file(download_url: str) -> BytesIO:
        """ Helper function to fetch a file from a download URL into BytesIO.

        Args:
            download_url(str): The direct download URL of the file.

        Returns:

        """
        res = requests.get(download_url, stream=True)
        res.raise_for_status()
        file_obj = BytesIO(res.content)
        file_obj.seek(0)
        return file_obj

    def batch_download_files_as_bytes(self, file_paths_list: list[list[str]], drive_name: str | None = None) -> dict[str, BytesIO | None]:
        """
        Batch download multiple files into memory as BytesIO.
        Will automatically split into chunks of 20 requests.

        Args:
            file_paths_list: Example: [["Reports","2025","a.xlsx"], ["Reports","2025","b.xlsx"]]
            drive_name: Document library name. Default: 'Documents'

        Returns:
            dict: { "Reports/2025/a.xlsx": BytesIO(...) | None }
        """
        drive_id = self._get_drive_id(drive_name)
        if not drive_id:
            raise ValueError(f"Drive '{drive_name}' not found in site {self.site_id}")

        file_obj_dict: dict[str, BytesIO | None] = {}

        for batch_index in range(0, len(file_paths_list), BATCH_DOWNLOAD_LIMIT):
            chunk = file_paths_list[batch_index:batch_index + BATCH_DOWNLOAD_LIMIT]
            requests_body = []
            id_to_path_dict = {}
            for path_index, path in enumerate(chunk, start=1):
                relative_path = "/".join(path)
                requests_body.append({
                    "id": str(path_index),
                    "method": "GET",
                    "url": f"/sites/{self.site_id}/drives/{drive_id}/root:/{relative_path}"
                })
                id_to_path_dict[str(path_index)] = relative_path

            batch_url = "https://graph.microsoft.com/v1.0/$batch"
            response = requests.post(batch_url, headers=self._get_headers(), json={"requests": requests_body})
            response.raise_for_status()
            results = response.json().get("responses", [])

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {}
                for res in results:
                    path_str = id_to_path_dict.get(res["id"])
                    if res["status"] == 200 and "@microsoft.graph.downloadUrl" in res["body"]:
                        download_url = res["body"]["@microsoft.graph.downloadUrl"]
                        futures[path_str] = executor.submit(self.fetch_file, download_url)
                    else:
                        file_obj_dict[path_str] = None

                for path_str, fut in futures.items():
                    try:
                        file_obj_dict[path_str] = fut.result()
                    except Exception as e:
                        logging.error(f"Download failed for {path_str}: {e}")
                        file_obj_dict[path_str] = None

        return file_obj_dict

    def upload_file_by_bytes(self, file_obj: BytesIO, file_path_list: list[str], drive_name: str | None = None, chunk_size: int = UPLOAD_FILE_CHUNK_SIZE,
                             conflict_behavior: str = "replace"):
        """
        Upload a file to SharePoint using upload session (works for small and large files).

        Args:
            file_obj: BytesIO object of file content
            file_path_list: List of folder names + filename, e.g. ["Reports","2025","budget.xlsx"]
            drive_name: Document library name
            chunk_size: Size of each upload chunk in bytes (default: 5 MB)
            conflict_behavior: What to do if file already exists. One of ["replace", "fail", "rename"]

        Returns:
            (bool, dict | None): (is_uploaded_successfully, response_json)
        """
        is_uploaded_successfully = True
        drive_id = self._get_drive_id(drive_name)
        if not drive_id:
            raise ValueError(f"Drive '{drive_name}' not found in site {self.site_id}")

        relative_path = "/".join(file_path_list)

        session_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{drive_id}/root:/{relative_path}:/createUploadSession"
        session_res = requests.post(session_url, headers=self._get_headers(), json={"item": {"@microsoft.graph.conflictBehavior": conflict_behavior}})
        try:
            session_res.raise_for_status()
            upload_url = session_res.json()["uploadUrl"]

            put_res = None
            file_obj.seek(0)
            total_size = len(file_obj.getbuffer())
            start = 0
            while start < total_size:
                end = min(start + chunk_size, total_size) - 1
                file_obj.seek(start)
                chunk = file_obj.read(end - start + 1)

                headers = {
                    "Content-Length": str(end - start + 1),
                    "Content-Range": f"bytes {start}-{end}/{total_size}"
                }
                put_res = requests.put(upload_url, headers=headers, data=chunk)
                if put_res.status_code not in (200, 201, 202):
                    is_uploaded_successfully = False
                    logging.error(f"Upload failed with status {put_res.status_code}: {put_res.text}")
                    return is_uploaded_successfully, None

                start = end + 1

            return is_uploaded_successfully, put_res.json()
        except Exception as e:
            logging.error(f"Upload session creation failed: {e}")
            return False, None

    def copy_item(self, source_path_list: list[str], target_folder_path_list: list[str], drive_name: str | None = None, new_item_name: str | None = None) -> (bool, str):
        """
        Copy an item (file/folder) to another folder. If target file name exists, system will create new name automatically.

        Args:
            source_path_list: List path to the file/folder, e.g. ["Reports","2025","budget.xlsx"]
            target_folder_path_list: List path to the destination folder, e.g. ["Reports","Archive"]
            drive_name: Document library name
            new_item_name: Optional new name for the copied item

        Returns:
            (bool, str): (is_copied_successfully, monitor_url)
        """
        is_copied_successfully = True
        source_has_drive, source_has_item, drive_id, source_item_id = self._prepare_drive_id_item_id(source_path_list, drive_name)
        if not source_has_drive or not source_has_item:
            raise ValueError(f"Source path '{'/'.join(source_path_list)}' not found in drive '{drive_name}'")

        target_has_drive, target_has_item, _, target_item_id = self._prepare_drive_id_item_id(target_folder_path_list, drive_name)
        if not target_has_drive or not target_has_item:
            raise ValueError(f"Target path '{'/'.join(target_folder_path_list)}' not found in drive '{drive_name}'")

        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{drive_id}/items/{source_item_id}/copy"
        payload: dict[str, Any] = {"parentReference": {"driveId": drive_id, "id": target_item_id}}
        if new_item_name:
            payload["name"] = new_item_name

        response = requests.post(url, headers=self._get_headers(), json=payload)
        if response.status_code not in (200, 202):
            is_copied_successfully = False
            logging.error(f"Copy failed with status {response.status_code}: {response.text}")
            return is_copied_successfully, ''

        if response.status_code == 202:
            logging.info("Copy operation skipped because target file is already exist.")
            is_copied_successfully = False
        else:
            logging.info("Copy operation completed.")

        return is_copied_successfully, response.headers.get("Location")

    def move_item(self, source_path_list: list[str], target_folder_path_list: list[str], drive_name: str | None = None, new_item_name: str | None = None) -> (bool, dict):
        """
        Move (cut) an item (file/folder) to another folder.

        Args:
            source_path_list: List path to the file/folder, e.g. ["Reports","2025","budget.xlsx"]
            target_folder_path_list: List path to the destination folder, e.g. ["Reports","Archive"]
            drive_name: Document library name
            new_item_name: Optional new name

        Returns:
            (bool, dict): (is_moved_successfully, response_json)
        """
        is_moved_successfully = True
        source_has_drive, source_has_item, drive_id, source_item_id = self._prepare_drive_id_item_id(source_path_list, drive_name)
        if not source_has_drive or not source_has_item:
            raise ValueError(f"Source path '{'/'.join(source_path_list)}' not found in drive '{drive_name}'")

        target_has_drive, target_has_item, _, target_item_id = self._prepare_drive_id_item_id(target_folder_path_list, drive_name)
        if not target_has_drive or not target_has_item:
            raise ValueError(f"Target path '{'/'.join(target_folder_path_list)}' not found in drive '{drive_name}'")

        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{drive_id}/items/{source_item_id}"
        payload: dict[str, Any] = {"parentReference": {"driveId": drive_id, "id": target_item_id}}
        if new_item_name:
            payload["name"] = new_item_name

        response = requests.patch(url, headers=self._get_headers(), json=payload)
        if response.status_code == 409:
            is_moved_successfully = False
            logging.error(f"Move failed: Target item with the same name already exists.")
            return is_moved_successfully, {}
        else:
            response.raise_for_status()
            return is_moved_successfully, response.json()

    def get_excel_used_range(self, file_path_list: list[str], sheet_name: str, drive_name: str | None = None) -> dict:
        """
        Get the used range of a worksheet, including max row and column info.

        Args:
            file_path_list (list[str]): Path to the Excel file, e.g. ["Reports", "2025", "budget.xlsx"]
            sheet_name (str): Worksheet name, e.g. "Sheet1"
            drive_name (str | None): Document library name, default: 'Documents'

        Returns:
            dict: {
                "address": "Sheet1!A1:D20",
                "rowCount": 20,
                "columnCount": 4,
                "lastRow": 20,
                "lastColumn": "D"
            }
        """
        has_drive, has_item, drive_id, item_id = self._prepare_drive_id_item_id(file_path_list, drive_name)
        if not has_drive or not has_item:
            raise ValueError(f"File path '{'/'.join(file_path_list)}' not found in drive '{drive_name}'")

        excel_url = (
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/workbook/worksheets('{sheet_name}')/usedRange"
        )

        response = requests.get(excel_url, headers=self._get_headers())
        response.raise_for_status()
        data = response.json()

        # 提取行列数
        row_count = data.get("rowCount", 0)
        col_count = data.get("columnCount", 0)

        return {
            "address": data.get("address"),
            "rowCount": row_count,
            "columnCount": col_count,
            "lastRow": row_count,
            "lastColumn": get_column_letter(col_count) if col_count else None
        }

    def update_excel_values(self, file_path_list: list[str], sheet_name: str, range_address: str, values: list[list], drive_name: str | None = None) -> dict:
        """
        Update cell values in a worksheet.

        Args:
            file_path_list (list[str]): Path to the Excel file, e.g. ["Reports", "2025", "budget.xlsx"]
            sheet_name (str): Worksheet name, e.g. "Sheet1"
            range_address (str): Excel range, e.g. "A1" or "A1:C3"
            values (list[list]): 2D list of values, e.g. [["Name", "Amount"], ["Alice", 100]]
            drive_name (str | None): Document library name, default: 'Documents'

        Returns:
            dict: Graph API response with updated range info
        """
        has_drive, has_item, drive_id, item_id = self._prepare_drive_id_item_id(file_path_list, drive_name)
        if not has_drive or not has_item:
            raise ValueError(f"File path '{'/'.join(file_path_list)}' not found in drive '{drive_name}'")

        excel_url = (
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/workbook/worksheets('{sheet_name}')/range(address='{range_address}')"
        )

        body = {"values": values}
        response = requests.patch(excel_url, headers=self._get_headers(), json=body)
        response.raise_for_status()
        return response.json()
