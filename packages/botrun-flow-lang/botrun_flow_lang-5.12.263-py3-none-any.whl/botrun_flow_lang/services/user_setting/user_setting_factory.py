import os
from botrun_flow_lang.services.user_setting.user_setting_fs_store import (
    UserSettingFsStore,
)


def user_setting_store_factory():
    env_name = os.getenv("ENV_NAME", "dev")
    return UserSettingFsStore(env_name)
