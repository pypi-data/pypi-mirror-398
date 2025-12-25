# Link: https://github.com/AutoRepoReviewITPD/AutoRepoReview/blob/main/docs/requirements/quality-requirements.md#qast004-1

import subprocess
import pytest


@pytest.mark.qas
def test_qas003_1() -> None:
    result = subprocess.run(
        ["uv", "run", "pytest", "--cov=app", "tests/unit", "--cov-fail-under=80"]
    )
    assert result.returncode == 0
