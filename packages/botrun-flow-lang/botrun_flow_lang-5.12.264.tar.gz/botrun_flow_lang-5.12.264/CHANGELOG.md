## [5.12.264]
- 修正 botrun_flow_lang/langgraph_agents/agents/langgraph_react_agent.py
  - from langchain.tools import StructuredTool 改成 from langchain_core.tools import StructuredTool

## [5.12.263]
- 優化 `get_hatches` 向下相容機制：
  - 使用 Firestore batch write 批量更新缺少 `updated_at` 的記錄（每批最多 500 個）
  - 解決 Firestore 無法直接篩選"字段不存在"的架構限制
  - 自動為舊記錄補充 `updated_at` 時間戳，確保所有 hatch 都能被正確查詢和排序
  - 首次查詢時自動遷移，後續查詢效能正常

## [5.12.262]
- 更新 requirement.txt，支援新版 botrun_hatch

## [5.12.261]
- Hatch 模型新增 `updated_at` 欄位（UTC ISO format），記錄最後更新時間
- `set_hatch` 方法在每次保存時自動更新 `updated_at` 時間戳
- hatch api `/hatches` 新增排序功能：
  - 新增 `sort_by` 查詢參數：指定排序欄位（預設：`updated_at`）
  - 新增 `order` 查詢參數：排序方向 `asc` 或 `desc`（預設：`desc`）
  - 預設排序：按修改日期降序（最新 → 最舊）
  - 目前支援排序欄位：`name`、`updated_at`（需搭配對應的 Firestore 索引）
  - 加入欄位白名單驗證，防止傳入不支援的欄位導致 Firestore 錯誤
- 新增 Firestore 複合索引：`user_id` (ascending) + `updated_at` (descending)
- 向下相容：現有 hatch 記錄的 `updated_at` 預設為空字串，排在最後

## [5.12.172]
- (seba) Dockerfile CMD 的部份改成可以用環境變數調整 worker 數量的設定方式

## [5.12.171]
- pdf mcp 工具支援處理超過 50MB 的 pdf 檔案

## [5.12.31]
- line bot api 暫時移除按讚反讚功能

## [5.11.282]
- fastapi 新增20 workers

## [5.11.281]
### Updated
- 支援台德 gpt-oss-120b 做為 react agent
  - 要支援的話，需要新增環境變數配置：
    - `TAIDE_API_KEY`
    - `TAIDE_BASE_URL`

## [5.11.41]
### Added
- LINE Bot Token 使用量記錄到 BigQuery 功能
  - 新增環境變數配置：
    - `BIGQUERY_TOKEN_LOG_API_URL`: BigQuery logging API URL
    - `BIGQUERY_TOKEN_LOG_ENABLED`: 是否啟用 token logging（預設為 true）
    - `SUBSIDY_LINE_BOT_MODEL_NAME`: 模型名稱（預設為 gemini-2.0-flash-thinking-exp）

## [5.11.11]
### Added
- DALL-E 圖片永久化儲存功能 [參考 specs/gen-img/design.md]
  - Storage API 新增 `/api/img-files/{user_id}` endpoint，支援圖片永久儲存到 GCS
  - 新增 `_upload_img_file_internal` 內部函數處理圖片上傳
  - local_files.py 新增 `download_image_from_url` 函數從 URL 下載圖片到記憶體
  - local_files.py 新增 `upload_image_and_get_public_url` 函數處理圖片下載與上傳流程
  - MCP generate_image 工具現在會將 DALL-E 生成的圖片自動上傳到 GCS，回傳永久 URL
  - 圖片儲存路徑：`img/{user_id}/dalle_{timestamp}_{random_id}.png`
  - 支援 fallback 機制：上傳失敗時回傳臨時 URL（1小時有效）

### Updated
- GCS bucket lifecycle rules：將 tmp/ 目錄檔案的自動刪除期限從 7 天延長至 365 天（1年）
- local_files.py 重新命名 `_perform_upload` → `_perform_tmp_file_upload`，明確表示暫存檔案上傳

## [5.10.291]
### Updated
- line bot api ，呼叫 cbh 做的 api

### Bug fix
- 修正， scrape mcp tool 回傳型態要是 dict，不能是 str

## [5.10.282]
### Added
- 新增支援 vertex-ai/ 開頭類型的模型，指定使用 vertex-ai 提供的模型，模型的名稱需依照以下規則命名
  vertex-ai/<region>/<model_name>
  相關模型資訊請參考 https://cloud.google.com/vertex-ai/generative-ai/docs/models?hl=zh-tw

## [5.10.232]
### Updaeted
- line bot 加 debug log

## [5.10.231]
### Updaeted
- gemini_subsidy_agent_graph 調整參數

## [5.10.221]
### Added
- 加入 gemini_subsidy_agent_graph，可透過 langgraph api 呼叫

## [5.10.141]
### Updated
- 調整 ChatAnthropicVertex 的使用方式，加入 project 參數

## [5.10.131]
### Updated
- gemini output max_tokens 設成 32000

## [5.10.82]
### Updated
- claude 原本使用 4 的模型都改成 4.5
- botrun-hatch 升級

## [5.10.32]
### Updated
- 修正 default_mcp 要回傳給使用者 URL 的 prompt，拿掉負面表述，加入 one shot
- claude openrouter 預設模型改為 anthropic/claude-sonnet-4.5

## [5.9.301]
### Updated
- 修正 default_mcp 要回傳給使用者 URL 的 prompt，讓語氣更明確，並直接提供 markdown 格式

## [5.9.251]
### Updated
- 產生美波 url 的時候加入 hideBotrunHatch=true 以及 hideUserInfo=true 參數，讓美波前端隱藏波孵及使用者資訊按鈕

## [5.9.151]
### Updated
- 更新 TAIWAN_SUBSIDY_SUPERVISOR_PROMPT 題詞

## [5.9.112]
### Updated
- 產生美波 url 的時候加入 external=true 參數，讓美波前端知道是外部使用者

## [5.9.111]
### Added
- 串接美波 line 認證 API 取得美波連結，帶入 line 提問，進入美波後會觸發自動發送提問機制
### Updated
- 更新 TAIWAN_SUBSIDY_SUPERVISOR_PROMPT 題詞

## [5.8.291]
### Updated
- version api 加入 log

## [5.8.222]
### BugFix
- 修正 version api 讀不到

## [5.8.221]
### Updated
- `create_html_page` 加回各框架的 cdn 網址
- default_mcp 加上，如果有 URL，要回傳給使用者的 prompt

## [5.8.212]
### Updated
- `TaiwanSubsidyAgentGraph`預設模型改回使用用 gemini-2.5-pro，步驟中間多加了說明

## [5.8.211]
### Updated
- `TaiwanSubsidyAgentGraph`預設模型用 gemini-2.5-flash，只有計算保留 gemini-2.5-pro

## [5.8.202]
### Updated
- `calculation_analysis` 變成 ainvoke

## [5.8.201]
### Updated
- `TaiwanSubsidyAgentGraph` 的 `calculation_analysis`, `extract_documents` 的 LLM不要 stream到前台

## [5.8.192]
### Updated
- `TaiwanSubsidyAgentGraph` get_content 只取最後一個 ai message

## [5.8.191]
### Added
- `langgraph_api` 可以執行 `TaiwanSubsidyAgentGraph`

## [5.8.182]
### Updated
- mcp 套件 還原到 1.10.1，不然 streamable http 會有問題

## [5.8.181]
### Updated
- mcp 套件 升級

## [5.8.151]
### Updated
- 更新 套件
- 加入 generate_tmp_text_file tool
- 加入 TaiwanSubsidyAgentGraph
- `langgraph_api` 加入 `/list`, `/schema`

## [5.8.142]
### Updated
- 沒改到 Dockerfile >.<

## [5.8.141]
### Updated
- 移除 playwright 的安裝，現在很少用到，而且打包時會出現 font 的錯誤
```
E: Package 'ttf-unifont' has no installation candidate
E: Package 'ttf-ubuntu-font-family' has no installation candidate
Failed to install browsers
Error: Installation process exited with code: 100
npm notice
npm notice New major version of npm available! 10.9.3 -> 11.5.2
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.5.2
npm notice To update run: npm install -g npm@11.5.2
npm notice
The command '/bin/sh -c npx playwright install --with-deps chrome' returned a non-zero code: 1
ERROR
ERROR: build step 0 "gcr.io/cloud-builders/docker" failed: step exited with non-zero status: 1
```

## [5.8.51]
### Updated
- 更新 pdfminer-six = "20250506"

## [5.7.131]
### Added
- 加入 gov_researcher_graph v1

## [5.7.81]
### Refactored
- 🔧 重構 HTML 檔案上傳機制：消除 HTTP 自我依賴問題 [GitHub Issue #50](https://github.com/sebastian-hsu/botrun_flow_lang/issues/50)
  - 在 `storage_api.py` 中新增 `_upload_html_file_internal()` 內部函數，提取核心上傳邏輯
  - 重構 `local_files.py` 中的 `_perform_html_upload()` 函數，使用直接函數調用取代 HTTP 請求
  - 將相關函數轉為 async/await 模式，避免事件循環衝突
  - 更新 MCP 工具函數使用 `await` 調用：`create_html_page`、`create_plotly_chart`、`create_mermaid_diagram`
  - 改善系統穩定性：消除 Cloud Run 容器自我依賴導致的死鎖風險
  - 提升效能：移除 HTTP 開銷，減少資源使用

### Updated
- 📝 改善 MCP 工具文檔：為 7 個 MCP 工具函數的 docstring 添加必要參數標註
  - 明確標註 `botrun_flow_lang_url` 和 `user_id` 為 REQUIRED 參數
  - 說明 LLM 可從 system prompt 中取得這些參數值
  - 涵蓋函數：`chat_with_pdf`、`chat_with_imgs`、`generate_image`、`generate_tmp_public_url`、`create_html_page`、`create_plotly_chart`、`create_mermaid_diagram`

## [5.7.51]
### Added
- 將原本工具，改成 mcp，透過 mcp來提供 service [GitHub Issue #49](https://github.com/sebastian-hsu/botrun_flow_lang/issues/49)
  - 將所有 10 個本地工具遷移至 MCP 服務器
  - 建立 `botrun_flow_lang/mcp_server/default_mcp.py` 作為所有工具的統一管理入口
  - 實現 FastAPI 與 MCP 的無縫整合，提供 streamable HTTP 服務於 `/mcp/default`

## [5.7.32]
### Updated
- `storage_cs_store.py` 改善 bucket lifecycle rules 管理機制：
  - 修改 `create_bucket` 方法，確保 lifecycle rules 在 bucket 創建或更新時正確設定
  - 新增 lifecycle rules 檢查邏輯，只有在規則不同時才進行更新
  - 改善日誌記錄，提供更詳細的 bucket 創建和更新狀態信息
  - 優化錯誤處理，提供更準確的錯誤描述

## [5.7.31]
### Updated
- `storage_cs_store.py` 加上 botrun logger

## [5.7.11]
### Updated
- /api/tmp-files/, /html-files 不需要確認認證

## [5.6.304]
### Updated
- 🔄 重構 LangGraph React Agent 快取系統：從執行緒快取轉換為 botrun_id 快取 [GitHub Issue #43](https://github.com/sebastian-hsu/botrun_flow_lang/issues/43)
  - 建立新的 `LangGraphBotrunCache` 模組於 `botrun_flow_lang/langgraph_agents/cache/langgraph_botrun_cache.py`
  - 實作 botrun_id 為主鍵的快取機制，支援參數驗證與自動快取失效
  - 移除 `langgraph_react_agent.py` 中的舊快取邏輯 (`_graph_cache`, `get_cached_graph`, `cache_graph`)
  - 在 `langgraph_api.py` 新增 `get_cached_or_create_react_graph` 輔助函數
  - 更新 `process_langgraph_request` 和 `managed_langgraph_stream_wrapper` 使用新的 botrun_id 快取邏輯
  - 從 `get_supported_graphs` 移除 LANGGRAPH_REACT_AGENT 避免程式碼重複
  - 關鍵特性：
    - 當 `botrun_id` 為 None/空值時 → 完全跳過快取，每次建立新的 graph
    - 當 `botrun_id` 有值時 → 使用參數雜湊驗證進行快取管理
    - 參數變更時自動清除對應 botrun_id 的快取
    - 支援快取統計與老舊項目清理機制


## [5.6.303]
### Added
- Token 驗證 API：新增 auth_api 模組提供 access token 驗證功能
  - 新增 `TokenVerifyClient` 類別，支持 IAP 認證和標準認證
  - 新增 `POST /api/auth/token_verify` 端點，接收 form data 格式的 access_token
  - 支持與後端 API `/botrun/token_verify` 的整合
  - 完整的錯誤處理：401 (無效 token)、400 (請求格式錯誤)、422 (缺少參數)、500 (服務錯誤)
  - 新增功能測試確保 API 正常運作
  - 參考 [GitHub Issue #44](https://github.com/sebastian-hsu/botrun_flow_lang/issues/44)

### Updated
- 優化 auth_utils.py 的認證機制：重構 verify_jwt_token 函數支持 IAP 認證
  - 使用統一的 `TokenVerifyClient` 取代直接的 aiohttp 調用，避免程式碼重複
  - 自動支持 IAP 認證：當設定 `IAP_CLIENT_ID` 和 `IAP_SERVICE_ACCOUNT_KEY_FILE` 環境變數時自動啟用
  - 統一錯誤處理機制：與 `TokenVerifyClient` 使用一致的錯誤分類和 HTTP 狀態碼
  - 改善日誌記錄：整合 `BotrunLogger` 提供詳細的認證過程記錄
  - 保持向下相容性：所有現有 API 介面和功能保持不變
  - 增強維護性：認證邏輯集中管理，統一 botrun_back API 調用機制
  - 參考 [GitHub Issue #45](https://github.com/sebastian-hsu/botrun_flow_lang/issues/45)

## [5.6.301]
### Added
- JWT Token 認證功能：為 hatch_api 和 storage_api 添加雙重認證機制
  - 保留現有 JWT_TOKENS 萬用 token 檢查邏輯（用於 API 測試）
  - 新增 botrun_back API 認證整合，呼叫 /botrun/token_verify 進行用戶驗證
  - 新增 CurrentUser 模型和權限驗證輔助函數
  - hatch_api：依據不同權限需求實作用戶匹配、hatch owner、讀取權限驗證
  - storage_api：實作 user_id 匹配驗證，/directory-sizes 限制管理員專用
  - 分享機制 API 無需認證：share_hatch, unshare_hatch, is_hatch_shared_with_user
  - 使用現有 aiohttp 進行 HTTP 請求，無需額外依賴
  - 參考 GitHub Issue #42

## [5.6.255]
### Updated
- (seba) 移除 youtube transcript api套件

## [5.6.254]
### Updated
- (seba) 移除 profiling 的相關邏輯

## [5.6.253]
### Updated
- (seba) 把 langgraph_runner加回來

## [5.6.252]
### Updated
- (seba) agent_runner 拿到 langgraph_runner，只留下 agent_runner，有點忘記當初為何需要langgraph_runner

## [5.6.251]
### Added
- (elan) 重構agent_runner以維持通用性
- (elan) 將verify_token函式從subsidy_api.py移到auth_utils.py讓APIs共用
- (elan)Line bot主動推播API新增token驗證機制

## [5.6.221]
### Updated
- langgraph_react_agent，把偵測拿到 cached graph的邏輯往一開始調整，讓 fetch速度更快

## [5.6.203]
### Updated
- 因為要在 botrun_back 裡面執行，預設就將 react agent checkpointer 改成 memory

## [5.6.202]
### Updated
- 加了更多 log

## [5.6.201]
### Updated
- 把 import 搬到外面，因為 langgraph 要搬到 botrun_back 裡面了
- 把 log 寫到 profiling.log

## [5.6.191]
### Added
- 加入 profiling 的程式碼
### Bug fix
- ChatModelEndEvent 加入 chunk, 修正 subsidy api 會出錯的問題

## [5.6.182]
### Updated
- 程式裡用到的 gemini 模型，都變成 2.5 GA 版本

## [5.6.181]
### Updated
- (seba) langchain-mcp-adapters升級，原有的 async 包起來的方式，不需要了
- (seba) 移除 mcp connection pool 的機制

## [5.6.171]
### Added
- 🚀 多使用者 MCP 連線池架構實作 [GitHub Issue #38](https://github.com/sebastian-hsu/botrun_flow_lang/issues/38)
  - 實作具備 LRU 淘汰機制和 TTL 清理功能的連線池
  - 新增每個使用者的連線隔離機制以確保安全性
  - 建立背景清理任務進行自動資源管理
  - 新增完整的連線池監控功能
  - 主要功能：
    - 智慧型連線重複使用（相同使用者 + 相同設定 = 重複使用連線）
    - 安全隔離（不同使用者取得各自獨立的連線）
    - 資源限制（最多 100 個連線，30 分鐘 TTL）
    - 每 5 分鐘自動背景清理
    - 連線池統計與監控

### Added
- (elan) 修正Search node沒有回傳on_chat_model_end事件的問題
- (elan) 新增紀錄Line使用者輸入及LLM輸出的訊息到BigQuery的功能(v2版，紀錄graph內的訊息)

### Updated
- 重構 `langgraph_api.py` 使用連線池，不再每次請求都建立新連線
- 更新 `main.py` 加入應用程式生命週期管理，確保正確清理資源
- 以連線池管理模式取代 `AsyncExitStack` 做法
- search agent node 的 normal chat node 模型改為 gemini 2.5 flash
- 移除 gemini code execution tool

### Files Added
- `botrun_flow_lang/services/mcp_connection_pool.py` - 核心連線池實作
- `botrun_flow_lang/services/mcp_context_manager.py` - 簡化的上下文管理器

### Performance Benefits
- ⚡ 消除連線建立開銷，提升回應速度
- 🔒 使用者隔離防止跨使用者資料洩漏
- 💾 LRU + TTL 機制防止記憶體累積
- 🧹 背景自動清理，無需人工維護
- 📊 具備完整監控與統計功能

## [5.6.111]
### Added
- (seba) 搜尋可以回傳圖片，建立 html的時候，可以 embed 在裡面
  - 一定要 perplexity 才行，所以必須設定好 PPLX_API_KEY 才能支援

## [5.6.101]
### Added
- (elan) 新增主動推播訊息給Line使用者的API
- (elan) 新增取得google sheet內容的功能
- (seba) Hatch 新增 `last_sync_gdoc_time` 欄位，記錄最後一次成功同步 Google Doc 的時間
- (seba) `create_hatch` 和 `update_hatch` API 回傳格式變更，新增 `gdoc_update_success` 欄位顯示 Google Doc 更新是否成功
- (seba) `reload_template_from_doc` API 成功時會更新 `last_sync_gdoc_time`

### Updated
- (seba) 優化 Google Doc 同步機制：
  - 成功時更新 `last_sync_gdoc_time` 為當前 UTC 時間
  - 失敗時保留原有的 `last_sync_gdoc_time` 不變
  - 當 `enable_google_doc_link` 為 false 時清空 `last_sync_gdoc_time`
  - 加入 `last_sync_gdoc_success` 的欄位
- (seba) Search agent normal_chat_node 改成 4.1 mini

## [5.6.45]
### Added
- (seba) Hatch 支援 `google_doc_link` and `enable_google_doc_link`，如果`enable_google_doc_link`為 true，可以從`google_doc_link`抓到內容，Hatch 的 prompt_template 會變成 google_doc 裡的內容
  - 相關修改記錄在這個 [github issue #35](https://github.com/sebastian-hsu/botrun_flow_lang/issues/35)
- hatch api 支援 reload template，如果 google doc 的內容更改，可以呼叫 reload 

## [5.6.44]
### Updated
- (seba) model api 不要用 prefix的，不然api會出 error

## [5.6.43]
### Added
- (seba) 新增 agent-models api，可以在 Google Sheets 設定要支援的 代理人model列表，預設 sheet 是 default-agents，個別的 ENV_NAME-agents

### Flutter Added
- (seba) 波孵人 (非代理人)的模型列表，會由 API讀取。
- (seba) 波孵人 (代理人)的模型列表，會由 API讀取。

## [5.6.42]
### Added
- (seba) 新增 model api，可以在 Google Sheets 設定要支援的 model列表，會讀取 ENV_NAME的 sheet，如果沒有，會讀 default，如果再沒有，就會讀取預設的列表
  - 新增 GOOGLE_APPLICATION_CREDENTIALS_FOR_MODELS_SHEET 環境變數：要存取 models sheet 的 service account key
  - 新增 MODELS_GSPREAD_ID 環境變數：models sheet 的 id

## [5.6.41]
### Bug fix
- (seba) 修正 firestore checkpointer 在 delete_thread時，如果一次刪除太多筆資料，會無法刪除的情形

## [5.6.32]
### Added
- (elan) 新增紀錄Line使用者輸入及LLM輸出的訊息到BigQuery的功能(v1版，尚未紀錄graph內的訊息)
- (elan) 新增使用者顯示名稱欄位到按讚反讚Google sheet紀錄表
### Updated
- (seba) line bot init Logger 的時候，try catch起來，防止沒有設定環境變數出錯，因為這個只有 line 有在用，所以其它平臺不需要

## [5.6.31]
### Added
- (seba) 津貼line加上「reset」語法，使用者輸入之後會清除所有歷史對話 (背景，前面 line 的訊息還在，但是背後不會記得之前的對話了)
- (seba) search agent 在 requirement_node 使用 trust_call，確保回覆true/false

### Updated
- (seba) search agent 如果進到 normal_chat_node，就不會回傳 related questions
- (seba) search agent ，如果是 non stream的模式，在內容裡面，移除 [1], [2]..等參照資訊
 
## [5.6.22]
### Updated
- (seba) 津貼line參考來源不要markdown語法
 
## [5.6.21]
### Updated
- (seba) 刪除 hatch 時，會把 分享的 hatch 關連刪除
 
## [5.5.292]
### Updated
- (seba)search_agent_graph, requirement_node使用 gemini-2.5-flash，並增加 openrouter key的判斷機制，有 openrouter key會使用 openrouter
- (seba)search_agent_graph, related_node使用 gemini-2.5-flash，並增加 openrouter key的判斷機制，有 openrouter key會使用 openrouter
- (seba)search_agent_graph, normal_chat_node使用 gpt-4.1-nano，並增加 openrouter key的判斷機制，有 openrouter key會使用 openrouter

## [5.5.291]
### Added
- (elan)LINE bot 新增相關問題的按鈕功能
- (elan)LINE bot 新增使用者按讚反讚按鈕並將回饋寫入google sheet的功能
- (elan)以環境變數加上官方宣告文字並移除Line bot回覆開頭的空白行

### Updated
- (seba) 可以從 google doc 讀取, requirement_prompt, normal_chat_prompt, related_prompt
- (seba) SearchAgentGraph把原本放在外面的 import，放進 function內，加速import

### Flutter Bug Fix
- (seba) 分享按鈕的網址有錯誤


## [5.5.271]
### Updated
- (seba) subsidy_api 預設改用 google doc 讀取，修改 `google_drive_utils` 讀取 service account 的邏輯

## [5.5.261]
### Added
- (seba) 波孵 UI 加上分享按鈕

## [5.5.243]
### Updated
- (seba) 升級 uvicorn版本

## [5.5.242]
### Added
- (seba) 加入 gemini_code_execution 工具

## [5.5.241]
### Updated
- (seba) react agent 支援 claude 4
- (seba) 搜尋時判斷要用什麼key，不再使用  is_use_openrouter, 會直接判斷openrouter key, base_url是否存在
- (seba) pdf, img 解析，預設使用 gemini 2.5 flash (除非環境變數有特別指定)

## [5.5.221]
### Added
- (seba) hatch_api 加入 is_hatch_shared_with_user
```
# Check if a hatch is shared with a specific user
curl --location 'http://0.0.0.0:8080/api/hatch/123abc/share/target.user@example.com'
# Response example: {"is_shared":true,"message":"Hatch 123abc is shared with user target.user@example.com"}
```

## [5.5.212]
### Added
- (seba) hatch 可以分享，用法如下[Github issue #30](https://github.com/sebastian-hsu/botrun_flow_lang/issues/30)：
```
curl --location 'http://0.0.0.0:8080/api/hatch/123abc/share' \
--header 'Content-Type: application/json' \
--data-raw '{"user_id":"target.user@example.com"}'

# Unshare a hatch
curl --location --request DELETE 'http://0.0.0.0:8080/api/hatch/123abc/share/target.user@example.com'

# Get shared hatches
curl --location 'http://0.0.0.0:8080/api/hatches/shared?user_id=target.user@example.com'
```

## [5.5.204]
### Flutter
- (seba) textfield 加 border


## [5.5.203]
### Added
- (seba) 加入可以取得 youtube summary 的 api

## [5.5.202]
### Flutter Updated
- (seba) 手機版在編輯的時候，可以讓手機鍵盤填滿畫面

## [5.5.201]
### Bug fix & Update
- 使用async with修復LINE Bot API中的Unclosed client session錯誤
- 修正因刪減訊息而造成Line bot無法搜尋及讀取歷史訊息的問題
- 新增Line bot提供相關問題的功能
- 新增從Google Doc取得智津貼提詞的功能

## [5.5.141]
### Bug fix
- chat_with_imgs，會發生 import error 的情形


## [5.5.133]
### Bug fix
- 不硬性檢查 SUBSIDY_LINE_BOT_CHANNEL_SECRET, SUBSIDY_LINE_BOT_CHANNEL_ACCESS_TOKEN環境變數

## [5.5.132]
### Bug fix
- 呼叫 botrun_back/info API，需要支援 server 在 IAP裡面

## [5.5.131]
### Bug fix
- 修正多重async導致Line bot api回應慢的問題
- 移除LineBot class並重構webhook處理流程
- 避免將空訊息傳進llm並確保傳進perplexity的訊息角色有交替
- 修正SearchAgentGraph的add_conditional_edges沒加END導致的KeyError:__end_

## [5.5.72]
### Updated
- 更新套件

## [5.5.61]
### Bug fix
- 修正 stream 模式下無法使用 mcp tools 的問題


## [5.5.51]
### Added
- agent 支援 mcp


## [5.4.281]
### Added
- subsidy_webhook新增訊息頻率限制功能
### Updated
- 修改 建立html 的 prompt，更強調要使用template
### Bug fix
- 修復Line Bot處理並行請求問題：使用類變數追蹤使用者訊息處理狀態，防止頻繁訊息導致Claude API錯誤Line Bot無法再回訊
- 修復perplexity_search中的usage資料存取安全檢查，避免鍵不存在錯誤


## [5.4.233]
### Bug fix
- 修正有些 agent event 無法 json serialized 的問題，如果遇到無法json dump解開的，就會用 str 代替

## [5.4.232]
### Added
- react agent 支援多語系 en, zh-TW，會判斷如果 user_input and system_prompt 都沒有中文，就會用英文

## [5.4.222]
### Updated
- create_react_agent 在 invoke 的時候，會把 config 帶在 agent_runner 裡面，fix 共用 memory 的時候，A上傳的網頁會跑到 B帳號下面的問題

## [5.4.221]
### Added
- 加入 版本號 api

## [5.4.171]
### Updated
- 移除用不到的 workflow 的相關程式碼
- line bot api把 graph init 放在 api 裡面
- 移除 litellm (因為每個 import 都要花2秒)
- pdf_analyzer 移除使用 vertexai，改用 google-genai，因為 vertexai 載入時間要2秒

## [5.4.153]
### Updated
- 調整 langgraph_api.py 不會先讀 graph

## [5.4.152]
### Updated
- 修改產生 HTML 報告的 prompt，讓它更多使用 tailwind等現成框架

## [5.4.151]
### Updated
- 如果env 有輸入OPENROUTER_API_KEY, OPENROUTER_BASE_URL, agent 改用 OpenRouter Claude3.7

## 重構SearchAgentGraph、加入波津貼 LINE Bot記憶對話功能
### Added
- SearchAgentGraph 新增初始化參數 memory，讓波津貼 LINE Bot 可以傳 AsyncFirestoreCheckpointer 記憶對話
- 新增 SearchAgentGraph 的 runtime config，透過 extra_config 參數將它傳入 agent_runner

### Updated
- 移除 SearchAgentGraph 中的參數設定功能，改用 graph runtime config 的方式傳遞參數
- 移除 SearchAgentGraph 的 graph2 和單例模式，讓各個 API 都能產生所屬實例
- 調整 langgraph api中SearchAgentGraph的config設定方式

## [5.4.102]
### Added
- 加入 botrun_back 的 info api

## [5.4.101]
### Updated
- RateLimitClient 加入 cloud logging

## [5.4.91]
### Roy Updated
- 修改 pdf_analyzer 跟 img_analyzer 的 model，可以指定多個 model，並且會依序嘗試，直到有一個成功為止
- 環境變數設定範例：
  - PDF_ANALYZER_MODEL=claude-3-7-sonnet-latest,gemini-2.0-flash
  - IMG_ANALYZER_MODEL=claude-3-7-sonnet-latest,gemini-2.0-flash

## [5.4.31]
### Added
- react agent 在超過　recursion limit 的時候，會回傳錯誤給呼叫方，呼叫方可以 resume，resume 的時候會 將 recursion limit 往上加，讓它可以進行下一輪的呼叫
- ChatAnthropic max token改成 64000

## [5.4.22]
### Added
- 加入 perplexity search 的 openrouter 版本
- 加入環境變數 IS_USE_OPENROUTER，可以指定是否使用 openrouter 的版本
- 加入環境變數 OPENROUTER_API_KEY，可以指定 openrouter 的 api key

## [5.4.21]
### Updated
- agent 的最後 state 也會加到 logger中

## [5.4.11]
### Added
- 加入 botrun_logger 機制，需要設定環境變數 [Issue #12](https://github.com/sebastian-hsu/botrun_flow_lang/issues/12)
  - `BOTRUN_LOG_NAME`: 命名規則，參考 `botrun_back` 的 `BOTRUN_FRONT_URL`，範例：
    - https://dev.botrun.ai > `log-dev-botrun-ai`
    - https://tryai.nat.gov.tw/lab32 > `log-tryai-nat-gov-tw-lab32`
    - 這個參數沒有去呼叫 `botrun_back` 取得的原因是，不想被 restapi 綁住，所以先用手動設定
  - `BOTRUN_LOG_PROJECT_ID`: 參考 `borrun_back`，這個有設定
  - `BOTRUN_LOG_CREDENTIALS_PATH`: 參考 `borrun_back`，這個有設定
- [Logger 機制的說明](https://docs.google.com/presentation/d/1ph7VnUP1FPj4UzOkJ7HQcV0ITqiFUxd7VsRKvUFUjZA/edit?slide=id.p#slide=id.p)

### Updated
- 修改 logger 記錄的型式，並且加入 default_logger，以防深層的 function需要 logger時，沒有 BotrunLogger
- react agent 加入 logger

## [5.3.311]
### Added
- invoke api 加入 session_id 的參數，為了要加入 log
### Updated
- 修改波津貼API的系統提示詞並改成以檔案的方式讀取
- 修改波津貼API的SearchAgentGraph設定

## [5.3.291]
### Added
- 新增波津貼 Line bot webhook 功能：
  - 實作基本資訊回覆功能
  - 整合 agent 回覆機制並設定相關參數
  - 加入訊息過長自動分段發送機制
  - 優化回應內容，移除推論模型的思考過程
- 針對 non-stream 的 langgraph，加入還沒有 tool usage 的 token usage data
- 實現 AsyncFirestoreCheckpointer，使 react agent 可以使用 Firestore 作為狀態持久化後端 [GitHub Issue #8](https://github.com/sebastian-hsu/botrun_flow_lang/issues/8)
### Updated
- AsyncFirestoreCheckpointer 的日誌設置改為環境變數控制，默認不顯示 INFO 級別日誌 [參考作法](https://github.com/sebastian-hsu/botrun_flow_lang/issues/8#issuecomment-2757028985)
- 讓 line bot init 的時候不會因為沒有設定環境變數而出錯
### Bug Fix
- 修正 perplexity search 在 stream的時候，不會回覆正確的 token 使用量

## [5.3.242]
### Updated
- 修正 RateLimitClient，如果沒有設定環境變數，constructor 會出錯

## [5.3.241]
### Updated
- RateLimitClient，如果沒有設定環境變數，會回都可以使用

## [5.3.201]
### Added
- 加入圖片生成速率限制檢查功能
  - 新增 `BotrunRateLimitException` 類別，提供使用者可見的錯誤訊息前綴 
  - 更新 `generate_image` 功能，在生成圖片前檢查使用者配額
  - 當使用者達到每日限制時，顯示友好的錯誤訊息並提供當前使用量資訊
  - 成功生成圖片後自動更新使用計數
  - [GitHub Issue #5](https://github.com/sebastian-hsu/botrun_flow_lang/issues/5)
- 加入 Botrun Rate Limit API 集成
  - 新增 `RateLimitClient` 類別，可以查詢用戶的速率限制信息
  - 添加環境變數 `BOTRUN_BACK_API_BASE` 以連接到 Botrun 後端 API
  - 支援 IAP (Identity-Aware Proxy) 身份驗證，通過環境變數 `IAP_CLIENT_ID` 和 `IAP_SERVICE_ACCOUNT_KEY_FILE` 設定
  - [GitHub Issue #2](https://github.com/sebastian-hsu/botrun_flow_lang/issues/2)
  - [GitHub Issue #3](https://github.com/sebastian-hsu/botrun_flow_lang/issues/3)
- 擴展 `RateLimitClient` 功能
  - 新增 `update_drawing_usage` 方法，支援更新用戶的繪圖使用計數
  - 支援 IAP 和標準身份驗證
  - 處理用戶未找到（404）和其他錯誤情況
  - [GitHub Issue #4](https://github.com/sebastian-hsu/botrun_flow_lang/issues/4)
- 加入簡易 Rate Limit API 端點
  - 新增 `rate_limit_api.py`，提供簡單的 `/api/rate_limit/{username}` GET 端點
  - 封裝 `RateLimitClient` 功能，讓客戶端可輕鬆獲取用戶配額資訊
  - 支援適當的錯誤處理，包括用戶不存在（404）和後端服務錯誤（500）
  - [GitHub Issue #6](https://github.com/sebastian-hsu/botrun_flow_lang/issues/6)

## [5.3.191]
### Updated
- react agent 模型預設使用 claude 3.7，可以傳參數變成 gemini

## [5.3.184]
### Updated
- `token-efficient-tools-2025-02-19` 會造成輸出結果不好, mermaid 的圖亂畫，所以先拿掉
  - https://dev.botrun.ai/s/2d37bdf045de4331ca9882d53e694b3f


## [5.3.183]
### Updated
- prompt caching 最多只支援4個 block，所以先移除 user , assistant message 的 prompt caching

### Bug Fix
- 如果有 user or assistant message 的內容是空的，則不加到 message 裡面
  - https://dev.botrun.ai/s/2d37bdf045de4331ca9882d53e694b3f

## [5.3.182]
### Added
- 修正在 prompt caching 在轉 LangChain message的時候，如果遇到 message 是 array，要多做一層處理

## [5.3.181]
### Added
- react agent 加入 prompt caching 機制
  - https://github.com/langchain-ai/langchain/discussions/25610?sort=top#discussioncomment-10405165
  - https://python.langchain.com/docs/integrations/chat/anthropic/#prompt-caching
  - System Message 加入 prompt caching
  - header 代入 `token-efficient-tools-2025-02-19`
    - https://docs.anthropic.com/en/docs/build-with-claude/tool-use/token-efficient-tool-use
  - user , assistant message 加上 prompt caching (判斷agent model 是 anthropic才會加)


## [5.3.172]
### Updated
- invoke react agent 的 api，可以傳入 agent 的模型

## [5.3.171]
### Updated
- 升級 `botrun-hatch` 的套件

## [5.3.151]
### Updated
- 修改 `botrun-hatch` 的套件

## [5.3.142]
### Updated
- extract module 到 botrun_hatch, botrun_litellm

## [5.3.141]

### Updated
- 修改 boto3 的 compatible version

## [5.3.112]

### Added
- 加入環境變數 PDF_ANALYZER_MODEL, IMG_ANALYZER_MODEL可以指定解析 pdf, img 的 model
  - 目前只支援 claude-3-7-sonnet-latest, gemini-2.0-flash，預設是gemini-2.0-flash

## [5.3.111]

### Added
- 加入環境變數 AGENT_MODEL=claude-3-7-sonnet-latest，可以設定 agent 的 model
  - 目前只支援 claude-3-7-sonnet-latest, gemini-2.0-flash
- 新增web_search工具的使用須知;新增用來比較使用者指定的日期時間與當前時間，判斷是過去還是未來的工具
- 新增用來判斷使用者指定的日期時間是過去還是未來的測試

### Updated
- agent 移除用不到的 tools
- 修改 analyze pdf with gemini 出錯時的 return value

## [5.3.71]

### Updated
- agent 從 claude 3.7 變成 gemini 2.0
- pdf, image 解析從 claude  3.7 變成 gemini 2.0

## [5.3.53]

### Updated
- 調整react agent的system prompt以修正將使用者指定時間誤判成未來的問題

## [5.3.52]

### Updated
- agent 產生的plotly, mermaid, html的，不會有7天的限制
  - 修正：波孵agent 建立的圖表，html, 不要有七天的暫存限制 (https://app.asana.com/0/1207731969918412/1209569395447152)

## [5.3.51]

### Updated
- FirestoreBase 會吃 GOOGLE_CLOUD_PROJECT的參數，可以指定 project，主要是給其它的 service account，可以指定 project 使用

## [5.3.42]

### Updated
- 如果遇到 rate limit 的問題，會 sleep 7-20 秒，然後retry 

## [5.3.41]

### Updated
- 修改判斷過去、現在、未來的 prompt 到 react agent 的 system prompt

## [5.3.31]

### Updated
- 新增 產生網頁的 tools doc 到 document

## [5.3.21]

### Updated
- 解決react 判斷時間本來在過去，但是判斷在未來的情況

## [5.2.282]

### Updated
- 修改 langgraph_react_agent 的 model，可以支援 claude 的 key rotation

## [5.2.281]

### Added
- 加入 storage api，可以取得 GCS bucket 中每個目錄的總檔案大小與檔案數量，排除 tmp 目錄

## [5.2.271]

### Updated
- 系統中所有的 3.5 sonnet 的 model 都改成 3.7 sonnet 的 model

## [5.2.264]

### Updated
- react agent 移除 deep_research tool，感覺還沒有做的很好

## [5.2.263]

### Added
- react agent 加入 deep_research tool，可以進行深度研究

## [5.2.262]

### Added
- 加入 create_html_page tool，可以生成 html 頁面

## [5.2.261]

### Updated
- 修改 langgraph_react_agent 的 model，改成使用 claude-3-7-sonnet-latest
- langchain 相關的套件也升級，以支援 claude-3-7-sonnet-latest

## [5.2.251]

### Updated
- 修改 langgraph_react_agent 的 model，改成使用 claude-3-7-sonnet-latest

## [5.2.191]

### Updated
- 修改 langgraph_react_agent 的 current_time的註解，避免時間錯亂的問題

## [5.2.163]

### Updated
- 修改 langgraph_react_agent 的 agent 模型，改成使用 gemini-2.0-pro-exp

## [5.2.162]

### Updated
- 修改 web_search 調用的方式，會傳 current_time給它，避免時間錯亂的問題

## [5.2.161]

### Updated
- perplexity 的 model 支援參數傳入，目前支援：sonar-reasoning-pro 跟 sonar-pro

## [5.2.131]

### Updated
- pdf_analyzer 在使用 anthrpic失敗後，會使用 gemini-2.0-flash-001 來分析 pdf 文件

## [5.2.123]

### Added
- 新增 ReAct Agent Tools Documentation，可以在 /docs/tools 看到

## [5.2.122]

### Updated
- 調整 PERPLEXITY_SEARCH_AGENT ，讓它在如果使用者沒有搜尋需求時，不會上網搜尋
  - 原始需求：https://app.asana.com/0/1207731969918412/1209284806782749 

## [5.2.121]

### Updated
- 修正 langgraph_react_agent 的 prompt，請它在回答 URL 的時候要注意

## [5.2.101]

### Updated
- 修正 langgraph_react_agent 的 prompt 參數變更

## [5.2.83]

### Bug Fix
- 修正 user_prompt_prefix 沒有傳給 perplexity 的問題

## [5.2.82]

### Updated
- perplexity 如果整 user_prompt_prefix 的時候，會先加入 <使用者提問> 標籤，再加入 input_content

## [5.2.81]

### Updated
- perplexity 的 search_domain_filter 不支援 wildcard(*) 的網域，所以在傳api之前，會先檢查網域的合理性。

## [5.2.73]

### Bug Fix
- 修正 perplexity 沒有真的搜尋的問題

## [5.2.72]

### Updated
- 調整 chat_with_imgs, chat_with_pdf 的 prompt，讓他們回應時可以帶圖表的內容

### Bug Fix
- 修正 system prompt 會傳兩次的問題

## [5.2.71]

### Updated
- 修改相關的 prompt

## [5.2.67]

### Updated
- 修改相關的 prompt

## [5.2.63]

### Added
- (seba) 加入 Mermaid 圖表功能：
  - 新增 `create_mermaid_visualization` tool，支援生成互動式圖表
  - 支援多種圖表類型：流程圖、序列圖、類別圖等
  - 整合 chat_with_pdf 和 chat_with_imgs 與 Mermaid 的圖表生成功能

### Updated
- (seba) 改進 langgraph_react_agent 的系統提示：
  - 加入 Mermaid 相關工具的使用說明和範例
  - 明確指定工具間的整合使用方式
  - 統一回應格式，確保圖表 URL 正確顯示

## [5.2.62]

### Updated
- (seba) 改進 langgraph_react_agent 的系統提示：
  - 強化 plotly 圖表 URL 的顯示要求
  - 提供更具體的回應格式範例
  - 加入固定的 URL 顯示位置要求
  - 添加 URL 顯示檢查機制
  - 改進錯誤處理和提示訊息

## [5.2.61]

### Added
- (seba) 新增 plotly 相關功能：
  - 加入 `create_plotly_visualization` tool，支援生成互動式圖表
  - 整合 chat_with_pdf 和 chat_with_imgs 與 plotly 的數據視覺化功能
  - 支援從 PDF 和圖片中提取數據並生成 plotly 圖表

### Updated
- (seba) 改進 langgraph_react_agent 的系統提示：
  - 加入 plotly 相關工具的使用說明和範例
  - 明確指定工具間的整合使用方式
  - 統一回應格式，確保圖表 URL 正確顯示
  - 改進錯誤處理和提示訊息

## [5.2.51]

### Added
- (seba) 新增 `get_img_content_type` 函數於 `img_util.py`：
  - 使用 imghdr 檢測實際的圖片格式
  - 支援 JPEG、PNG、GIF、WebP 等常見格式
  - 提供詳細的錯誤處理機制

### Updated
- (seba) 改進 `local_files.py` 的檔案處理機制：
  - 修改 `get_file_content_type` 函數，整合 `get_img_content_type` 功能
  - 優化 `upload_and_get_tmp_public_url` 函數，自動修正圖片副檔名
  - 根據實際圖片格式調整上傳檔案的副檔名
- (seba) 更新測試用例：
  - 新增 `test_img_util.py` 測試檔案
  - 加入圖片格式檢測的相關測試
  - 改進測試案例的錯誤訊息

## [5.2.42] - 2025-02-04

### Updated
- (seba) 重新命名 `chat_with_img` 為 `chat_with_imgs`：
  - 函數名稱更好地反映多圖片處理能力
  - 更新相關的文檔說明
  - 加入 generate_tmp_public_url 的使用說明

## [5.2.41] - 2025-02-04

### Added
- (seba) 改善圖片處理功能於 `img_util.py`：
  - 加入 GCS 圖片 URL 的重新導向處理機制
  - 改進 httpx client 的設定與生命週期管理
  - 支援多圖片分析
  - 優化錯誤處理，提供更詳細的錯誤訊息
- (seba) langgraph_react_agent 加入 generate_image tool：
  - 使用 DALL-E 3 模型生成高品質圖片
  - 支援詳細的提示詞控制（風格、構圖、色調等）
  - 自動處理圖片生成限制和安全檢查

### Updated
- (seba) 更新 langgraph_react_agent 的圖片生成回應格式：
  - 修改系統提示為中文
  - 統一回應格式為 `@begin img("{image_url}") @end`
  - 確保圖片 URL 一定會包含在回應中
- (seba) 更新 `langgraph_react_agent.py` 中的 `chat_with_img` 工具：
  - 修改介面支援多張圖片輸入（最多20張）
  - 加入多圖片分析和比較功能
  - 更新文件說明，包含多圖片處理的能力和限制
  - 改進參數說明，明確標示支援多圖片輸入
- (seba) 更新 Dockerfile，加入 --system 參數，修改 uv 無法正常安裝的問題

### Removed
- (seba) 暫時移除 langgraph_react_agent 的 get_youtube_transcript tool，因為 youtube-transcript-api 在 cloud run 環境下無法正常運作

## [5.1.252] - 2025-01-25

### Updated
- (seba) langgraph_react_agent 的 get_youtube_transcript 功能改進：
  - 支援多種 YouTube URL 格式（標準網址、短網址、嵌入網址）
  - 改進字幕獲取邏輯，優先嘗試人工字幕，再嘗試自動生成字幕
  - 提供更詳細的錯誤訊息，方便除錯
  - 加入型別提示和詳細的文檔說明

## [5.1.251] - 2025-01-25
### Added
- (seba) langgraph_react_agent 加入 get_youtube_transcript tool，可以取得 YouTube 影片的字幕內容
- (seba) langgraph_react_agent 加入 generate_tmp_public_url tool，可以將本地檔案上傳並取得暫存的公開 URL
- (seba) 加入 local_files 模組，提供檔案上傳功能
- (seba) storage api 加入 /tmp-files 的 endpoint，可以上傳檔案到 GCP 並設為公開存取，檔案會在 7 天後自動刪除

### Updated
- (seba) 修改 chat_with_pdf 功能，改為支援從 URL 讀取 PDF 檔案，不再需要本地檔案
- (seba) storage service 加入 lifecycle rules 機制，設定 /tmp 開頭的檔案會在 7 天後自動刪除
- (seba) 改善 get_youtube_transcript 和 scrape 的文檔說明，加入更詳細的參數說明和使用建議

## [5.1.243] - 2025-01-24
### Added
- (seba) langgraph_react_agent 加入 chat_with_pdf 的 tool，可以跟 PDF 文件對話

## [5.1.242] - 2025-01-24
### Added
- (seba) 加入 PDF analyzer 的測試，可以測試環境影響說明書中的表格內容

## [5.1.241] - 2025-01-24
### Updated
- (seba) langgraph_react_agent 加入 days_between 的 tool

## [5.1.235] - 2025-01-23
### Updated
- (seba) hatch 加入 enable_agent的參數

## [5.1.234] - 2025-01-23
### Updated
- (seba) langgraph_react_agent　可以傳入 system_prompt

## [5.1.233] - 2025-01-23
### Added
- (seba)　加入 langgraph_react_agent，可以做 react 的聊天

## [5.1.232] - 2025-01-23
### Bug Fix
- (seba)　修正 perplexity 有時候引證回不來的情況，原因是 perplexity 的 api不見得都有 finish_reason 為 stop 的狀況，但是回來的 response 都會有 citations 的資料，所以就不等 stop才抓，直接抓 citations 的資料

## [5.1.231] - 2025-01-23
### Updated
- (seba)　perplexity 的模型改成使用 sonar-pro

## [5.1.102] - 2025-01-10
### Bug fix
- (seba) 修正　perplexity 搜尋沒有給 domain_filter 但是沒有產生參考文獻的問題

## [5.1.101] - 2025-01-10
### Bug fix
- (seba) 修正　perplexity 搜尋用錯 graph，導致有些會無法回覆

## [5.1.92] - 2025-01-09
### Updated
- (seba) perplexity api 優化 stream為 false的輸出

## [5.1.91] - 2025-01-09
### Added
- (seba) LangGraph api 支援 stream 的輸出

## [5.1.81] - 2025-01-08
### Added
- (seba) LangGraph api 加入 invoke 介面，目前還不支援 stream

## [5.1.71] - 2025-01-07
### Updated
- (seba) subsidy api，token 驗證多加幾組 token
- (seba) 修正 subsidy api 的 提示文字，阻擋紅隊攻擊

## [4.12.262] - 2024-12-26
### Updated
- (seba) 加入 subsidy api，加入 token 驗證

## [4.12.261] - 2024-12-26
### Added
- (seba) 加入 subsidy api，可以做補助申請的 api 呼叫

## [4.12.191] - 2024-12-19
### Updated
- (seba) Hatch 加入 model_name 的參數，可以指定使用哪個 model

## [4.12.172] - 2024-12-17
### Updated
- (seba) 修改 storage api 的 回傳訊息

## [4.12.171] - 2024-12-17
### Added
- (seba) 加入 storage api，可以上傳跟下載檔案

## [4.12.161] - 2024-12-16
### Updated
- (seba) 降版 pdfminer-six 到 20231228

## [4.12.124] - 2024-12-12
### Updated
- (seba) extract node disable streaming

## [4.12.123] - 2024-12-12
### Updated
- (seba) summarize node，還是繼續使用 gemini

## [4.12.122] - 2024-12-12
### Updated
- (seba) summarize node，會先嘗試 claude，失敗再嘗試 gemini

## [4.12.121] - 2024-12-12
### Updated
- (seba) 修改 tavily search 為 custom search
- (seba) 抓取網頁，pdf 加入了 cache 機制
- (seba) extract node，會先嘗試 claude，失敗再嘗試 gemini

## [4.12.103] - 2024-12-10
### Updated
- (seba) base_url如果沒有，return None

## [4.12.102] - 2024-12-10
### Updated
- (seba) 修正抓 taide/ 開頭的時候，沒有抓後面完整模型名字的問題

## [4.12.101] - 2024-12-10
### Updated
- (seba) 支援如果 model_name 是 taide/ 開頭的話也會使用 taide 的 model

## [4.12.41] - 2024-12-04
### Updated
- (seba) langgraph api，最後會加入 content 跟 state 的輸出
- (seba) 支援 ai_researcher 的 content 輸出
- (seba) api 支援 /langgraph/list 取得所有支援的 graph

## [4.12.32] - 2024-12-03
### Updated
- (seba) langgraph api，可以支援 search_agent 跟 ai_researcher

## [4.12.31] - 2024-12-03
### Added
- (seba) 加入 langgraph api，可以執行 langgraph


## [4.11.281] - 2024-11-28
### Updated
- (seba) hatch 加入 user_prompt_prefix，可以在每次的　user prompt前面加入這段文字
- (seba) hatch 加入 search_domain_filter，可以控制搜尋的網域限制, 目前只有針對 perplexit 有效, 範例：["*.gov.tw", "-*.gov.cn"]

## [4.11.272] - 2024-11-27
### Updated
- (seba) llm_agent_util 的 AGENT_TEMPLATE 改為使用 tag 標籤

## [4.11.271] - 2024-11-27
### Updated
- (seba) llm_agent 加入 max_system_prompt_length 參數，可以控制是否要使用 system prompt

## [4.11.265] - 2024-11-26
### Updated
- (seba) 加入 get_custom_llm_provider 函式，可以取得 custom llm provider
 
## [4.11.264] - 2024-11-26
### Updated
- (seba) 如果 model 是 botrun 的話，會從環境變數取得 api key 跟 base url
 
## [4.11.263] - 2024-11-26
### Updated
- (seba) llm_agent 加入 include_in_history 參數，可以控制是否將這次的回答加入 history

## [4.11.262] - 2024-11-26
### Updated
- (seba) 加入 llm_agent_util 的 agent template

- (seba) extract botrun_chat 的 llm_agent 到 botrun_flow_lang
## [4.11.261] - 2024-11-26
### Added
- (seba) extract botrun_chat 的 llm_agent 到 botrun_flow_lang
- (seba) 加入 llm_utils，可以取得 api key 跟 base url

## [4.11.201] - 2024-11-20
### Updated
- (seba) hatch 加入 search_vendor 參數，可以控制搜尋的 vendor

## [4.11.191] - 2024-11-19
### Updated
- (seba) hatch 加入 related_question_prompt 參數，可以控制產生相關問題的 prompt

## [4.11.152] - 2024-11-15
### Updated
- (seba) hatch 加入 enable_search 參數，可以控制是否要開啟搜尋

## [4.11.151] - 2024-11-15
### Updated
- (seba) 更新 fastapi 到 0.115.5

## [4.11.141] - 2024-11-14
### Updated
- (seba) rename PERPLEXITY_API_KEY to PPLX_API_KEY

## [4.11.121] - 2024-11-12
### Added
- (seba) 加入 hatch/statistics API，可以取得所有 hatches 的統計資料

## [4.11.81] - 2024-11-08
### Added
- (seba) 加入 vertexai search node

## [4.11.81] - 2024-11-06
### Updated
- (seba) 調整 SearchAndScrapeNode 的子問題數量為 3

## [4.11.64] - 2024-11-06
### Updated
- (seba) 調整 SearchAndScrapeNode 的子問題數量為 3

## [4.11.63] - 2024-11-06
### Updated
- (seba) 修正 PerplexityNode 的 history 最後一個是 user role 的問題

## [4.11.62] - 2024-11-06
### Updated
- (seba) 修正 PerplexityNode 的 history 的 system, user role 的問題

## [4.11.61] - 2024-11-06
### Added
- (seba) 加入 PerplexityNode，可以做 perplexity 搜尋

## [4.11.41] - 2024-11-04
### Updated
- (seba) 修改 SearchAndScrapeNode 的 運行方式，會問五個問題，然後total 抓五個網頁

## [4.11.34] - 2024-11-03
### Updated
- (seba) 修改 SearchAndScrapeNode 的 運行方式，會從所有的搜尋結果中選出最相關的五個，然後再對這五個做爬蟲，爬蟲設定 timeout 為 15 秒

## [4.11.33] - 2024-11-03
### Updated
- (seba) 修改 SearchAndScrapeNode 的 print 方式

## [4.11.32] - 2024-11-03
### Updated
- (seba) user_setting 加入 search_vendor 跟 search_enabled

## [4.11.31] - 2024-11-03
### Updated
- (seba) 修改 SearchAndScrapeNode 的 print 方式

## [4.11.22] - 2024-11-02
### Updated
- (seba) StartNode 跟 LLMNode 加入 input_variables，可以傳入 history 變數

## [4.11.21] - 2024-11-02
### Added
- (seba) 加入 SearchAndScrapeNode，只要輸入問題，可以做搜尋跟爬蟲

## [4.10.311] - 2024-10-31
### Updated
- (seba) BaseNodeData 加入 complete_output 的參數，可以指定 complete 的時候要印出哪個 output_variables 的變數

## [4.10.301] - 2024-10-30
### Bug Fix
- (seba) 修正 async iteration node 裡面的 node 存取 item 的問題

## [4.10.292] - 2024-10-29
### Updated
- (seba) 修改 http request node 的 errorprint 方式

## [4.10.291] - 2024-10-29
### Updated
- (seba) 更新 LLM 的呼叫方式

## [4.10.284] - 2024-10-28
### Updated
- (seba) 搜尋排除 pdf, doc, docx, xls, xlsx, ppt, pptx
- (seba) 加入 user_workflow_api

## [4.10.283] - 2024-10-28
### Updated
- (seba) 改變目錄結構，app 改為 botrun_flow_lang

## [4.10.282] - 2024-10-28
### Updated
- (seba) uvicorn 降為 0.25.0

## [4.10.281] - 2024-10-28
### Updated
- (seba) fastapi 降為 0.110.0

## [4.10.261] - 2024-10-26
### Added
- (seba) 加入 code ndoe，可以輸入 python程式碼
- (seba) 加入 search api，可以做 google 搜尋
- (seba) 加入 http request node，可以做 http request
- (seba) 加入 iteration node，可以做迴圈
- (seba) 加入 async iteration node，可以做非同步迴圈

## [4.10.221] - 2024-10-22
### Updated
- (seba) 支援 stream 的 workflow engine

## [4.10.211] - 2024-10-21
### Added
- New API endpoint `/hatch/default/{user_id}` to get the default hatch for a user
- New API endpoint `/hatch/set_default` to set a hatch as default for a user
- New API endpoint `/user_setting/` CRUD for user setting
### Updated
- (seba) hatch 加上 is_default，預設為 false

## [4.10.151] - 2024-10-15
### Added
- (seba) New API endpoint `/hatch/hatches` to get a list of hatches for a specific user, with pagination support.

## [4.10.142] - 2024-10-14
### Updated
- (seba) allow all cors

## [4.10.141] - 2024-10-14
### Updated
- (seba) 加入能夠設定 flow，以及執行 flow 的 workflow engine
- (seba) 加入hatch_api

## [4.10.21] - 2024-10-02
### Added
- (seba) init project

