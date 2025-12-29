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

sed 's/\$ENV/dev/g' cloudbuild_template.yaml > cloudbuild_dev.yaml
sed 's/\$ENV/dev/g' Dockerfile.template > Dockerfile.dev

gcloud builds submit --config cloudbuild_dev.yaml --project=scoop-386004
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
  --cpu-boost 
# 如果冷啟動不是問題，應該要改成 gen2或是 default