#!/usr/bin/env python3
"""
Reset Test Script
用於測試重置功能的腳本
"""

import os
import sys
import asyncio
from pathlib import Path

from botrun_flow_lang.langgraph_agents.agents.checkpointer.firestore_checkpointer import (
    AsyncFirestoreCheckpointer,
)

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def main():
    print("=== Reset Test Started ===")
    await AsyncFirestoreCheckpointer(
        env_name="botrun-flow-lang-elan-dev"
    ).adelete_thread("U3a24c9741d2bbe44285ded6761baf794")

    print("=== Reset Test Completed ===")


if __name__ == "__main__":
    asyncio.run(main())
