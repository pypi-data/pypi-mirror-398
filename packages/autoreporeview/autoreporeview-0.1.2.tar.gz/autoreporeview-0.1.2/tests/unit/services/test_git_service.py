from unittest.mock import patch
import pytest
from app.services.git_service import GitService


def test_get_diff(
    git_service: GitService,
) -> None:
    diff = git_service.get_diff(".", "HEAD", "HEAD~1")
    assert isinstance(diff, str)


def test_clone(
    git_service: GitService,
) -> None:
    repo = "https://github.com/torvalds/linux"
    clone_path = "/tmp/linux_repo"
    with patch.object(git_service, "_call_os") as mock_call_os:
        git_service.clone(repo, clone_path)
        mock_call_os.assert_called_once_with(f"git clone {repo} {clone_path}")


def test_get_contributors_with_multiple_contributors(
    git_service: GitService,
) -> None:
    """Test get_contributors with multiple contributors and multiple commits."""
    mock_output = (
        "Alice|Fix bug in login\nBob|Add new feature\nAlice|Update documentation"
    )
    expected_command = 'git log commitA..commitB --pretty=format:"%an|%s" --no-merges'

    with patch.object(
        git_service, "_call_os", return_value=mock_output
    ) as mock_call_os:
        with patch("app.services.git_service.os.chdir"):
            result = git_service.get_contributors_by_commits(
                "path", "commitA", "commitB"
            )

    mock_call_os.assert_called_once_with(expected_command)
    # Check that both contributors are present with correct counts
    assert "- Alice: 2 commit(s)" in result
    assert "- Bob: 1 commit(s)" in result
    # Should have one newline between entries (2 contributors = 1 newline)
    lines = result.split("\n")
    assert len(lines) == 2
    assert all("- " in line and " commit(s)" in line for line in lines)


def test_get_contributors_with_single_contributor(
    git_service: GitService,
) -> None:
    """Test get_contributors with a single contributor."""
    mock_output = "Alice|Fix bug in login\nAlice|Add new feature"
    expected_command = 'git log commitA..commitB --pretty=format:"%an|%s" --no-merges'

    with patch.object(
        git_service, "_call_os", return_value=mock_output
    ) as mock_call_os:
        with patch("app.services.git_service.os.chdir"):
            result = git_service.get_contributors_by_commits(
                "path", "commitA", "commitB"
            )

    mock_call_os.assert_called_once_with(expected_command)
    assert result == "- Alice: 2 commit(s)"


def test_get_contributors_with_empty_output(
    git_service: GitService,
) -> None:
    """Test get_contributors returns empty string when no commits found."""
    mock_output = ""
    expected_command = 'git log commitA..commitB --pretty=format:"%an|%s" --no-merges'

    with patch.object(
        git_service, "_call_os", return_value=mock_output
    ) as mock_call_os:
        with patch("app.services.git_service.os.chdir"):
            result = git_service.get_contributors_by_commits(
                "path", "commitA", "commitB"
            )

    mock_call_os.assert_called_once_with(expected_command)
    assert result == ""


def test_get_contributors_with_whitespace_only(
    git_service: GitService,
) -> None:
    """Test get_contributors returns empty string when output is only whitespace."""
    mock_output = "   \n\t  \n"
    expected_command = 'git log commitA..commitB --pretty=format:"%an|%s" --no-merges'

    with patch.object(
        git_service, "_call_os", return_value=mock_output
    ) as mock_call_os:
        with patch("app.services.git_service.os.chdir"):
            result = git_service.get_contributors_by_commits(
                "path", "commitA", "commitB"
            )

    mock_call_os.assert_called_once_with(expected_command)
    assert result == ""


def test_get_contributors_ignores_lines_without_separator(
    git_service: GitService,
) -> None:
    """Test get_contributors ignores lines without '|' separator."""
    mock_output = "Alice|Fix bug\nInvalid line without separator\nBob|Add feature"
    expected_command = 'git log commitA..commitB --pretty=format:"%an|%s" --no-merges'

    with patch.object(
        git_service, "_call_os", return_value=mock_output
    ) as mock_call_os:
        with patch("app.services.git_service.os.chdir"):
            result = git_service.get_contributors_by_commits(
                "path", "commitA", "commitB"
            )

    mock_call_os.assert_called_once_with(expected_command)
    assert "- Alice: 1 commit(s)" in result
    assert "- Bob: 1 commit(s)" in result
    assert "Invalid line" not in result


def test_get_contributors_strips_whitespace_from_author_and_message(
    git_service: GitService,
) -> None:
    """Test get_contributors strips whitespace from author names and commit messages."""
    mock_output = "  Alice  |  Fix bug  \n  Bob  |  Add feature  "
    expected_command = 'git log commitA..commitB --pretty=format:"%an|%s" --no-merges'

    with patch.object(
        git_service, "_call_os", return_value=mock_output
    ) as mock_call_os:
        with patch("app.services.git_service.os.chdir"):
            result = git_service.get_contributors_by_commits(
                "path", "commitA", "commitB"
            )

    mock_call_os.assert_called_once_with(expected_command)
    assert "- Alice: 1 commit(s)" in result
    assert "- Bob: 1 commit(s)" in result


def test_get_contributors_handles_commit_messages_with_pipe(
    git_service: GitService,
) -> None:
    """Test get_contributors handles commit messages that contain '|' character."""
    mock_output = "Alice|Fix bug | critical issue\nBob|Add feature"
    expected_command = 'git log commitA..commitB --pretty=format:"%an|%s" --no-merges'

    with patch.object(
        git_service, "_call_os", return_value=mock_output
    ) as mock_call_os:
        with patch("app.services.git_service.os.chdir"):
            result = git_service.get_contributors_by_commits(
                "path", "commitA", "commitB"
            )

    mock_call_os.assert_called_once_with(expected_command)
    assert "- Alice: 1 commit(s)" in result
    assert "- Bob: 1 commit(s)" in result
    # Should split only on first '|', so message should include the rest


def test_get_contributors_by_commits_handles_git_log_failure(
    git_service: GitService,
) -> None:
    """Test get_contributors_by_commits handles git log failure."""
    with patch("app.services.git_service.os.chdir"):
        with patch.object(
            git_service, "_call_os", side_effect=Exception("git log failed")
        ):
            with pytest.raises(Exception, match="git log failed"):
                git_service.get_contributors_by_commits("path", "commitA", "commitB")


def test_get_contributors_by_commits_large_number_of_commits(
    git_service: GitService,
) -> None:
    """Test get_contributors_by_commits with a large number of commits."""
    mock_output = "\n".join([f"Author{i}|Commit message {i}" for i in range(1000)])
    with patch.object(git_service, "_call_os", return_value=mock_output):
        with patch("app.services.git_service.os.chdir"):
            result = git_service.get_contributors_by_commits(
                "path", "commitA", "commitB"
            )
    assert len(result.split("\n")) == 1000


def test_get_diff_by_time(
    git_service: GitService,
) -> None:
    """Test get_diff_by_time returns diff for time range."""
    from datetime import datetime

    mock_diff = "diff --git a/file.py b/file.py\n+new line"
    with patch.object(git_service, "_call_os", return_value=mock_diff):
        with patch("app.services.git_service.os.chdir"):
            start_time = datetime(2024, 1, 1, 0, 0, 0)
            end_time = datetime(2024, 1, 2, 0, 0, 0)
            result = git_service.get_diff_by_time("path", start_time, end_time)

    assert result == mock_diff


def test_get_contributors_by_time_with_contributors(
    git_service: GitService,
) -> None:
    """Test get_contributors_by_time with multiple contributors."""
    from datetime import datetime

    mock_output = "Alice|Fix bug\nBob|Add feature\nAlice|Update docs"
    with patch.object(git_service, "_call_os", return_value=mock_output):
        with patch("app.services.git_service.os.chdir"):
            start_time = datetime(2024, 1, 1, 0, 0, 0)
            end_time = datetime(2024, 1, 2, 0, 0, 0)
            result = git_service.get_contributors_by_time("path", start_time, end_time)

    assert "Alice" in result
    assert "Bob" in result
    assert "2 commit(s)" in result or "1 commit(s)" in result


def test_get_contributors_by_time_empty_output(
    git_service: GitService,
) -> None:
    """Test get_contributors_by_time with empty output."""
    from datetime import datetime

    with patch.object(git_service, "_call_os", return_value=""):
        with patch("app.services.git_service.os.chdir"):
            start_time = datetime(2024, 1, 1, 0, 0, 0)
            end_time = datetime(2024, 1, 2, 0, 0, 0)
            result = git_service.get_contributors_by_time("path", start_time, end_time)

    assert result == ""
