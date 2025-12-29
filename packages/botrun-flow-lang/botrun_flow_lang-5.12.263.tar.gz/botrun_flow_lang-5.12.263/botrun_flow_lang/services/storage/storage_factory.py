import os
from dotenv import load_dotenv

from botrun_flow_lang.services.storage.storage_cs_store import StorageCsStore
from botrun_flow_lang.services.storage.storage_store import StorageStore

load_dotenv()


def storage_store_factory() -> StorageStore:
    env_name = os.getenv("HATCH_ENV_NAME", "botrun-hatch-dev")
    return StorageCsStore(env_name)
