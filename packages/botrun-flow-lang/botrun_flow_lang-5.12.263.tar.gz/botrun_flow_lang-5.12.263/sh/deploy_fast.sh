#!/bin/bash
set -ex

source .venv/bin/activate

# poetry export -f requirements.txt --output requirements.txt --without-hashes --without-urls

gcloud builds submit --config cloudbuild_fast.yaml --project=scoop-386004
gcloud run deploy botrun-flow-lang-fastapi-fast \
  --image asia-east1-docker.pkg.dev/scoop-386004/botrun-flow-lang/botrun-flow-lang-fastapi-fast \
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