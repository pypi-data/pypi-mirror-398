#!/bin/bash
set -ex

source .venv/bin/activate
# gcloud firestore indexes composite create \
#   --collection-group=botrun-hatch-hatch \
#   --field-config=field-path=user_id,order=ascending \
#   --field-config=field-path=name,order=ascending \
#   --field-config=field-path=__name__,order=ascending \
#   --project=scoop-386004

poetry export -f requirements.txt --output requirements.txt --without-hashes --without-urls

gcloud builds submit --config cloudbuild_prod.yaml --project=scoop-386004
gcloud run deploy botrun-flow-lang-fastapi-prod \
  --image asia-east1-docker.pkg.dev/scoop-386004/botrun-flow-lang/botrun-flow-lang-fastapi-prod \
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
  --execution-environment=gen1
# 如果冷啟動不是問題，應該要改成 gen2或是 default