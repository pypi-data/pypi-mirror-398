#!/bin/bash
set -ex

# 激活虛擬環境
source .venv/bin/activate

# 生成文檔
python botrun_flow_lang/tools/generate_docs.py

echo "Documentation generated successfully!" 