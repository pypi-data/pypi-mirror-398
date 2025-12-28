import logging
import re
import msal
import base64
from io import BytesIO
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,  # 设置日志级别，INFO 以上都会显示
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class OutlookReaderManager:
    def __init__(self, public_service_user_name, public_service_user_password, token_name, service_url, verify_ssl=False):
        """ Initialize OutlookReaderManager parameters

        Args:
            public_service_user_name(str): Username for public service
            public_service_user_password(str): Password for public service
            token_name(str): Token name in public service
            service_url(str): Public service URL
            verify_ssl(bool|str): Whether to verify SSL certificates
        """
        self.public_service_user_name = public_service_user_name
        self.public_service_user_password = public_service_user_password
        self.token_name = token_name
        self.verify_ssl = verify_ssl
        self.service_url = service_url
        self.client_id, self.tenant_id, self.client_secret, self.cache_token = self._prepare_outlook_reader_config()
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]

        self.cache = msal.SerializableTokenCache()
        self.app = None
        self.result = None
        self._load_cache()
        self._initialize_app()
        # self._authenticate()

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
        client_id = self._get_public_service_data('OUTLOOK_READER_CLIENT_ID')
        tenant_id = self._get_public_service_data('OUTLOOK_READER_TENANT_ID')
        client_secret = self._get_public_service_data('OUTLOOK_READER_CLIENT_SECRET')
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
            logging.info(f"Found existing account in token cache: {accounts[0]['username']}")
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

    @staticmethod
    def _extract_text_with_links(html_content):
        """  Extract text with links from HTML content

        Args:
            html_content(str): HTML content

        """
        soup = BeautifulSoup(html_content, "html.parser")

        # 遍历所有 a 标签，把它替换成 "文字 (URL)"
        for a in soup.find_all("a"):
            text = a.get_text(strip=True)
            href = a.get("href", "")
            if href:
                a.replace_with(f"{text} ({href})")
            else:
                a.replace_with(text)

        # 输出带换行的纯文本
        return soup.get_text("\n")

    def _locate_target_mail_folder(self, mail_folder_name_list=None):
        """ Locate target mail folder by name list

        Args:
            mail_folder_name_list(list): List of folder names to locate

        Returns:
            str: Folder ID if found, else 'inbox'
        """
        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        current_mail_folder_url = "https://graph.microsoft.com/v1.0/me/mailFolders"
        current_folder_id = ''
        current_mail_message_url = ''

        if mail_folder_name_list is not None:
            for mail_folder_index, mail_folder_name in enumerate(mail_folder_name_list):
                if not re.match(r'^[\w\-\s]+$', mail_folder_name):
                    raise ValueError(f"Invalid folder name: {mail_folder_name}. Only letters, numbers, spaces, hyphens, and underscores are allowed.")
                else:
                    response = requests.get(current_mail_folder_url, headers=headers, verify=self.verify_ssl)
                    if response.status_code == 200:
                        folders = response.json().get("value", [])
                        for folder in folders:
                            if folder.get("displayName", "").lower() == mail_folder_name.lower():
                                logging.info(f"Located target mail folder: {folder.get('displayName')}")
                                current_folder_id = folder.get("id", '')
                                current_mail_folder_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{current_folder_id}/childFolders"
                    else:
                        raise Exception(f"Failed to retrieve mail folders for {mail_folder_name}, status code: {response.status_code}")

            if current_folder_id:
                current_mail_message_url = f'https://graph.microsoft.com/v1.0/me/mailFolders/{current_folder_id}/messages?'
        else:
            logging.info("No specific mail folder provided, defaulting to Inbox.")
            current_folder_id = 'inbox'
            current_mail_message_url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?"

        return current_folder_id, current_mail_message_url

    def search_emails_in_target_email_folder(self, search_query, mail_folder_name_list=None, download_attachments=False):
        """ Search emails in target email folder

        Args:
            search_query(str): Search query string, which is the query parameter after question mark in the URL
            mail_folder_name_list(list): List of folder names to locate
            download_attachments(bool): Whether to download attachments

        Returns:
            list: A list of dictionaries, each representing an email message.
                  Each dictionary contains the following keys:
                      - id (str): The unique ID of the email.
                      - subject (str): The subject line of the email.
                      - from (str): The sender's email address.
                      - received_date_time (str): The datetime when the email was received.
                      - body_preview (str): A short preview of the email body.
                      - body_content (str): The full email body (plain text or extracted text if HTML).
                      - attachments (list): A list of attachments, each being a dictionary with:
                          - file_name (str): The name of the attachment file.
                          - file_obj (BytesIO): The binary content of the file wrapped in a BytesIO object.
        """
        search_email_result = []

        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        current_folder_id, current_mail_message_url = self._locate_target_mail_folder(mail_folder_name_list)

        search_endpoint = f'{current_mail_message_url}{search_query}'

        response = requests.get(search_endpoint, headers=headers, verify=self.verify_ssl)
        if response.status_code == 200:
            messages = response.json().get("value", [])
            for message_index, message in enumerate(messages, start=1):
                message_id = message.get("id")
                message_dict = {
                    'id': message_id,
                    "subject": message.get("subject", ''),
                    "from": message.get("from", {}).get("emailAddress", {}).get("address", ''),
                    "received_date_time": message.get("receivedDateTime", ''),
                    "body_preview": message.get("bodyPreview", ''),
                    'attachments': []
                }

                body = message.get("body", {})
                content_type = body.get("contentType")
                content = body.get("content")

                if content_type == "html":
                    text_content = self._extract_text_with_links(content)
                else:
                    text_content = content
                    text_content = re.sub(r"(From:|Sent:|To:|Subject:)", r"\n\1", text_content)
                message_dict['body_content'] = text_content

                if download_attachments:

                    attachment_url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
                    att_resp = requests.get(attachment_url, headers=headers, verify=self.verify_ssl)

                    if att_resp.status_code == 200:
                        attachments = att_resp.json().get("value", [])
                        if attachments:
                            for attachment in attachments:
                                if attachment["@odata.type"] == "#microsoft.graph.fileAttachment":
                                    filename = attachment["name"]
                                    content_bytes = attachment["contentBytes"]
                                    file_content = BytesIO(base64.b64decode(content_bytes))
                                    file_content.seek(0)
                                    message_dict['attachments'].append({
                                        "file_name": filename,
                                        "file_obj": file_content
                                    })
                                else:
                                    logging.warning(f"Attachment {attachment['name']} is not a file (it may be an itemAttachment or referenceAttachment)")
                        else:
                            logging.warning("There are no attachments in current email!")
                    else:
                        logging.error("Failed to get attachments:", att_resp.status_code, att_resp.text)
                search_email_result.append(message_dict)
            return search_email_result
        else:
            raise Exception(f"Failed to search emails, status code: {response.status_code}")

    def move_emails_to_target_email_folder(self, message_id_list, mail_folder_name_list=None):
        """ Move emails to target email folder

        Args:
            message_id_list(list): List of email IDs to move
            mail_folder_name_list(list): List of folder names to locate
        """
        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        current_folder_id, current_mail_message_url = self._locate_target_mail_folder(mail_folder_name_list)

        for message_id in message_id_list:
            move_url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/move"
            data = {
                "destinationId": current_folder_id
            }
            response = requests.post(move_url, headers=headers, json=data, verify=self.verify_ssl)
            if response.status_code == 201:
                logging.info(f"Message ID {message_id} moved successfully to folder ID {current_folder_id}.")
            else:
                logging.error(f"Failed to move message ID {message_id}, status code: {response.status_code}, response: {response.text}")
