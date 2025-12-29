import os
import traceback
import inspect
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import sys
import logging

from google.cloud import logging as cloud_logging
from google.cloud.logging import Resource
from google.oauth2 import service_account


class BotrunLogger(logging.Logger):
    """Botrun 專用日誌系統，基於 Python 標準 logging 和 Google Cloud Logging

    提供結構化日誌記錄功能，支援多種日誌級別、自定義項目 ID 和服務帳戶認證。
    可根據環境變數配置日誌行為，支援在 Cloud Run 環境中自動獲取資源信息。
    """

    def __init__(
        self,
        name: str = "botrun",
        level: str = "INFO",
        log_name: str = "",
        resource_type: str = "cloud_run_revision",
        project_id: Optional[str] = None,
        service_account_file: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """初始化 BotrunLogger

        Args:
            name: logger 名稱
            level: 日誌級別
            log_name: 日誌名稱，用於在 Cloud Logging 中區分不同服務的日誌
            resource_type: Google Cloud 資源類型，通常為 cloud_run_revision 或 global
            project_id: 指定 GCP 項目 ID，如不指定則使用默認項目
            service_account_file: 服務帳戶密鑰文件路徑，如不指定則使用應用默認憑證
            session_id: 會話 ID
            user_id: 用戶 ID
        """
        # 初始化基礎 Logger
        level = os.getenv("BOTRUN_LOGGER_LEVEL", "INFO")
        super().__init__(name, getattr(logging, level.upper()))

        # 如果沒有 handler，加入一個基本的 console handler
        if not self.handlers:
            console_handler = logging.StreamHandler()
            # Use the custom fields passed in 'extra'
            formatter = logging.Formatter(
                "[%(levelname)s][%(caller_filename)s:%(caller_funcName)s:%(caller_lineno)d] %(message)s"
            )
            console_handler.setFormatter(formatter)
            self.addHandler(console_handler)

        # 從環境變數獲取配置
        self.log_payload = os.getenv("LOG_PAYLOAD", "true").lower() == "true"

        if not log_name:
            log_name = os.getenv("BOTRUN_LOG_NAME", "log-dev-botrun-ai")
        print(f"[BotrunLogger]log_name: {log_name}")
        # 如果未指定項目 ID，嘗試從環境變數獲取
        if not project_id:
            project_id = os.getenv("BOTRUN_LOG_PROJECT_ID", "scoop-386004")
        print(f"[BotrunLogger]project_id: {project_id}")

        # 如果未指定服務帳戶文件，嘗試從環境變數獲取
        if not service_account_file:
            service_account_file = os.getenv("BOTRUN_LOG_CREDENTIALS_PATH", "")
        print(f"[BotrunLogger]service_account_file: {service_account_file}")

        self.session_id = session_id
        self.user_id = user_id

        # 初始化 Cloud Logging 客戶端
        self.client = self._initialize_client(project_id, service_account_file)
        self.use_cloud_logging = self.client is not None
        if self.use_cloud_logging:
            self.cloud_logger = self.client.logger(log_name)
            self.project_id = self.client.project
        else:
            self.cloud_logger = None
            self.project_id = project_id or "unknown-project"

        self.resource_type = resource_type
        self.resource_labels = self._get_resource_labels()

        # 記錄初始化信息
        self.debug(
            "BotrunLogger 初始化完成",
            event="logger_init",
            log_name=log_name,
            resource_type=resource_type,
            project_id=self.project_id,
            cloud_logging_enabled=self.use_cloud_logging,
        )

    def _log(
        self,
        level: int,
        msg: Any,
        args: tuple,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
        **kwargs,
    ) -> None:
        """重寫 _log 方法以支援結構化日誌和 Cloud Logging

        這是 logging.Logger 的核心方法，所有日誌方法最終都會調用這個方法。
        """
        # --- Find the correct caller frame outside this logger class --- #
        f = inspect.currentframe()
        # Default stacklevel for logging methods is 1. We need to go up further.
        # Levels: _log -> std library caller (e.g., info) -> actual user call
        frames_to_go_up = stacklevel + 1
        for _ in range(frames_to_go_up):
            if f is None:
                break
            f = f.f_back

        if f:
            caller_file = Path(f.f_code.co_filename).name
            caller_func = f.f_code.co_name
            caller_line = f.f_lineno
            prefix = f"[{caller_file}:{caller_func}:{caller_line}] "
        else:
            caller_file = "unknown"
            caller_func = "unknown"
            caller_line = 0
            prefix = ""

        # --- Prepare data for Cloud Logging --- #
        log_data_for_cloud = {
            "message": f"{prefix}{msg % args if args else msg}",  # Format message for cloud
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv("ENV_NAME", "botrun-flow-lang-dev"),
            "application": "botrun_flow_lang",
            "file": caller_file,
            "function": caller_func,
            "line": caller_line,
            "session_id": self.session_id,
            "user_id": self.user_id,
        }

        # Handle exception info for Cloud Logging
        computed_exc_info = None
        if exc_info:
            if isinstance(exc_info, BaseException):
                computed_exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                computed_exc_info = sys.exc_info()

            if computed_exc_info and computed_exc_info[0] is not None:
                log_data_for_cloud["exception"] = {
                    "type": computed_exc_info[0].__name__,
                    "message": str(computed_exc_info[1]),
                    "traceback": "".join(
                        traceback.format_exception(*computed_exc_info)
                    ),
                }
        else:
            computed_exc_info = None  # Ensure it's None if exc_info was false

        # Add extra kwargs passed directly to the log call for Cloud Logging
        if kwargs:
            log_data_for_cloud.update(kwargs)

        # --- Prepare data for standard logging handlers (like console) --- #
        # Create the 'extra' dict to pass correct caller info to handlers
        handler_extra = extra or {}
        handler_extra["caller_filename"] = caller_file
        handler_extra["caller_funcName"] = caller_func
        handler_extra["caller_lineno"] = caller_line

        # --- Call parent _log for standard handlers --- #
        # Pass the original msg and args so Formatter works correctly
        # Pass the computed exception info
        # Pass the enriched 'extra' dictionary
        # Pass stack_info if provided
        # stacklevel=1 here tells the *parent* _log it doesn't need to look further up
        super()._log(
            level,
            msg,
            args,
            exc_info=computed_exc_info,
            extra=handler_extra,
            stack_info=stack_info,
            stacklevel=1,
        )

        # --- Send to Cloud Logging if enabled --- #
        if self.use_cloud_logging and self.isEnabledFor(level):
            try:
                severity = logging.getLevelName(level)
                self.cloud_logger.log_struct(
                    log_data_for_cloud,  # Use the prepared cloud data
                    severity=severity,
                    resource=Resource(
                        type=self.resource_type, labels=self.resource_labels
                    ),
                )
            except Exception as e:
                # Avoid Cloud Logging failure crashing the app
                # Log the failure using the standard handler

                traceback.print_exc()
                print(f"Cloud Logging failed: {e}")
                # self.handle(
                #     self.makeRecord(
                #         self.name,
                #         logging.ERROR,
                #         "(unknown file)",
                #         0,
                #         f"Cloud Logging failed: {e}",
                #         (),
                #         None,
                #         func="_log",
                #     )
                # )

    def _initialize_client(
        self, project_id: Optional[str], service_account_file: Optional[str]
    ) -> Optional[cloud_logging.Client]:
        """初始化 Cloud Logging 客戶端

        Args:
            project_id: GCP 項目 ID
            service_account_file: 服務帳戶密鑰文件路徑

        Returns:
            Optional[cloud_logging.Client]: 已配置的日誌客戶端，若初始化失敗則為 None
        """
        try:
            # 使用服務帳戶認證
            if service_account_file and os.path.exists(service_account_file):
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_file
                )
                return cloud_logging.Client(project=project_id, credentials=credentials)
            # 使用應用默認憑證
            return cloud_logging.Client(project=project_id)
        except Exception as e:
            # 如果初始化失敗，打印錯誤並回退到標準輸出
            print(f"⚠️ 無法初始化 Cloud Logging 客戶端: {str(e)}")
            print(f"將使用標準輸出記錄日誌。錯誤詳情: {traceback.format_exc()}")
            return None

    def _get_resource_labels(self) -> Dict[str, str]:
        """獲取 Cloud Run 資源標籤

        從環境變數中獲取 Cloud Run 相關信息，用於資源標籤

        Returns:
            Dict[str, str]: 資源標籤字典
        """
        return {}

    # 為了保持與原有代碼的相容性，保留這些方法，但現在它們直接調用父類的方法
    # These methods are now redundant because the base class methods will call our overridden _log method.
    # Remove debug, info, warning, error, critical methods
    # def debug(self, msg: str, *args, **kwargs) -> None:
    #     """記錄 DEBUG 級別的日誌"""
    #     super().debug(msg, *args, **kwargs)
    #
    # def info(self, msg: str, *args, **kwargs) -> None:
    #     """記錄 INFO 級別的日誌"""
    #     super().info(msg, *args, **kwargs)
    #
    # def warning(self, msg: str, *args, **kwargs) -> None:
    #     """記錄 WARNING 級別的日誌"""
    #     super().warning(msg, *args, **kwargs)
    #
    # def error(self, msg: str, *args, exc_info: bool = True, **kwargs) -> None:
    #     """記錄 ERROR 級別的日誌"""
    #     super().error(msg, *args, exc_info=exc_info, **kwargs)
    #
    # def critical(self, msg: str, *args, **kwargs) -> None:
    #     """記錄 CRITICAL 級別的日誌"""
    #     super().critical(msg, *args, **kwargs)


# --- Default Standard Logger --- #


def _create_default_logger() -> logging.Logger:
    """Creates a default standard Python logger that streams to console."""
    logger = logging.getLogger("botrun.default")
    logger.setLevel(logging.INFO)  # Set default level

    # Avoid adding duplicate handlers if this is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        # Use format similar to BotrunLogger's prefix
        formatter = logging.Formatter(
            "[%(levelname)s][%(filename)s:%(funcName)s:%(lineno)d] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# 建立一個預設的標準 logger 實例
# This logger only prints to console and does NOT send to Cloud Logging.
# Use BotrunLogger explicitly when Cloud Logging features are needed.
default_logger = _create_default_logger()

# 建立一個預設的 BotrunLogger 全域實例
# 大部分模組可以重用這個實例，避免重複初始化
_default_botrun_logger = None


def get_default_botrun_logger() -> BotrunLogger:
    """
    獲取預設的 BotrunLogger 實例，只會初始化一次

    Returns:
        BotrunLogger: 預設的 BotrunLogger 實例
    """
    global _default_botrun_logger
    if _default_botrun_logger is None:
        _default_botrun_logger = BotrunLogger()
    return _default_botrun_logger


def get_session_botrun_logger(
    session_id: str = None, user_id: str = None
) -> BotrunLogger:
    """
    獲取帶有 session 和 user 信息的 BotrunLogger 實例

    Args:
        session_id: 會話 ID
        user_id: 用戶 ID

    Returns:
        BotrunLogger: 帶有特定 session/user 信息的 BotrunLogger 實例
    """
    return BotrunLogger(session_id=session_id, user_id=user_id)
