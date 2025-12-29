import os
from dotenv import load_dotenv

from botrun_flow_lang.services.hatch.hatch_fs_store import HatchFsStore

load_dotenv()


def hatch_store_factory() -> HatchFsStore:
    env_name = os.getenv("HATCH_ENV_NAME", "botrun-hatch-dev")
    return HatchFsStore(env_name)
