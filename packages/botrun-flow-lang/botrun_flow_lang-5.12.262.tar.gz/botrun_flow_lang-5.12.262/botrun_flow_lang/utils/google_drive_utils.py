import io
import os
import re
import asyncio
import logging
import requests
import uuid
from typing import Optional, Tuple

import chardet
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.auth.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


load_dotenv()


def authenticate_google_services(service_account_file: str):
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )
    drive_service = build("drive", "v3", credentials=credentials)
    docs_service = build("docs", "v1", credentials=credentials)
    return drive_service, docs_service


# def service_account_authentication(service_name, version, scopes):
#     service_account_file: str = os.getenv(
#         "GOOGLE_APPLICATION_CREDENTIALS", "./keys/google_service_account_key.json"
#     )
#     credentials: Credentials = service_account.Credentials.from_service_account_file(
#         service_account_file, scopes=scopes
#     )
#     return build(service_name, version, credentials=credentials)


def get_google_doc_content_with_service(
    file_id: str, mime_type, service, with_decode=True
):
    request = None
    if mime_type == "application/vnd.google-apps.document":
        request = service.files().export_media(fileId=file_id, mimeType="text/plain")
    elif mime_type == "application/octet-stream":
        request = service.files().get_media(fileId=file_id)
    elif (
        mime_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        request = service.files().get_media(fileId=file_id)
    else:
        request = service.files().get_media(fileId=file_id)

    if request is None:
        return None

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)

    if with_decode:
        raw_content = fh.getvalue()
        detected_encoding = chardet.detect(raw_content)
        content = raw_content.decode(detected_encoding["encoding"])
        if content.startswith("\ufeff"):
            content = content[1:]
        content = content.replace("\r\n", "\n")
        return content
    content = fh.getvalue()
    content = content.replace("\r\n", "\n")
    return content


def get_google_doc_mime_type(file_id: str, drive_service) -> str:
    """
    取得指定 Google 文件的 MIME 類型

    Args:
        file_id (str): Google 文件的 ID

    Returns:
        str: 文件的 MIME 類型，例如 'application/vnd.google-apps.document'

    Raises:
        HttpError: 當無法取得檔案資訊時拋出
    """
    # scopes = ['https://www.googleapis.com/auth/drive']
    try:
        # service = service_account_authentication(
        #     service_name="drive",
        #     version="v3",
        #     scopes=scopes
        # )

        # 取得檔案的中繼資料
        file_metadata = (
            drive_service.files().get(fileId=file_id, fields="mimeType").execute()
        )

        return file_metadata.get("mimeType", "")
    except HttpError as error:
        print(f"An error occurred: {error}")
        raise


def get_sheets_service(service_account_file: str):
    """
    取得 Google Sheets 服務物件

    Args:
        service_account_file (str): Google 服務帳戶金鑰檔案路徑

    Returns:
        googleapiclient.discovery.Resource: Google Sheets 服務物件
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )

        return build("sheets", "v4", credentials=credentials)

    except Exception as e:
        import logging

        logging.error(f"[Google Sheets] 建立服務物件失敗: {e}")
        raise


def create_sheet_if_not_exists(
    service_account_file: str,
    spreadsheet_id: str,
    sheet_name: str,
    headers: list = None,
):
    """
    檢查工作表是否存在，不存在則建立

    Args:
        service_account_file (str): Google 服務帳戶金鑰檔案路徑
        spreadsheet_id (str): Google Sheets 的 ID
        sheet_name (str): 工作表名稱
        headers (list): 可選，要加入的標題列

    Returns:
        bool: 成功返回 True，失敗返回 False
    """
    try:
        service = get_sheets_service(service_account_file)
        sheet = service.spreadsheets()

        # 檢查工作表是否存在
        spreadsheet = sheet.get(spreadsheetId=spreadsheet_id).execute()
        worksheet_names = [ws["properties"]["title"] for ws in spreadsheet["sheets"]]

        if sheet_name not in worksheet_names:
            # 建立新工作表
            requests = [{"addSheet": {"properties": {"title": sheet_name}}}]
            sheet.batchUpdate(
                spreadsheetId=spreadsheet_id, body={"requests": requests}
            ).execute()

            # 如果提供了標題列，則加入
            if headers:
                sheet.values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"{sheet_name}!1:1",
                    valueInputOption="RAW",
                    body={"values": [headers]},
                ).execute()

            return True

        return True  # 工作表已存在

    except Exception as e:
        import logging

        logging.error(f"[Google Sheets] 建立工作表失敗: {e}")
        return False


def get_sheet_content(service_account_file: str, spreadsheet_id: str, sheet_name: str):
    """
    讀取指定 Google Sheet 的內容，回傳 dict（key 為欄位名稱，value 為 list）。

    Args:
        service_account_file (str): Google 服務帳戶金鑰檔案路徑
        spreadsheet_id (str): Google Sheets 的 ID
        sheet_name (str): 工作表名稱

    Returns:
        dict: key 為欄位名稱，value 為 list

    Raises:
        Exception: 讀取失敗時拋出
    """
    try:
        service = get_sheets_service(service_account_file)
        range_name = f"{sheet_name}"
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        values = result.get("values", [])
        if not values:
            return {}
        header, *rows = values
        columns = {col: [] for col in header}
        for row in rows:
            for idx, col in enumerate(header):
                columns[col].append(row[idx] if idx < len(row) else None)
        return columns
    except Exception as e:
        raise Exception(f"讀取 Google Sheet 內容失敗: {e}")


def append_data_to_gsheet(
    service_account_file: str,
    spreadsheet_id: str,
    sheet_name: str,
    data_dict: dict,
    sort_order: str = "new_to_old",
):
    """
    插入資料到 Google Sheets，支援新到舊和舊到新兩種排序方式

    Args:
        service_account_file (str): Google 服務帳戶金鑰檔案路徑
        spreadsheet_id (str): Google Sheets 的 ID
        sheet_name (str): 工作表名稱
        data_dict (dict): 要插入的資料，key 為欄位名稱，value 為資料
        sort_order (str): 排序方式，"new_to_old" (預設) 或 "old_to_new"

    Returns:
        dict: API 回應結果

    Raises:
        Exception: 當操作失敗時拋出例外
    """
    try:
        service = get_sheets_service(service_account_file)
        sheet = service.spreadsheets()

        # 讀取第一行標題列
        header_range = f"{sheet_name}!1:1"
        result = (
            sheet.values()
            .get(spreadsheetId=spreadsheet_id, range=header_range)
            .execute()
        )

        headers = result.get("values", [[]])[0]
        if not headers:
            raise Exception(f"工作表 {sheet_name} 沒有標題列")

        # 根據標題列建立資料陣列
        row_data = []
        for header in headers:
            row_data.append(data_dict.get(header, ""))

        if sort_order == "new_to_old":
            # 新到舊：插入到第2行
            # 取得工作表資訊以獲得 sheetId
            spreadsheet = sheet.get(spreadsheetId=spreadsheet_id).execute()
            sheet_id = None
            for ws in spreadsheet["sheets"]:
                if ws["properties"]["title"] == sheet_name:
                    sheet_id = ws["properties"]["sheetId"]
                    break

            if sheet_id is None:
                raise Exception(f"找不到工作表: {sheet_name}")

            # 先插入一個空行在第2行
            insert_request = {
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": 1,  # 第2行（0-based索引）
                        "endIndex": 2,
                    },
                    "inheritFromBefore": False,
                }
            }

            # 執行插入空行操作
            sheet.batchUpdate(
                spreadsheetId=spreadsheet_id, body={"requests": [insert_request]}
            ).execute()

            # 然後將資料寫入第2行
            range_name = f"{sheet_name}!2:2"
            result = (
                sheet.values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body={"values": [row_data]},
                )
                .execute()
            )

        elif sort_order == "old_to_new":
            # 舊到新：附加到最後一行
            range_name = f"{sheet_name}!A:A"  # 使用 A:A 讓 Google Sheets 自動定位到最後
            result = (
                sheet.values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    insertDataOption="INSERT_ROWS",
                    body={"values": [row_data]},
                )
                .execute()
            )

        else:
            raise ValueError(
                f"不支援的排序方式: {sort_order}，請使用 'new_to_old' 或 'old_to_new'"
            )

        return result

    except Exception as e:
        import logging

        logging.error(f"[Google Sheets] 插入資料失敗 (排序方式: {sort_order}): {e}")
        raise


def extract_google_doc_id_from_link(google_doc_link: str) -> Optional[str]:
    """
    Extract Google Doc ID from various Google Doc URL formats.

    Args:
        google_doc_link: Google Doc URL in various formats

    Returns:
        Google Doc ID if found, None otherwise
    """
    if not google_doc_link:
        return None

    # Common patterns for Google Doc URLs
    patterns = [
        r"/document/d/([a-zA-Z0-9-_]+)",
        r"id=([a-zA-Z0-9-_]+)",
        r"/file/d/([a-zA-Z0-9-_]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, google_doc_link)
        if match:
            return match.group(1)

    # If it's already just an ID (alphanumeric string)
    if re.match(r"^[a-zA-Z0-9-_]+$", google_doc_link.strip()):
        return google_doc_link.strip()

    return None


async def fetch_google_doc_content(doc_link: str) -> Optional[str]:
    """
    Fetch content from Google Doc using service account credentials.

    Args:
        doc_link: Google Doc link or ID

    Returns:
        Document content as plain text, or None if failed
    """
    try:
        # Check for required environment variables
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_FOR_BOTRUN_DOC")
        if not credentials_path:
            logging.error(
                "GOOGLE_APPLICATION_CREDENTIALS_FOR_BOTRUN_DOC environment variable not set"
            )
            return None

        if not os.path.exists(credentials_path):
            logging.error(
                f"Google service account credentials file not found: {credentials_path}"
            )
            return None

        # Extract document ID from the link
        doc_id = extract_google_doc_id_from_link(doc_link)
        if not doc_id:
            logging.error(f"Unable to extract Google Doc ID from link: {doc_link}")
            return None

        # Run the Google API calls in an executor to avoid blocking
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None, fetch_google_doc_content_sync, credentials_path, doc_id
        )

        return content

    except Exception as e:
        logging.error(f"Error fetching Google Doc content from {doc_link}: {e}")
        return None


def fetch_google_doc_content_sync(credentials_path: str, doc_id: str) -> Optional[str]:
    """
    Synchronous helper method to fetch Google Doc content.
    """
    try:
        # Authenticate with Google services
        drive_service, docs_service = authenticate_google_services(credentials_path)

        # Get document MIME type
        mime_type = get_google_doc_mime_type(doc_id, drive_service)

        # Fetch document content
        content = get_google_doc_content_with_service(
            doc_id, mime_type, drive_service, with_decode=True
        )

        if content and isinstance(content, str):
            # Clean up the content
            content = content.strip()
            if content:
                logging.info(
                    f"Successfully fetched Google Doc content (length: {len(content)})"
                )
                return content

        logging.warning(f"Google Doc {doc_id} appears to be empty")
        return None

    except Exception as e:
        logging.error(f"Error in sync Google Doc fetch for {doc_id}: {e}")
        return None


async def get_webhook_base_url() -> Optional[str]:
    """
    Get the webhook base URL from the botrun info API.

    Returns:
        The botrun_flow_lang_url from the API response, or None if failed
    """
    try:
        botrun_back_api_base = os.getenv("BOTRUN_BACK_API_BASE")
        if not botrun_back_api_base:
            logging.error("BOTRUN_BACK_API_BASE environment variable not set")
            return None

        info_url = f"{botrun_back_api_base}/botrun/info"

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, requests.get, info_url)

        if response.status_code == 200:
            data = response.json()
            botrun_flow_lang_url = data.get("botrun_flow_lang_url")
            if botrun_flow_lang_url:
                logging.info(f"Retrieved webhook base URL: {botrun_flow_lang_url}")
                return botrun_flow_lang_url
            else:
                logging.error("botrun_flow_lang_url not found in API response")
                return None
        else:
            logging.error(f"Failed to get botrun info: HTTP {response.status_code}")
            return None

    except Exception as e:
        logging.error(f"Error getting webhook base URL: {e}")
        return None


async def register_google_drive_webhook(
    doc_link: str, hatch_id: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Register a webhook with Google Drive for a specific document.

    Args:
        doc_link: Google Doc link or ID
        hatch_id: The hatch ID to associate with this webhook

    Returns:
        Tuple of (success, channel_id, resource_id)
    """
    try:
        # Get credentials path
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_FOR_BOTRUN_DOC")
        if not credentials_path:
            logging.error("GOOGLE_APPLICATION_CREDENTIALS_FOR_BOTRUN_DOC not set")
            return False, None, None

        if not os.path.exists(credentials_path):
            logging.error(f"Credentials file not found: {credentials_path}")
            return False, None, None

        # Extract document ID
        doc_id = extract_google_doc_id_from_link(doc_link)
        if not doc_id:
            logging.error(f"Unable to extract Google Doc ID from: {doc_link}")
            return False, None, None

        # Get webhook base URL
        base_url = await get_webhook_base_url()
        if not base_url:
            return False, None, None

        # Construct webhook URL
        webhook_url = f"{base_url}/api/hatch/webhook/google-drive"

        # Run webhook registration in executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            register_google_drive_webhook_sync,
            credentials_path,
            doc_id,
            webhook_url,
            hatch_id,
        )

        return result

    except Exception as e:
        logging.error(f"Error registering Google Drive webhook: {e}")
        return False, None, None


def register_google_drive_webhook_sync(
    credentials_path: str, doc_id: str, webhook_url: str, hatch_id: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Synchronous helper to register Google Drive webhook.
    """
    try:
        # Authenticate with Google Drive
        drive_service, _ = authenticate_google_services(credentials_path)

        # Generate unique channel ID
        channel_id = f"hatch-{hatch_id}-{uuid.uuid4()}"

        # Prepare webhook registration request
        body = {
            "id": channel_id,
            "type": "web_hook",
            "address": webhook_url,
            "token": hatch_id,  # Use hatch_id as token for identification
        }

        # Register the webhook
        response = drive_service.files().watch(fileId=doc_id, body=body).execute()

        channel_id = response.get("id")
        resource_id = response.get("resourceId")

        logging.info(
            f"Successfully registered webhook for doc {doc_id}, channel: {channel_id}"
        )
        return True, channel_id, resource_id

    except HttpError as e:
        logging.error(f"Google API error registering webhook: {e}")
        return False, None, None
    except Exception as e:
        logging.error(f"Error in sync webhook registration: {e}")
        return False, None, None


async def unregister_google_drive_webhook(channel_id: str, resource_id: str) -> bool:
    """
    Unregister a Google Drive webhook.

    Args:
        channel_id: The channel ID to stop
        resource_id: The resource ID associated with the channel

    Returns:
        True if successful, False otherwise
    """
    try:
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_FOR_BOTRUN_DOC")
        if not credentials_path:
            logging.error("GOOGLE_APPLICATION_CREDENTIALS_FOR_BOTRUN_DOC not set")
            return False

        if not os.path.exists(credentials_path):
            logging.error(f"Credentials file not found: {credentials_path}")
            return False

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            unregister_google_drive_webhook_sync,
            credentials_path,
            channel_id,
            resource_id,
        )

        return result

    except Exception as e:
        logging.error(f"Error unregistering Google Drive webhook: {e}")
        return False


def unregister_google_drive_webhook_sync(
    credentials_path: str, channel_id: str, resource_id: str
) -> bool:
    """
    Synchronous helper to unregister Google Drive webhook.
    """
    try:
        # Authenticate with Google Drive
        drive_service, _ = authenticate_google_services(credentials_path)

        # Prepare stop request
        body = {"id": channel_id, "resourceId": resource_id}

        # Stop the webhook
        drive_service.channels().stop(body=body).execute()

        logging.info(f"Successfully unregistered webhook channel: {channel_id}")
        return True

    except HttpError as e:
        logging.error(f"Google API error unregistering webhook: {e}")
        return False
    except Exception as e:
        logging.error(f"Error in sync webhook unregistration: {e}")
        return False
