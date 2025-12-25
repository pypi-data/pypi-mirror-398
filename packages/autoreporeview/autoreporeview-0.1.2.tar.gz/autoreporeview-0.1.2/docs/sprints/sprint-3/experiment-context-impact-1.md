<details>

<summary>Input Request</summary>

````
You are an AI assistant helping to summarize changes in a GitHub repository project written in Python.

Here is a git diff output showing the changes made in the codebase:

```
diff --git a/.github/workflows/on_release.yml b/.github/workflows/on_release.yml
index 4285487..eaba626 100644
--- a/.github/workflows/on_release.yml
+++ b/.github/workflows/on_release.yml
@@ -169,6 +169,31 @@ jobs:
           } >> "$GITHUB_OUTPUT"
           echo "cache_ref=${repo}:${latest_tag}" >> "$GITHUB_OUTPUT"
 
+      - name: Python setup
+        uses: actions/setup-python@v5
+        with:
+          python-version: '3.11.8'
+
+      - name: Bump version - packaging__.py
+        run: |
+          # Install required packages
+          pip install semver packaging
+
+          # Get version tag and remove 'v' prefix
+          version_tag=${{ github.event.release.tag_name }}
+          version_tag=${version_tag#v}
+
+          # Convert semver to PyPI version using the script
+          pypi_version=$(python semver2pypi.py $version_tag)
+
+          # Update only the __version__ in __packaging__.py
+          sed -i "s/__version__ = VERSION_STRING/__version__ = \"$pypi_version\"/" packages/__packaging__.py
+
+          # Print the result for verification
+          echo "Original version tag: $version_tag"
+          echo "PyPI version: $pypi_version"
+          cat packages/__packaging__.py
+
       - name: Build and push ${{ matrix.name }}
         uses: docker/build-push-action@v6
         with:
diff --git a/.github/workflows/pre-commit.yml b/.github/workflows/pre-commit.yml
index 117e479..fd6ad02 100644
--- a/.github/workflows/pre-commit.yml
+++ b/.github/workflows/pre-commit.yml
@@ -12,7 +12,7 @@ jobs:
     - uses: actions/checkout@v3
     - uses: actions/setup-python@v4
       with:
-        python-version: 3.x
+        python-version: 3.12.x
     - name: install pre-commit
       run: python -m pip install 'pre-commit<4'
     - name: show environment
diff --git a/packages/opal-common/opal_common/monitoring/apm.py b/packages/opal-common/opal_common/monitoring/apm.py
index 2d51d83..77f2b18 100644
--- a/packages/opal-common/opal_common/monitoring/apm.py
+++ b/packages/opal-common/opal_common/monitoring/apm.py
@@ -1,58 +1,69 @@
 import logging
-from typing import Optional
 from urllib.parse import urlparse
 
-from ddtrace import config, patch, tracer
-from ddtrace.trace import Span, TraceFilter
+from ddtrace import patch, tracer
+from ddtrace.trace import TraceFilter
 from loguru import logger
 
 
+class DropRootPathTraces(TraceFilter):
+    """TraceFilter that drops any trace whose root HTTP route/path is "/".
+
+    Per ddtrace docs:
+      - process_trace receives a list of spans (one trace)
+      - return None to drop it, or the (optionally modified) list to keep it
+    We examine only the root span (parent_id is None).
+    """
+
+    def process_trace(self, trace):
+        # Locate root span
+        root = next((s for s in trace if getattr(s, "parent_id", None) is None), None)
+        if root is None:
+            return trace  # Keep if we can't identify a root
+
+        # Prefer normalized route (framework-provided)
+        route = root.get_tag("http.route")
+        if route == "/":
+            return None
+
+        # Fallback: parse raw URL if present
+        url = root.get_tag("http.url")
+        if url:
+            try:
+                if urlparse(url).path == "/":
+                    return None
+            except Exception:
+                # Fail-open: keep the trace if parsing fails
+                pass
+
+        return trace
+
+
 def configure_apm(enable_apm: bool, service_name: str):
-    """Optionally enable datadog APM / profiler."""
-    if enable_apm:
-        logger.info("Enabling DataDog APM")
-        # logging.getLogger("ddtrace").propagate = False
-
-        class FilterRootPathTraces(TraceFilter):
-            def process_trace(self, trace: list[Span]) -> Optional[list[Span]]:
-                for span in trace:
-                    if span.parent_id is not None:
-                        return trace
-
-                    if url := span.get_tag("http.url"):
-                        parsed_url = urlparse(url)
-
-                        if parsed_url.path == "/":
-                            return None
-
-                return trace
-
-        patch(
-            fastapi=True,
-            redis=True,
-            asyncpg=True,
-            aiohttp=True,
-            loguru=True,
-        )
-        tracer.configure(
-            settings={
-                "FILTERS": [
-                    FilterRootPathTraces(),
-                ]
-            }
-        )
-
-    else:
-        logger.info("DataDog APM disabled")
-        # Note: In ddtrace v3.0.0+, the 'enabled' parameter is no longer supported
-        # APM should be disabled via environment variable DD_TRACE_ENABLED=false
-        # or by not patching any integrations at all
-        pass
+    """Enable Datadog APM and install the DropRootPathTraces filter."""
+    if not enable_apm:
+        logger.info("Datadog APM disabled")
+        return
+
+    logger.info("Enabling Datadog APM")
+
+    patch(
+        fastapi=True,
+        redis=True,
+        asyncpg=True,
+        aiohttp=True,
+        loguru=True,
+    )
+
+    tracer.configure(
+        trace_processors=[DropRootPathTraces()],
+    )
 
 
 def fix_ddtrace_logging():
+    """Reduce ddtrace logger verbosity and remove its handlers so our logging
+    setup controls output."""
     logging.getLogger("ddtrace").setLevel(logging.WARNING)
-
     ddtrace_logger = logging.getLogger("ddtrace")
-    for handler in ddtrace_logger.handlers:
+    for handler in list(ddtrace_logger.handlers):
         ddtrace_logger.removeHandler(handler)
diff --git a/scripts/start.sh b/scripts/start.sh
old mode 100755
new mode 100644
index 350c836..c147846
--- a/scripts/start.sh
+++ b/scripts/start.sh
@@ -11,8 +11,10 @@ if [[ -z "${OPAL_BROADCAST_URI}" && "${UVICORN_NUM_WORKERS}" != "1" ]]; then
 fi
 
 prefix=""
+
 # Start Gunicorn
-if [[ -z "${OPAL_ENABLE_DATADOG_APM}" && "${OPAL_ENABLE_DATADOG_APM}" = "true" ]]; then
+# Enable ddtrace if OPAL_ENABLE_DATADOG_APM is set and empty or "true"; unset disables it
+if [[ -n "${OPAL_ENABLE_DATADOG_APM+x}" && ( -z "${OPAL_ENABLE_DATADOG_APM}" || "${OPAL_ENABLE_DATADOG_APM}" = "true" ) ]]; then
 	prefix=ddtrace-run
 fi
 (set -x; exec $prefix gunicorn -b 0.0.0.0:${UVICORN_PORT} -k uvicorn.workers.UvicornWorker --workers=${UVICORN_NUM_WORKERS} -c ${GUNICORN_CONF} ${UVICORN_ASGI_APP} -t ${GUNICORN_TIMEOUT} --keep-alive ${GUNICORN_KEEP_ALIVE_TIMEOUT})
```

Please provide a clear and concise summary of the changes made, focusing on what was added, removed, or modified. Explain the purpose and impact of these changes as accurately as possible based only on this diff.
````


</details>

<details>

<summary>Summary output</summary>

```
Here is a summary of the changes made in the codebase:

The changes primarily focus on refining Datadog APM integration, updating Python versions in CI/CD workflows, and introducing a version bumping mechanism for releases.

### `a/.github/workflows/on_release.yml`

*   **Added Version Bumping for Releases**:
    *   A new step "Python setup" was added to install Python `3.11.8`.
    *   Another new step, "Bump version - packaging__.py", was added to automatically update the project's version during a release.
    *   This step installs `semver` and `packaging` Python libraries.
    *   It extracts the release tag (e.g., `v1.2.3`), removes the 'v' prefix, and converts it to a PyPI-compatible version using a `semver2pypi.py` script (not provided in this diff).
    *   Finally, it uses `sed` to update the `__version__` string in `packages/__packaging__.py` to reflect the new PyPI-compatible version.

### `a/.github/workflows/pre-commit.yml`

*   **Updated Python Version**:
    *   The `python-version` used for the pre-commit workflow was updated from `3.x` to `3.12.x`.

### `a/packages/opal-common/opal_common/monitoring/apm.py`

*   **Refactored Datadog APM Trace Filtering**:
    *   The `ddtrace.config` import was removed.
    *   The former `FilterRootPathTraces` nested class within `configure_apm` was replaced by a new, standalone class `DropRootPathTraces`.
    *   `DropRootPathTraces` now provides a more robust mechanism to drop traces whose root HTTP route or URL path is `/`. It first checks `http.route` and then falls back to parsing `http.url`.
    *   The `configure_apm` function now uses `tracer.configure(trace_processors=[DropRootPathTraces()])` instead of `settings={"FILTERS": [...]}`.
    *   The `fix_ddtrace_logging` function received a docstring and was slightly modified to iterate over a `list` copy of `ddtrace_logger.handlers` when removing them, which is a safer practice.

### `a/scripts/start.sh`

*   **Changed File Permissions**:
    *   The file mode changed from `100755` (executable) to `100644` (regular file). This might impact how the script is executed if it relies on its executable bit.
*   **Modified Datadog APM Enablement Logic**:
    *   The conditional logic for enabling `ddtrace-run` was made more robust.
    *   Previously, APM was enabled if `OPAL_ENABLE_DATADOG_APM` was unset *and* equal to `"true"` (a contradictory condition).
    *   The new condition (`[[ -n "${OPAL_ENABLE_DATADOG_APM+x}" && ( -z "${OPAL_ENABLE_DATADOG_APM}" || "${OPAL_ENABLE_DATADOG_APM}" = "true" ) ]]`) now correctly enables APM if the `OPAL_ENABLE_DATADOG_APM` environment variable is explicitly set (either to an empty string or `"true"`). If it's unset or set to any other value (e.g., `"false"`), APM will not be enabled via the `ddtrace-run` prefix.
```

</details>