# Link: https://github.com/AutoRepoReviewITPD/AutoRepoReview/blob/main/docs/requirements/quality-requirements.md#qast001-1

import pytest
import time
from app import __main__ as main


@pytest.mark.skip("Test is expensive")
@pytest.mark.qas
def test_qas001_1(
    cloned_repo: str,
) -> None:
    number_of_requests = 10

    time_threshold = 30
    failed_requests = 0

    for _ in range(number_of_requests):
        start = time.time()
        main.summary(cloned_repo, "HEAD", "HEAD~1")
        end = time.time()

        elapsed_time = end - start
        if elapsed_time > time_threshold:
            failed_requests += 1

        time.sleep(2)  # give LLM rest a bit

    assert failed_requests <= 1, (
        f"Number of failed requests: {failed_requests} out of {number_of_requests}"
    )
