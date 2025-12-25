# MLflow Cloudsmith Plugin

[![CI](https://github.com/cloudsmith-io/mlflow-cloudsmith-plugin/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/cloudsmith-io/mlflow-cloudsmith-plugin/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8–3.12](https://img.shields.io/badge/python-3.8%E2%80%933.12-blue.svg)](https://www.python.org/downloads/)
[![MLflow 2.x](https://img.shields.io/badge/MLflow-2.x-orange.svg)](https://mlflow.org/)

**MLflow Artifact Repository plugin** that stores artifacts as **Cloudsmith RAW packages**.

---

## Key Features

* Seamless MLflow integration (`cloudsmith://owner/repo`)
* List/Download artifacts within the MLflow UI
* Organized via tags (`mlflow`, `experiment-<id>`, `run-<id>`, `path-<artifact_path>`)

---

## Installation

```bash
pip install mlflow-cloudsmith
```

---

## Usage with MLflow

```python
import os
import mlflow

os.environ["CLOUDSMITH_API_KEY"] = "<your-api-key>"
os.environ["MLFLOW_ARTIFACT_URI"] = "cloudsmith://<owner>/<repo>"

with mlflow.start_run():
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_artifact("model.pkl")
```

### Direct Repository Usage

```python
from plugin.cloudsmith_repository import CloudsmithArtifactRepository

repo = CloudsmithArtifactRepository("cloudsmith://<owner>/<repo>")
repo.log_artifact("model.pkl", "models/production")

for info in repo.list_artifacts("models"):
    print(info.path, info.file_size, info.is_dir)
```
### Example startup:

```bash
mlflow server \
  --host 127.0.0.1 \
  --port 5000 \
  --artifacts-destination cloudsmith://<CLOUDSMITH_NAMESPACE>/<CLOUDSMITH_REPO>
```


---

## URI Format

```
cloudsmith://<owner>/<repository>[/<path>]
```

**Examples:**

* `cloudsmith://my-org/ml-artifacts`
* `cloudsmith://my-org/ml-artifacts/experiments`

---

## Configuration

| Variable               | Description                                | Required |
| ---------------------- | ------------------------------------------ | -------- |
| `CLOUDSMITH_API_KEY`   | Cloudsmith API token                       | ✅        |
| `CLOUDSMITH_DEBUG`     | `true` / `false` to toggle verbose logging | ❌        |
| `MLFLOW_EXPERIMENT_ID` | Used for tagging                           | ❌        |
| `MLFLOW_RUN_ID`        | Used for tagging                           | ❌        |

---

## How It Works (Brief)

* Each MLflow artifact is uploaded as a **Cloudsmith RAW package** with preserved original filename and metadata.
* The plugin builds an **in-memory tree** of artifact paths and returns **only immediate children** for UI browsing.
* Packages are tagged for easy filtering:
  `mlflow`, `experiment-*`, `run-*`, `path-*` (slashes replaced with dashes).

---

## Artifact Representation & Tagging

**Example Run Context**

* `experiment_id`: `123`
* `run_id`: `0123456789abcdef0123456789abcdef`
* Files logged:

  * `models/model.pkl`
  * `conda.yaml`

**Package Details**

* **Name:** `mlflow-<base-filename>-<run_id_first8>-<timestamp>`
  e.g., `mlflow-model-01234567-1754914964`
* **Version:** `<experiment_id>+<run_id>`
  e.g., `123+0123456789abcdef0123456789abcdef`
* **Filename:** Original filename (e.g., `model.pkl`)
* **Description:**

  ```
  MLflow artifact: <artifact_path> (experiment: <experiment_id>, run: <run_id>)
  ```

  e.g., `MLflow artifact: models/model.pkl (experiment: 123, run: 0123456789abcdef0123456789abcdef)`
* **Tags:**

  * `mlflow`
  * `experiment-123`
  * `run-0123456789abcdef0123456789abcdef`
  * `path-models-model.pkl`

**Notes**

* Descriptions hold the authoritative artifact path for listing & downloads.
* `path-*` tags replace `/` with `-` for fallback reconstruction.
* **MLflow UI listing:**

  * `list_artifacts("")` → `[models/ (dir), conda.yaml]`
  * `list_artifacts("models")` → `[models/model.pkl]`

---

## Testing

```bash
pytest -q
```

### Integration Tests (Opt-in)

```bash
export CLOUDSMITH_RUN_INTEGRATION=1
export CLOUDSMITH_API_KEY=""      # required
export CLOUDSMITH_TEST_OWNER=""   # required
export CLOUDSMITH_TEST_REPO=""    # required

pytest -q
```

---

## Cleanup Script (Delete by Run/Experiment)

`scripts/cleanup_orphans.sh` deletes Cloudsmith RAW packages for a given run or experiment ID.
**No MLflow server is contacted.** Requires: `bash`, `curl`, `jq`.

**Environment Variables / Flags**

| Variable / Flag                     | Description                        | Required |
| ----------------------------------- | ---------------------------------- | -------- |
| `CLOUDSMITH_API_KEY`                | API key                            | ✅        |
| `CLOUDSMITH_OWNER`                  | Owner/org slug                     | ✅        |
| `CLOUDSMITH_REPO`                   | Repo slug                          | ✅        |
| `RUN_ID` / `--run-id`               | MLflow run ID                      | ❌        |
| `EXPERIMENT_ID` / `--experiment-id` | MLflow experiment ID               | ❌        |
| `CLEANUP_CONFIRM=1` / `--confirm`   | Perform deletion (dry-run default) | ❌        |

**Examples:**

```bash
# Dry-run: show packages for a run-id
CLOUDSMITH_API_KEY="" CLOUDSMITH_OWNER=myorg CLOUDSMITH_REPO=myrepo \
    scripts/cleanup_orphans.sh --run-id 0123456789abcdef0123456789abcdef

# Delete for a run-id (confirmation required)
CLOUDSMITH_API_KEY="" CLOUDSMITH_OWNER=myorg CLOUDSMITH_REPO=myrepo \
    scripts/cleanup_orphans.sh --run-id 0123456789abcdef0123456789abcdef --confirm

# Combine experiment-id + run-id
CLOUDSMITH_API_KEY="" CLOUDSMITH_OWNER=myorg CLOUDSMITH_REPO=myrepo \
    scripts/cleanup_orphans.sh --experiment-id 123 --run-id 0123456789abcdef0123456789abcdef --confirm
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING](CONTRIBUTING.md) for more details.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).
