#!/bin/bash
set -ex

# 建立新環境的時候要執行
# gcloud firestore indexes composite create \
#   --collection-group=botrun-hatch-dev-hatch \
#   --field-config=field-path=user_id,order=ascending \
#   --field-config=field-path=name,order=ascending \
#   --field-config=field-path=__name__,order=ascending \
#   --project=scoop-386004
source .venv/bin/activate

# poetry export -f requirements.txt --output requirements.txt --without-hashes --without-urls

sed 's/\$ENV/modaline/g' cloudbuild_template.yaml > cloudbuild_modaline.yaml
sed 's/\$ENV/modaline/g' Dockerfile.template > Dockerfile.modaline

gcloud builds submit --config cloudbuild_modaline.yaml --project=scoop-386004
gcloud alpha run deploy botrun-flow-lang-fastapi-modaline \
  --image asia-east1-docker.pkg.dev/scoop-386004/botrun-flow-lang/botrun-flow-lang-fastapi-modaline \
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
  --cpu-boost 
# 如果冷啟動不是問題，應該要改成 gen2或是 default