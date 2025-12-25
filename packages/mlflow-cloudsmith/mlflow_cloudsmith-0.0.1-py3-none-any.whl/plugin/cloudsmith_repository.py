# Copyright 2025 Cloudsmith Ltd
"""
Cloudsmith MLflow plugin - Main repository implementation.

This module implements the CloudsmithArtifactRepository class that provides
MLflow artifact storage capabilities using Cloudsmith RAW packages.
"""

import os
import posixpath
import requests
import hashlib
import time
import re
from urllib.parse import urlparse
from typing import List, Optional, Tuple
import logging

from mlflow.store.artifact.artifact_repo import (
    ArtifactRepository,
    verify_artifact_path,
)
from mlflow.entities import FileInfo
from mlflow.utils.file_utils import relative_path_to_artifact_path

_logger = logging.getLogger(__name__)

VERSION = "0.1.0"
CLOUDSMITH_API_BASE = "https://api.cloudsmith.io/v1"
CHUNK_SIZE = 100 * 1024 * 1024  # 100MB threshold

class CloudsmithArtifactRepository(ArtifactRepository):
    """
    Cloudsmith artifact repository for storing MLflow artifacts as
    RAW packages.

    This implementation stores artifacts as RAW packages in Cloudsmith,
    using tags to track MLflow experiment and run information.
    """

    is_plugin = True

    def __init__(self, artifact_uri, tracking_uri=None):
        """
        Initialize the Cloudsmith artifact repository.

        Args:
            artifact_uri: URI in format
                cloudsmith://<owner>/<repository>[/<path>]
            tracking_uri: MLflow tracking URI (unused but required by
                MLflow 3.x)
        """
        super(CloudsmithArtifactRepository, self).__init__(artifact_uri)

        self.debug_mode = os.getenv("CLOUDSMITH_DEBUG", "false").lower() == "true"
        # Allow disabling pagination for troubleshooting via env var
        self.disable_pagination = (
            os.getenv("CLOUDSMITH_DISABLE_PAGINATION", "true").lower() == "true"
        )
        self.api_key = os.getenv("CLOUDSMITH_API_KEY")

        # Ensure logger outputs when debug is enabled
        if not _logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            _logger.addHandler(handler)
        _logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        _logger.info("Cloudsmith: Initializing with URI: %s", artifact_uri)

        if not self.api_key:
            raise ValueError("CLOUDSMITH_API_KEY environment variable must be set")

        # Parse the URI
        self.owner, self.repository, self.base_path = self._parse_uri(artifact_uri)

        _logger.debug(
            "Cloudsmith: owner=%s, repository=%s, base_path=%s",
            self.owner,
            self.repository,
            self.base_path,
        )

    @staticmethod
    def _parse_uri(uri: str) -> tuple:
        """
        Parse a Cloudsmith URI into its components.

        Args:
            uri: URI in format cloudsmith://<owner>/<repository>[/<path>]

        Returns:
            tuple: (owner, repository, base_path)
        """
        parsed = urlparse(uri)

        if parsed.scheme != "cloudsmith":
            raise ValueError(
                f"Invalid Cloudsmith URI scheme: {parsed.scheme}. "
                f"Expected 'cloudsmith'"
            )

        if not parsed.netloc:
            raise ValueError(
                (
                    f"Invalid Cloudsmith URI: {uri}. Must include owner and "
                    f"repository"
                )
            )

        # Extract owner and repo
        owner = parsed.netloc
        path_parts = parsed.path.strip("/").split("/") if parsed.path else []
        repository = path_parts[0] if len(path_parts) > 0 else None
        base_path = "/".join(path_parts[1:]) if len(path_parts) > 1 else ""

        if not owner or not repository:
            raise ValueError(
                f"Invalid Cloudsmith URI: {uri}. Must specify both owner and "
                f"repository"
            )
        return owner, repository, base_path

    def _get_headers(self) -> dict:
        """Get HTTP headers for Cloudsmith API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"mlflow-cloudsmith-plugin/{VERSION}",
        }

    # --- Helpers for context inference and pagination ---
    def _infer_mlflow_context(
        self, desired_prefix: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Infer experiment_id and run_id from base_path or a desired prefix.
        Prefer parsing '<run_id>/artifacts' (standard MLflow layout). We do not
        guess experiment_id unless it is clearly encoded in the path.
        """
        candidate = (desired_prefix or self.base_path or "").strip("/")
        if not candidate:
            return None, None
        parts = [p for p in candidate.split("/") if p]
        exp_id: Optional[str] = None
        run_id: Optional[str] = None

        if "artifacts" in parts:
            try:
                idx = parts.index("artifacts")
                # Standard MLflow: '<run_id>/artifacts' -> take segment
                # before it
                if idx >= 1:
                    run_id = parts[idx - 1]
                # Some stores might encode '<exp>/<run>/artifacts'
                if idx >= 2 and not exp_id:
                    # Only set if present; otherwise leave None
                    exp_id = parts[idx - 2]
            except ValueError:
                pass
        else:
            # No explicit 'artifacts' segment; if a single segment remains,
            # treat it as run_id; otherwise, avoid guessing.
            if len(parts) == 1:
                run_id = parts[0]

        return exp_id, run_id

    def _paginate_packages(self, query: Optional[str]) -> list:
        """Fetch Cloudsmith packages for the given query.
        Single-page fetch (pagination disabled by default) to simplify
        and avoid Cloudsmith search quirks observed in practice.
        """
        url = f"{CLOUDSMITH_API_BASE}/packages/{self.owner}/" f"{self.repository}/"
        # Build a sequence of query attempts: initial -> format-only ->
        # no query
        attempts: List[Optional[str]] = [query]
        if query and "format:raw" not in query:
            attempts.append("format:raw")
        if "format:raw" not in attempts:
            attempts.append("format:raw")
        attempts.append(None)

        last_error: Optional[str] = None
        for attempt in attempts:
            params = {"page": 1, "page_size": 250}
            if attempt:
                params["query"] = attempt
            try:
                _logger.debug(
                    "Cloudsmith: list packages (single page), query=%r", attempt
                )
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                )
                if response.status_code != 200:
                    last_error = response.text
                    _logger.debug(
                        "Cloudsmith: list failed for query=%r: %s",
                        attempt,
                        last_error,
                    )
                    continue
                packages = response.json()
                if not isinstance(packages, list):
                    _logger.debug(
                        "Cloudsmith: unexpected payload for query=%r: %s",
                        attempt,
                        str(packages)[:200],
                    )
                    continue
                _logger.debug(
                    "Cloudsmith: fetched %d packages for query=%r",
                    len(packages),
                    attempt,
                )
                return packages
            except (requests.RequestException, ValueError) as e:
                last_error = str(e)
                _logger.debug(
                    "Cloudsmith: list error for query=%r", attempt, exc_info=True
                )

        raise RuntimeError(
            "Failed to list packages. Last error: %s" % (last_error or "unknown error")
        )

    def _get_package_tags(self, package: dict) -> List[str]:
        """
        Return a flat list of tag strings from a Cloudsmith package payload.
        """
        tags = []
        raw = package.get("tags") or package.get("tags_immutable") or {}
        if isinstance(raw, dict):
            for _, vals in raw.items():
                if isinstance(vals, list):
                    tags.extend([v for v in vals if isinstance(v, str)])
        elif isinstance(raw, list):
            tags.extend([v for v in raw if isinstance(v, str)])
        return tags

    def _has_required_tags(
        self,
        package: dict,
        required_tags: List[str],
    ) -> bool:
        tags = self._get_package_tags(package)
        return all(t in tags for t in required_tags)

    def _generate_package_metadata(self, artifact_path: str, local_file: str) -> dict:
        """
        Generate metadata for the RAW package based on MLflow context.

        Args:
            artifact_path: Path of the artifact within MLflow
            local_file: Local file path

        Returns:
            dict: Package metadata
        """
        # Try to extract MLflow context from environment or artifact path
        experiment_id = os.getenv("MLFLOW_EXPERIMENT_ID") or ""
        run_id = os.getenv("MLFLOW_RUN_ID") or ""

        # If env not set, infer from artifact_path/base_path
        if not experiment_id or not run_id:
            # artifact_path we pass in already includes base_path
            inferred_exp, inferred_run = self._infer_mlflow_context(artifact_path)
            if inferred_exp and not experiment_id:
                experiment_id = inferred_exp
            if inferred_run and not run_id:
                run_id = inferred_run

        if not experiment_id:
            experiment_id = "unknown"
        if not run_id:
            run_id = "unknown"

        # Generate package name based on file and context
        filename = os.path.basename(local_file)
        base_name = os.path.splitext(filename)[0]

        # Create a unique package name with timestamp to avoid conflicts
        timestamp = str(int(time.time()))
        package_name = f"mlflow-{base_name}-{run_id[:8]}-{timestamp}"

        # Create description with MLflow metadata
        description = (
            f"MLflow artifact: {artifact_path or filename} "
            f"(experiment: {experiment_id}, run: {run_id})"
        )

        # Create tags as a comma-separated string
        # Cloudsmith will parse this into the tags_immutable.info array
        tags = [
            "mlflow",
            f"experiment-{experiment_id}",
            f"run-{run_id}",
        ]
        if artifact_path:
            # Clean the artifact path for use in tags
            clean_path = artifact_path.replace("/", "-").replace("\\", "-")
            tags.append(f"path-{clean_path}")

        return {
            "name": package_name,
            # Prefer version as experiment_id+run_id when both are available
            "version": (
                f"{experiment_id}+{run_id}" if experiment_id and run_id else "1.0.0"
            ),
            "description": description,
            "tags": ",".join(tags),
        }

    def _calculate_checksums(self, file_path: str) -> tuple:
        """
        Calculate MD5 and SHA256 checksums for a file.

        Args:
            file_path: Path to the file

        Returns:
            tuple: (md5_hash, sha256_hash)
        """
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)

        return md5_hash.hexdigest(), sha256_hash.hexdigest()

    def _wait_for_package_sync(
        self, package_identifier: str, max_wait_time: int = 60
    ) -> bool:
        """
        Wait for a package to be synchronized and available for download.

        Args:
            package_identifier: Package identifier
            max_wait_time: Maximum time to wait in seconds

        Returns:
            bool: True if package is synchronized, False if timeout
        """
        _logger.debug("Cloudsmith: Waiting for package sync: %s", package_identifier)

        wait_interval = 2.0
        total_wait_interval = max(1.0, wait_interval)
        last_progress = 0
        first = True
        start = time.time()

        def _progress(payload: dict) -> int:
            for key in ("sync_progress", "progress", "percentage"):
                val = payload.get(key)
                if isinstance(val, (int, float)):
                    try:
                        iv = int(val)
                        if 0 <= iv <= 100:
                            return max(1, iv)
                    except (TypeError, ValueError):
                        pass
            return 0

        while True:
            elapsed = time.time() - start
            if elapsed >= max_wait_time:
                _logger.warning(
                    "Cloudsmith: Package sync timeout after %.1fs: %s",
                    elapsed,
                    package_identifier,
                )
                return False

            try:
                status_url = (
                    f"{CLOUDSMITH_API_BASE}/packages/"
                    f"{self.owner}/{self.repository}/"
                    f"{package_identifier}/status/"
                )
                resp = requests.get(status_url, headers=self._get_headers())
                if resp.status_code != 200:
                    if resp.status_code == 404:
                        _logger.debug(
                            "Cloudsmith: status 404 (not ready) for %s",
                            package_identifier,
                        )
                    else:
                        _logger.debug(
                            "Cloudsmith: status %s polling %s",
                            resp.status_code,
                            package_identifier,
                        )
                else:
                    data = resp.json()
                    ok = bool(data.get("is_sync_completed"))
                    failed = bool(data.get("is_sync_failed"))
                    prog = _progress(data)
                    if prog > last_progress:
                        delta = prog - last_progress
                        last_progress = prog
                        _logger.debug(
                            "Cloudsmith: sync progress +%d -> %d%% (%s)",
                            delta,
                            prog,
                            package_identifier,
                        )
                    if ok:
                        _logger.debug(
                            "Cloudsmith: Package synchronized in %.2fs (%d%%): %s",
                            elapsed,
                            prog,
                            package_identifier,
                        )
                        return True
                    if failed:
                        reason = data.get("sync_failure_reason") or data.get("reason")
                        _logger.warning(
                            "Cloudsmith: Package sync failed (%s): %s",
                            package_identifier,
                            reason or "no reason",
                        )
                        return False
            except requests.RequestException as e:
                _logger.debug(
                    "Cloudsmith: transient HTTP error waiting for %s: %s",
                    package_identifier,
                    e,
                )
            except ValueError as e:
                _logger.debug(
                    "Cloudsmith: JSON parse error waiting for %s: %s",
                    package_identifier,
                    e,
                )

            if first:
                first = False
            else:
                time.sleep(total_wait_interval)
                total_wait_interval = min(300.0, total_wait_interval + wait_interval)

    def _upload_file_to_cloudsmith(
            self, local_file: str, artifact_path: Optional[str] = None
        ) -> str:
            """
            Upload a file to Cloudsmith as a RAW package.

            Args:
                local_file: Path to the local file to upload
                artifact_path: MLflow artifact path

            Returns:
                str: Package identifier
            """
            _logger.info("Cloudsmith: Uploading %s as %s", local_file, artifact_path)

            filename = os.path.basename(local_file)
            file_size = os.path.getsize(local_file)
            md5_hash, sha256_hash = self._calculate_checksums(local_file)
            is_multi = file_size > CHUNK_SIZE

            # 1. Request upload
            upload_req = {
                "filename": filename,
                "md5_checksum": md5_hash,
                "sha256_checksum": sha256_hash,
            }
            if is_multi:
                upload_req["method"] = "put_parts"

            files_url = f"{CLOUDSMITH_API_BASE}/files/{self.owner}/{self.repository}/"
            resp = requests.post(files_url, headers=self._get_headers(), json=upload_req)
            if resp.status_code != 202:
                raise RuntimeError(f"Failed to request upload URL: {resp.text}")
            data = resp.json()
            upload_url = data["upload_url"]
            upload_fields = data.get("upload_fields", {})
            file_id = data["identifier"]
            _logger.debug("Cloudsmith: Upload prepared id=%s multi=%s", file_id, is_multi)

            # 2. Upload file (single vs multi)
            if is_multi:
                part = 1
                with open(local_file, "rb") as fh:
                    while True:
                        chunk = fh.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        r = requests.put(
                            upload_url,
                            headers={"X-Api-Key": self.api_key},
                            params={"upload_id": file_id, "part_number": part},
                            data=chunk,
                        )
                        if r.status_code not in (200, 201, 204):
                            raise RuntimeError(
                                f"Failed uploading part {part}: {r.status_code} {r.text[:160]}"
                            )
                        part += 1
                complete_url = (
                    f"{CLOUDSMITH_API_BASE}/files/{self.owner}/{self.repository}/{file_id}/complete/"
                )
                comp_payload = {"upload_id": file_id, "complete": True}
                c_resp = requests.post(
                    complete_url, headers=self._get_headers(), json=comp_payload
                )
                if c_resp.status_code not in (200, 201, 202):
                    raise RuntimeError(
                        f"Failed to complete multi-part upload: {c_resp.status_code} {c_resp.text[:160]}"
                    )
                _logger.debug("Cloudsmith: multi-part upload complete id=%s", file_id)
            else:
                with open(local_file, "rb") as fh:
                    files = {"file": (filename, fh, "application/octet-stream")}
                    u_resp = requests.post(
                        upload_url, data=upload_fields, files=files
                    )
                if u_resp.status_code not in (200, 201, 204):
                    raise RuntimeError(
                        f"Failed to upload file: {u_resp.status_code} {u_resp.text[:160]}"
                    )

            # 3. Create package
            meta = self._generate_package_metadata(artifact_path, local_file)
            pkg_payload = {"package_file": file_id, **meta}
            raw_url = (
                f"{CLOUDSMITH_API_BASE}/packages/{self.owner}/{self.repository}/upload/raw/"
            )
            p_resp = requests.post(raw_url, headers=self._get_headers(), json=pkg_payload)
            if p_resp.status_code != 201:
                raise RuntimeError(
                    f"Failed to create RAW package: {p_resp.status_code} {p_resp.text[:200]}"
                )
            pkg = p_resp.json()
            identifier = pkg["identifier_perm"]
            _logger.debug("Cloudsmith: Created package %s", identifier)

            # 4. Wait for sync
            self._wait_for_package_sync(identifier)
            return identifier

    def log_artifact(self, local_file: str, artifact_path: Optional[str] = None):
        """
        Log a single artifact to Cloudsmith.

        Args:
            local_file: Path to the local file to upload
            artifact_path: Optional path within the artifact store
        """
        _logger.debug("Cloudsmith: log_artifact(%s, %s)", local_file, artifact_path)

        verify_artifact_path(artifact_path)

        # Construct the full artifact path (include base_path so list filters
        # work)
        if artifact_path:
            full_path = posixpath.join(
                self.base_path, artifact_path, os.path.basename(local_file)
            )
        else:
            full_path = posixpath.join(self.base_path, os.path.basename(local_file))

        self._upload_file_to_cloudsmith(local_file, full_path)

    def log_artifacts(self, local_dir: str, artifact_path: Optional[str] = None):
        """
        Log multiple artifacts from a directory to Cloudsmith.

        Args:
            local_dir: Path to the local directory containing artifacts
            artifact_path: Optional path within the artifact store
        """
        _logger.debug("Cloudsmith: log_artifacts(%s, %s)", local_dir, artifact_path)

        verify_artifact_path(artifact_path)
        local_dir = os.path.abspath(local_dir)

        for root, _, filenames in os.walk(local_dir):
            for filename in filenames:
                local_file_path = os.path.join(root, filename)

                # Calculate relative path from local_dir
                rel_path = os.path.relpath(local_file_path, local_dir)
                rel_path = relative_path_to_artifact_path(rel_path)

                # Construct artifact path (include base_path so list filters
                # work)
                if artifact_path:
                    full_artifact_path = posixpath.join(
                        self.base_path, artifact_path, rel_path
                    )
                else:
                    full_artifact_path = posixpath.join(self.base_path, rel_path)

                self._upload_file_to_cloudsmith(local_file_path, full_artifact_path)

    def list_artifacts(self, path: Optional[str] = None) -> List[FileInfo]:
        """
        List artifacts stored in Cloudsmith.
        Returns only the immediate children (dirs and files) at the
        requested path, building results from a full preloaded tree of all
        artifacts for the run.
        """
        _logger.debug("Cloudsmith: list_artifacts(%s)", path)

        # Normalize base and requested paths
        base_prefix = self.base_path.strip("/") if self.base_path else ""
        requested_path = (path or "").strip("/")

        # Infer experiment/run for strong filtering
        exp_guess, run_guess = self._infer_mlflow_context(base_prefix or self.base_path)

        def _is_valid_experiment_id(x: Optional[str]) -> bool:
            return bool(x and re.fullmatch(r"\d+", x))

        def _is_valid_run_id(x: Optional[str]) -> bool:
            return bool(x and re.fullmatch(r"[0-9a-f]{32}", x))

        exp_id = exp_guess if _is_valid_experiment_id(exp_guess) else None
        run_id = run_guess if _is_valid_run_id(run_guess) else None

        # Query for all mlflow RAW packages for this run
        q_parts: List[str] = ["format:raw", "tag:mlflow"]
        if run_id:
            q_parts.append(f"tag:run-{run_id}")
        if exp_id and run_id:
            q_parts.insert(
                1,
                f'VERSION:"{exp_id}+{run_id}"'.replace("VERSION", "version"),
            )
            q_parts.append(f"tag:experiment-{exp_id}")
        query = " and ".join(q_parts)

        _logger.debug(
            (
                "Cloudsmith: base_prefix=%r, requested_path=%r, "
                "exp_id=%r, run_id=%r, query=%r"
            ),
            base_prefix,
            requested_path,
            exp_id,
            run_id,
            query,
        )

        packages = self._paginate_packages(query)
        _logger.debug("Cloudsmith: fetched %d packages", len(packages))

        # Helper: choose package file size robustly
        def _pkg_size(pkg: dict) -> int:
            size = pkg.get("size") or pkg.get("file_size")
            if not size:
                try:
                    files = pkg.get("files") or []
                    for f in files:
                        if f.get("is_primary"):
                            return int(f.get("size") or 0)
                    if files:
                        return int(files[0].get("size") or 0)
                except (KeyError, ValueError, TypeError):
                    pass
            try:
                return int(size or 0)
            except (TypeError, ValueError):
                return 0

        # Helper: normalize an absolute artifact path to repo-root relative
        def _to_relative(artifact_path_abs: str) -> str:
            p = (artifact_path_abs or "").strip("/")
            if not p:
                return ""
            # Prefer exact base prefix stripping
            if base_prefix and (p == base_prefix or p.startswith(base_prefix + "/")):
                rel = p[len(base_prefix) :].lstrip("/")
                return rel
            # Common MLflow layout: <run_id>/artifacts/<...>
            if run_id and p.startswith(f"{run_id}/artifacts/"):
                prefix = f"{run_id}/artifacts/"
                return p[len(prefix) :]
            # If path starts with 'artifacts/' also strip it
            if p.startswith("artifacts/"):
                return p[len("artifacts/") :]
            # Otherwise, treat as already relative to root
            return p

        # Build a complete in-memory tree of all artifacts
        # Node shape: { 'dirs': {name: node}, 'files': {name: size} }
        def _new_node():
            return {"dirs": {}, "files": {}}

        tree = _new_node()
        unique_files = set()

        for pkg in packages:
            ap = self._extract_artifact_path_from_package(pkg)
            if not ap:
                continue
            abs_path = ap.strip("/")
            rel_path = _to_relative(abs_path)
            if not rel_path:
                continue
            # De-dup on full relative path (files only)
            size = _pkg_size(pkg)
            if (rel_path, size) in unique_files:
                continue
            unique_files.add((rel_path, size))

            # Insert into tree
            parts = [p for p in rel_path.split("/") if p]
            if not parts:
                continue
            cur = tree
            for seg in parts[:-1]:
                cur = cur["dirs"].setdefault(seg, _new_node())
            cur["files"][parts[-1]] = size

        # Navigate to the requested node
        node = tree
        if requested_path:
            for seg in [p for p in requested_path.split("/") if p]:
                if seg in node["dirs"]:
                    node = node["dirs"][seg]
                else:
                    # Path doesn't exist
                    _logger.debug(
                        "Cloudsmith: requested path %r not found in tree",
                        requested_path,
                    )
                    return []

        # Materialize immediate children as FileInfo
        results: List[FileInfo] = []
        prefix = requested_path if requested_path else ""

        # Directories first (sorted)
        for name in sorted(node["dirs"].keys()):
            child_path = posixpath.join(prefix, name) if prefix else name
            results.append(FileInfo(path=child_path, is_dir=True, file_size=0))

        # Files (sorted)
        for name in sorted(node["files"].keys()):
            child_path = posixpath.join(prefix, name) if prefix else name
            results.append(
                FileInfo(
                    path=child_path,
                    is_dir=False,
                    file_size=int(node["files"][name] or 0),
                )
            )

        _logger.debug(
            "Cloudsmith: list_artifacts -> %d items for path=%r",
            len(results),
            path,
        )
        return results

    def _extract_artifact_path_from_package(self, package: dict) -> Optional[str]:
        """Extract the original artifact path from package metadata.
        Prefers description (exact path), falls back to 'path-' tags,
        then filename.
        """
        description = package.get("description", "") or ""
        if "MLflow artifact:" in description:
            try:
                part = description.split("MLflow artifact:", 1)[1]
                artifact_part = part.split("(", 1)[0].strip()
                if artifact_part:
                    return artifact_part
            except Exception:
                pass

        # Fallback to tags structure (dict or list)
        raw_tags = package.get("tags") or package.get("tags_immutable") or {}
        if isinstance(raw_tags, dict):
            info_tags = raw_tags.get("info", []) or []
        elif isinstance(raw_tags, list):
            info_tags = raw_tags
        else:
            info_tags = []
        for tag in info_tags:
            if isinstance(tag, str) and tag.startswith("path-"):
                # More careful path reconstruction from tags
                path_part = tag[5:]
                # Convert back from tag format (dashes) to path format
                # But be careful about legitimate dashes in filenames
                return path_part.replace("-", "/")

        # Last resort: filename
        filename = package.get("filename")
        if filename:
            return filename
        return None

    def _download_file(self, remote_file_path: str, local_path: str):
        """
        Download a file from Cloudsmith to local storage.
        """
        _logger.debug(
            "Cloudsmith: _download_file(%s, %s)", remote_file_path, local_path
        )

        # Fetch packages with strict per-run query when possible
        exp_guess, run_guess = self._infer_mlflow_context(self.base_path)

        def _is_valid_experiment_id(x: Optional[str]) -> bool:
            return bool(x and re.fullmatch(r"\d+", x))

        def _is_valid_run_id(x: Optional[str]) -> bool:
            return bool(x and re.fullmatch(r"[0-9a-f]{32}", x))

        exp_id = exp_guess if _is_valid_experiment_id(exp_guess) else None
        run_id = run_guess if _is_valid_run_id(run_guess) else None

        q_parts: List[str] = ["format:raw", "tag:mlflow"]
        if run_id:
            q_parts.append(f"tag:run-{run_id}")
        if exp_id and run_id:
            q_parts.insert(1, f'version:"{exp_id}+{run_id}"')
            q_parts.append(f"tag:experiment-{exp_id}")
        q = " and ".join(q_parts)
        packages = self._paginate_packages(q)
        target_package = None

        # Construct the expected full path as stored in Cloudsmith
        # For files at the artifact root level, don't prepend base_path
        if self.base_path and self.base_path.strip("/"):
            expected_full_path = posixpath.join(
                self.base_path.strip("/"), remote_file_path.strip("/")
            ).strip("/")
        else:
            expected_full_path = remote_file_path.strip("/")

        _logger.debug("Cloudsmith: Looking for file with path: %s", expected_full_path)
        _logger.debug(
            "Cloudsmith: Base path: %s, Remote path: %s",
            self.base_path,
            remote_file_path,
        )

        for package in packages:
            description = package.get("description", "") or ""
            name = package.get("name", "") or ""
            is_mlflow = description.startswith("MLflow artifact:") or name.startswith(
                "mlflow-"
            )
            if not is_mlflow:
                continue

            # Extract path from description (most reliable)
            desc_path = None
            if "MLflow artifact:" in description:
                try:
                    desc_path = (
                        description.split("MLflow artifact:", 1)[1]
                        .split("(", 1)[0]
                        .strip()
                    )
                except (IndexError, ValueError):
                    desc_path = None

            _logger.debug(
                "Cloudsmith: Checking package %s with desc_path=%s",
                package.get("name", "unknown"),
                desc_path,
            )

            # Try multiple path matching strategies
            possible_paths = [expected_full_path]

            # Also try just the filename for root-level files
            if "/" not in remote_file_path.strip("/"):
                possible_paths.append(remote_file_path.strip("/"))

            # Try without base_path prefix
            if self.base_path and remote_file_path.strip("/"):
                possible_paths.append(remote_file_path.strip("/"))

            # Check description path against all possibilities
            if desc_path:
                desc_path_clean = desc_path.strip("/")
                for possible_path in possible_paths:
                    if desc_path_clean == possible_path:
                        target_package = package
                        _logger.debug(
                            "Cloudsmith: Found match via description path: %s",
                            desc_path_clean,
                        )
                        break
                if target_package:
                    break

            # Fallback to 'path-' tags
            for tag in self._get_package_tags(package):
                if tag.startswith("path-"):
                    tag_path = tag[5:].replace("-", "/").strip("/")
                    for possible_path in possible_paths:
                        if tag_path == possible_path:
                            target_package = package
                            _logger.debug(
                                "Cloudsmith: Found match via tag path: %s",
                                tag_path,
                            )
                            break
                    if target_package:
                        break
            if target_package:
                break

            # Fallback to filename match for simple cases
            filename = package.get("filename", "")
            if filename == os.path.basename(remote_file_path):
                target_package = package
                _logger.debug("Cloudsmith: Found match via filename: %s", filename)
                break

        if not target_package:
            _logger.debug(
                "Cloudsmith: No package found for path: %s", expected_full_path
            )
            _logger.debug("Cloudsmith: Available packages:")
            for pkg in packages[:5]:  # Show first 5 packages for debugging
                desc = pkg.get("description", "")
                desc_path = None
                if "MLflow artifact:" in desc:
                    try:
                        desc_path = (
                            desc.split("MLflow artifact:", 1)[1]
                            .split("(", 1)[0]
                            .strip()
                        )
                    except (IndexError, ValueError):
                        pass
                _logger.debug(
                    "  - %s: %s",
                    pkg.get("name", "unknown"),
                    desc_path,
                )
            raise FileNotFoundError(f"Artifact not found: {remote_file_path}")

        cdn_url = target_package.get("cdn_url") or target_package.get("download_url")
        if not cdn_url:
            raise RuntimeError(f"No download URL available for {remote_file_path}")
        _logger.info("Cloudsmith: Downloading from %s", cdn_url)

        # Use authentication for private repositories
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(cdn_url, stream=True, headers=headers)
        _logger.debug("Cloudsmith: Response status: %s", response.status_code)
        _logger.debug("Cloudsmith: Response headers: %s", dict(response.headers))

        if response.status_code != 200:
            error_msg = (
                f"HTTP {response.status_code}: {response.text[:500]}"
                if response.text
                else f"HTTP {response.status_code}: No response body"
            )
            raise RuntimeError(f"Failed to download file: {error_msg}")

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        _logger.debug("Cloudsmith: Download complete: %s", local_path)

    def _path_has_prefix(self, path: str, prefix: str) -> bool:
        """Return True if path equals prefix or starts with prefix + '/'."""
        if not path:
            return False
        if not prefix:
            return True
        p = path.strip("/")
        pr = prefix.strip("/")
        return p == pr or p.startswith(pr + "/")

    def _strip_prefix(self, path: str, prefix: str) -> str:
        """Remove prefix from path if present and return the remainder.
        If path equals prefix, returns an empty string.
        """
        if not path or not prefix:
            return path or ""
        p = path.strip("/")
        pr = prefix.strip("/")
        if p == pr:
            return ""
        if p.startswith(pr + "/"):
            return p[len(pr) + 1 :]
        return path

    def download_artifacts(
        self,
        artifact_path: Optional[str] = None,
        dst_path: Optional[str] = None,
    ) -> str:
        """
        Download artifacts from Cloudsmith to a local directory.

        Args:
            artifact_path: Path of the artifact to download
                (relative to artifact root)
            dst_path: Local path to download to. If None, creates a
                temporary directory.

        Returns:
            str: Local path where artifacts were downloaded.
            For single files, returns the file path.
            For directories, returns the directory path.
        """
        _logger.debug("Cloudsmith: download_artifacts(%s, %s)", artifact_path, dst_path)

        # Use artifact_path or default to empty string (root)
        artifact_path = artifact_path or ""

        # If dst_path is None, create a temp directory
        if dst_path is None:
            import tempfile

            dst_path = tempfile.mkdtemp()

        # Ensure dst_path exists
        os.makedirs(dst_path, exist_ok=True)

        # Check if this is a directory by trying to list its contents
        artifacts = self.list_artifacts(artifact_path)

        if not artifacts and artifact_path:
            # This might be a single file, try to download it directly
            try:
                # Create the destination path preserving the artifact structure
                if artifact_path:
                    local_dest_path = os.path.join(dst_path, artifact_path)
                    os.makedirs(os.path.dirname(local_dest_path), exist_ok=True)
                    self._download_file(artifact_path, local_dest_path)
                    return local_dest_path
                else:
                    # Should not happen but handle gracefully
                    return dst_path
            except FileNotFoundError:
                # Not a file either, return empty directory
                return (
                    os.path.join(dst_path, artifact_path) if artifact_path else dst_path
                )

        # Download each artifact
        for artifact in artifacts:
            if artifact.is_dir:
                # Recursively download directory contents
                sub_path = (
                    posixpath.join(artifact_path, artifact.path)
                    if artifact_path
                    else artifact.path
                )
                sub_dst = os.path.join(dst_path, artifact.path)
                self.download_artifacts(sub_path, sub_dst)
            else:
                # Download file
                remote_path = (
                    posixpath.join(artifact_path, artifact.path)
                    if artifact_path
                    else artifact.path
                )
                local_file = os.path.join(dst_path, artifact.path)
                os.makedirs(os.path.dirname(local_file), exist_ok=True)
                self._download_file(remote_path, local_file)

        # Follow MLflow's pattern: return dst_path/artifact_path
        # This ensures the returned path points to where the artifact content
        # is located
        return os.path.join(dst_path, artifact_path) if artifact_path else dst_path
