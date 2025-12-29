# botrun_flow_lang v1.0

## 開發環境安裝
- 使用 Python 3.11.9
- 安裝 uv 來管理 python 套件
  - 安裝 uv 可以參考: [官方文件](https://docs.astral.sh/uv/getting-started/installation/)
  - 第一次使用在 /project_folder/ 下執行
  ```bash
  uv sync
  ```
  - 之後如果需要新增/刪除套件，需要執行 `uv add xxx` , `uv remove xxx`


## 要進行本地端 fastapi 的開發
```bash
uvicorn botrun_flow_lang.main:app --reload --host 0.0.0.0 --port 8080
```
- 可以執行的 curl，可以參考 `botrun_flow_lang/tests/api_functional_tests.py`

## 開發規範
- 修改 `CHANGELOG.md`
- release 修改 `pyproject.toml`

## (備份用)如果要進行 agent 的開發
- 先[安裝 langgraph cli](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/)
- uncomment `botrun_flow_lang/langgraph_agents/agents/langgraph_react_agent.py` 的最後面幾行
- 在 project 目錄下執行 `langgraph dev`


# 以下是部署參考用，先保留
## 部署時會輸出可用的 requirements.txt
```bash
uv export --format requirements-txt --output-file requirements.txt --no-hashes
```
### 建立 firestore 的 index (以下以 dev 為例)，實際部署的程式寫在 `botrun_chat_deploy`
```bash
gcloud firestore indexes composite create \
  --collection-group=botrun-hatch-dev-hatch \
  --field-config=field-path=user_id,order=ascending \
  --field-config=field-path=name,order=ascending \
  --field-config=field-path=__name__,order=ascending \
  --project=scoop-386004

# 為AsyncFirestoreCheckpointer建立索引
gcloud firestore indexes composite create \
  --collection-group=botrun-flow-lang-dev-checkpointer \
  --field-config=field-path=checkpoint_ns,order=ascending \
  --field-config=field-path=thread_id,order=ascending \
  --field-config=field-path=timestamp,order=descending \
  --field-config=field-path=__name__,order=descending \
  --project=scoop-386004
```

### 打包 dev
```bash
gcloud builds submit --config cloudbuild_fastapi_dev.yaml --project=scoop-386004
```
### deploy cloud run, dev 的版本
```bash
gcloud run deploy botrun-flow-lang-fastapi-dev \
  --image asia-east1-docker.pkg.dev/scoop-386004/botrun-flow-lang/botrun-flow-lang-fastapi-dev \
  --port 8080 \
  --platform managed \
  --allow-unauthenticated \
  --project=scoop-386004 \
  --region=asia-east1 \
  --cpu 2 \
  --memory 8Gi \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 3600s \
  --concurrency 300 \
  --cpu-boost \
```

### 建立 staging 的 index
```bash
gcloud firestore indexes composite create \
  --collection-group=botrun-hatch-hatch \
  --field-config=field-path=user_id,order=ascending \
  --field-config=field-path=name,order=ascending \
  --field-config=field-path=__name__,order=ascending \
  --project=scoop-386004
```

### 打包 Cloud Run, staging 的版本
```bash
gcloud builds submit --config cloudbuild_fastapi.yaml --project=scoop-386004
```

### 佈署 cloud run, staging 的版本
```bash
gcloud run deploy botrun-flow-lang-fastapi \
  --image asia-east1-docker.pkg.dev/scoop-386004/botrun-flow-lang/botrun-flow-lang-fastapi \
  --port 8080 \
  --platform managed \
  --allow-unauthenticated \
  --project=scoop-386004 \
  --region=asia-east1 \
  --cpu 2 \
  --memory 8Gi \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 3600s \
  --concurrency 300 \
  --cpu-boost \
```

## 為了要減少冷啟動的時間，每十分鐘呼叫一次 heartbeat (為了省錢已移除，目前留著備份)
```bash
gcloud scheduler jobs create http botrun-flow-lang-heartbeat-job-$ENV \
  --schedule "*/10 * * * *" \
  --time-zone "Asia/Taipei" \
  --uri "https://botrun-flow-lang-fastapi-$ENV-36186877499.asia-east1.run.app/heartbeat" \
  --http-method GET \
  --location "asia-east1" \
  --project "scoop-386004"
```
測試 scheduler
```bash
gcloud scheduler jobs run botrun-flow-lang-heartbeat-job-$ENV --location "asia-east1" --project "scoop-386004"
```
