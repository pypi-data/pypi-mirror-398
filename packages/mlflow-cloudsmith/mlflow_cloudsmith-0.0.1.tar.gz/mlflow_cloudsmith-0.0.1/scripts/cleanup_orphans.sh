#!/usr/bin/env bash
# Minimal Cloudsmith MLflow cleanup: delete by run id and/or experiment id.
# No MLflow API calls. Safe by default (requires --confirm or CLEANUP_CONFIRM=1).

# Re-exec with bash if invoked with sh
if [ -z "${BASH_VERSION:-}" ]; then exec bash "$0" "$@"; fi

set -euo pipefail

# Defaults / config
CLOUDSMITH_API_KEY=${CLOUDSMITH_API_KEY:-""}
CLOUDSMITH_OWNER=${CLOUDSMITH_OWNER:-""}
CLOUDSMITH_REPO=${CLOUDSMITH_REPO:-""}
CLOUDSMITH_API_BASE=${CLOUDSMITH_API_BASE:-"https://api.cloudsmith.io/v1"}
CLOUDSMITH_PAGE_SIZE=${CLOUDSMITH_PAGE_SIZE:-100}
RUN_ID=${RUN_ID:-""}
EXPERIMENT_ID=${EXPERIMENT_ID:-""}
CLEANUP_CONFIRM=${CLEANUP_CONFIRM:-0}
JQ=${JQ:-jq}
CURL=${CURL:-curl}

usage() {
  cat <<EOF
Usage: $(basename "$0") [--run-id <run_id>] [--experiment-id <exp_id>] [--confirm]

Env vars (alternatively use flags):
  CLOUDSMITH_API_KEY   Required. Cloudsmith API key
  CLOUDSMITH_OWNER     Required. Cloudsmith owner/org slug
  CLOUDSMITH_REPO      Required. Cloudsmith repo slug
  RUN_ID               Optional. MLflow run id (32-hex or custom)
  EXPERIMENT_ID        Optional. MLflow experiment id (numeric or string)
  CLEANUP_CONFIRM=1    Optional. Perform deletion (otherwise dry-run)

Deletes Cloudsmith RAW packages tagged with mlflow filtered by the provided
experiment id and/or run id. No MLflow API calls are made.
EOF
}

require_bin() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Error: required binary '$1' not found in PATH" >&2
    exit 127
  }
}

require_env() {
  local name="$1"; local val="$2"
  if [[ -z "$val" ]]; then
    echo "Error: $name must be set" >&2
    usage
    exit 2
  fi
}

# Parse args (optional)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id)
      RUN_ID="${2:-}"; shift 2 ;;
    --experiment-id)
      EXPERIMENT_ID="${2:-}"; shift 2 ;;
    --confirm)
      CLEANUP_CONFIRM=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

main() {
  require_bin "$CURL"
  require_bin "$JQ"

  require_env CLOUDSMITH_API_KEY "$CLOUDSMITH_API_KEY"
  require_env CLOUDSMITH_OWNER "$CLOUDSMITH_OWNER"
  require_env CLOUDSMITH_REPO "$CLOUDSMITH_REPO"

  if [[ -z "$RUN_ID" && -z "$EXPERIMENT_ID" ]]; then
    echo "Error: Provide at least --run-id or --experiment-id (or env vars)." >&2
    usage
    exit 2
  fi

  # Build Cloudsmith search query
  local query="format:raw AND tag:mlflow"
  if [[ -n "$EXPERIMENT_ID" ]]; then
    query+=" AND tag:experiment-$EXPERIMENT_ID"
  fi
  if [[ -n "$RUN_ID" ]]; then
    query+=" AND tag:run-$RUN_ID"
  fi
  if [[ -n "$RUN_ID" && -n "$EXPERIMENT_ID" ]]; then
    query+=" AND version:\"$EXPERIMENT_ID+$RUN_ID\""
  fi

  local cs_headers=( -H "Authorization: Bearer ${CLOUDSMITH_API_KEY}" -H 'Accept: application/json' )
  local cs_url="${CLOUDSMITH_API_BASE}/packages/${CLOUDSMITH_OWNER}/${CLOUDSMITH_REPO}/"

  echo "Querying Cloudsmith: $query" >&2
  local page=1 total=0 deleted=0
  while :; do
    # Fetch page and capture HTTP status
    http_out=$($CURL -sS -G "$cs_url" "${cs_headers[@]}" \
      --data-urlencode "query=${query}" \
      --data-urlencode "page=${page}" \
      --data-urlencode "page_size=${CLOUDSMITH_PAGE_SIZE}" \
      -w '\n%{http_code}')
    resp="${http_out%$'\n'*}"
    code="${http_out##*$'\n'}"
    if [[ "$code" != "200" ]]; then
      # Some Cloudsmith instances return 404 with {"detail":"Invalid page."}
      # when requesting a page beyond the end. Treat this as end-of-results.
      if [[ "$code" == "404" ]] && echo "$resp" | grep -qi 'Invalid page'; then
        break
      fi
      echo "ERROR: Cloudsmith API returned HTTP $code" >&2
      echo "Response: ${resp:0:500}" >&2
      exit 1
    fi

    # Ensure JSON is an array; if not, report and exit
    jtype=$(echo "$resp" | $JQ -r 'type' || echo "parse-error")
    if [[ "$jtype" != "array" ]]; then
      echo "ERROR: Unexpected JSON type from Cloudsmith: $jtype" >&2
      echo "Body (truncated): ${resp:0:500}" >&2
      exit 1
    fi

    # Count array items
    count=$(echo "$resp" | $JQ 'length')
  if [[ "$count" == "0" ]]; then
      break
    fi

    echo "$resp" | $JQ -r '
      map(select(type=="object"))
      | .[]
      | "Target: \(.identifier_perm // "-") name=\(.name // "-") file=\(.filename // "-")"'
    total=$(( total + count ))

    if [[ "$CLEANUP_CONFIRM" == "1" ]]; then
      # Delete each identifier in this page
  ids=$(echo "$resp" | $JQ -r 'map(select(type=="object")) | .[].identifier_perm | select(. != null)')
      while IFS= read -r id; do
        [[ -z "$id" ]] && continue
        del_url="${CLOUDSMITH_API_BASE}/packages/${CLOUDSMITH_OWNER}/${CLOUDSMITH_REPO}/${id}/"
        code=$($CURL -sS -X DELETE "$del_url" "${cs_headers[@]}" -o /dev/null -w "%{http_code}")
        if [[ "$code" == "204" ]]; then
          echo "Deleted: $id"
          deleted=$(( deleted + 1 ))
        else
          echo "ERROR: Delete failed for $id (HTTP $code)" >&2
        fi
      done <<< "$ids"
    fi

    # If we got fewer than a full page, assume no more results
    if [[ "$count" -lt "$CLOUDSMITH_PAGE_SIZE" ]]; then
      break
    fi
    page=$(( page + 1 ))
  done

  if [[ "$CLEANUP_CONFIRM" == "1" ]]; then
    echo "Done. Deleted $deleted package(s) out of $total matched." >&2
  else
    echo "Dry-run. Matched $total package(s). Use --confirm or CLEANUP_CONFIRM=1 to delete." >&2
  fi
}

main "$@"
