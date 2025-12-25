<details>

<summary>Input Request</summary>

````
You are an AI assistant helping to summarize changes in a GitHub repository project written in Python. The repository URL is: https://github.com/permitio/opal

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

Please provide a clear and concise summary of the changes made, focusing on what was added, removed, or modified. Explain the purpose and impact of these changes as accurately as possible based only on this diff and repository URL.
````

</details>

<details>

<summary>Summary output</summary>

```
This diff summarizes changes in the `permitio/opal` GitHub repository, focusing on CI/CD pipeline improvements, Datadog APM configuration, and Python version updates.

Here's a breakdown of the changes:

### 1. `.github/workflows/on_release.yml` (CI/CD Workflow)

*   **Added Version Bumping for PyPI:** A new step has been introduced to the release workflow (`on_release.yml`).
    *   It sets up Python 3.11.8.
    *   Installs `semver` and `packaging` libraries.
    *   Uses a script named `semver2pypi.py` (not included in this diff but inferred from `run` command) to convert the Git release tag (e.g., `v1.2.3`) into a PyPI-compatible version string (e.g., `1.2.3`).
    *   This PyPI version is then used to update the `__version__` string in `packages/__packaging__.py` using a `sed` command.
    *   **Purpose:** This change automates the process of correctly setting the package version specifically for PyPI releases, ensuring that the package metadata reflects the actual release version.

### 2. `.github/workflows/pre-commit.yml` (Pre-commit CI Workflow)

*   **Python Version Update:** The Python version used by the `actions/setup-python` action has been updated from `3.x` to `3.12.x`.
    *   **Purpose:** This updates the Python environment for running pre-commit hooks in the CI, likely due to newer dependencies or to ensure compatibility with a more recent Python version used in development.

### 3. `packages/opal-common/opal_common/monitoring/apm.py` (Datadog APM Configuration)

*   **Improved Trace Filtering for Datadog APM:**
    *   A new `TraceFilter` class named `DropRootPathTraces` has been added. This filter is designed to drop Datadog traces where the root HTTP request path is `/` (e.g., `http.route` is `/` or the `http.url` path is `/`).
        *   It checks the `http.route` tag first and then falls back to `http.url` if `http.route` is not present or not `/`.
    *   The `configure_apm` function has been refactored:
        *   The logic for disabling APM is now cleaner, simply returning if `enable_apm` is `False`.
        *   The `tracer.configure` call now uses `trace_processors=[DropRootPathTraces()]` instead of embedding the filter within a `settings` dictionary, aligning with newer `ddtrace` API recommendations.
    *   The `fix_ddtrace_logging` function has received a docstring explaining its purpose.
    *   **Purpose:** These changes refine Datadog APM integration by making its configuration more robust and by reducing noise in monitoring data by automatically dropping traces for requests to the root path (`/`), which are often health checks or simple probes that may not require detailed tracing.

### 4. `scripts/start.sh` (Application Startup Script)

*   **Refined Datadog APM `ddtrace-run` Logic:** The conditional statement that determines whether to prefix the `gunicorn` command with `ddtrace-run` has been made more precise.
    *   Original: `if [[ -z "${OPAL_ENABLE_DATADOG_APM}" && "${OPAL_ENABLE_DATADOG_APM}" = "true" ]];` (This condition was logically flawed, as a variable cannot be both unset/empty and equal to `true` simultaneously).
    *   New: `if [[ -n "${OPAL_ENABLE_DATADOG_APM+x}" && ( -z "${OPAL_ENABLE_DATADOG_APM}" || "${OPAL_ENABLE_DATADOG_APM}" = "true" ) ]];`
        *   This new condition correctly checks two scenarios:
            1.  `OPAL_ENABLE_DATADOG_APM` is set (`-n "${OPAL_ENABLE_DATADOG_APM+x}"`) AND it is either an empty string (`-z "${OPAL_ENABLE_DATADOG_APM}"`) OR `true` (`"${OPAL_ENABLE_DATADOG_APM}" = "true"`).
        *   **Impact:** This ensures that `ddtrace-run` is correctly applied when the `OPAL_ENABLE_DATADOG_APM` environment variable is either set to `true` or is explicitly set but left empty. If the variable is completely unset, `ddtrace-run` will not be used, and if it's set to `false` or any other value, `ddtrace-run` will also not be used, providing clearer control over APM activation.
*   **Permissions Change:** The file permission changed from `100755` (executable) to `100644` (non-executable). This might be an oversight or indicates that the script is now intended to be run via `bash` explicitly rather than directly executed.
```

</details>
