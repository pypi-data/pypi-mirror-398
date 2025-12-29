#!/bin/bash

# 簡易的 shell script：將 temp_txt.md 中的 \n 轉換為真的斷行，輸出到 temp_txt2.md

INPUT_FILE="specs/gov-search/temp_txt.md"
OUTPUT_FILE="specs/gov-search/temp_txt2.md"

echo "開始處理 ${INPUT_FILE}..."

# 檢查輸入檔案是否存在
if [ ! -f "${INPUT_FILE}" ]; then
    echo "錯誤: 檔案 ${INPUT_FILE} 不存在"
    exit 1
fi

# 將 \n 轉換為真的斷行並輸出到新檔案
sed 's/\\n/\n/g' "${INPUT_FILE}" > "${OUTPUT_FILE}"

echo "處理完成！"
echo "輸入檔案: ${INPUT_FILE}"
echo "輸出檔案: ${OUTPUT_FILE}"
echo "檔案大小對比:"
echo "  原檔案: $(wc -c < "${INPUT_FILE}") bytes"
echo "  新檔案: $(wc -c < "${OUTPUT_FILE}") bytes"
echo "  行數變化: $(wc -l < "${INPUT_FILE}") -> $(wc -l < "${OUTPUT_FILE}") 行"