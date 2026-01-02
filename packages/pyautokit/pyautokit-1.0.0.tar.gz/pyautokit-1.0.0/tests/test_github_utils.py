"""Tests for github_utils module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from pyautokit.github_utils import GitHubClient, main


@pytest.fixture
def github_client():
    """Create GitHubClient with mock token."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"}):
        return GitHubClient()


@pytest.fixture
def mock_repo_response():
    """Mock repository API response."""
    return {
        "id": 123456,
        "name": "test-repo",
        "full_name": "user/test-repo",
        "description": "Test repository",
        "private": False,
        "html_url": "https://github.com/user/test-repo",
        "stargazers_count": 10,
        "forks_count": 5,
    }


@pytest.fixture
def mock_issue_response():
    """Mock issue API response."""
    return {
        "number": 1,
        "title": "Test issue",
        "body": "Issue body",
        "state": "open",
        "html_url": "https://github.com/user/repo/issues/1",
    }


@pytest.fixture
def mock_pr_response():
    """Mock pull request API response."""
    return {
        "number": 10,
        "title": "Test PR",
        "body": "PR description",
        "state": "open",
        "html_url": "https://github.com/user/repo/pull/10",
        "head": {"ref": "feature"},
        "base": {"ref": "main"},
    }


@pytest.fixture
def mock_release_response():
    """Mock release API response."""
    return {
        "id": 999,
        "tag_name": "v1.0.0",
        "name": "Release 1.0.0",
        "body": "Release notes",
        "html_url": "https://github.com/user/repo/releases/tag/v1.0.0",
    }


class TestGitHubClient:
    """Test GitHubClient class."""

    def test_init_with_token(self):
        """Test initialization with token."""
        client = GitHubClient(token="test-token")
        assert client.token == "test-token"
        assert client.client is not None

    def test_init_from_env(self):
        """Test initialization from environment."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env-token"}):
            client = GitHubClient()
            assert client.token == "env-token"

    def test_init_no_token_warning(self, caplog):
        """Test warning when no token provided."""
        with patch.dict(os.environ, {}, clear=True):
            client = GitHubClient()
            assert "No GitHub token" in caplog.text

    # Repository Tests

    @patch("pyautokit.github_utils.APIClient.post")
    def test_create_repo_success(self, mock_post, github_client, mock_repo_response):
        """Test successful repository creation."""
        mock_post.return_value = mock_repo_response

        result = github_client.create_repo(
            name="test-repo",
            description="Test description",
            private=True
        )

        assert result is not None
        assert result["name"] == "test-repo"
        assert result["full_name"] == "user/test-repo"
        mock_post.assert_called_once()

    @patch("pyautokit.github_utils.APIClient.post")
    def test_create_repo_failure(self, mock_post, github_client):
        """Test repository creation failure."""
        mock_post.return_value = None

        result = github_client.create_repo(name="test-repo")

        assert result is None

    @patch("pyautokit.github_utils.APIClient.get")
    def test_get_repo_success(self, mock_get, github_client, mock_repo_response):
        """Test successful repository retrieval."""
        mock_get.return_value = mock_repo_response

        result = github_client.get_repo("user", "test-repo")

        assert result is not None
        assert result["full_name"] == "user/test-repo"
        mock_get.assert_called_once_with("/repos/user/test-repo")

    @patch("pyautokit.github_utils.APIClient.get")
    def test_list_repos_user(self, mock_get, github_client, mock_repo_response):
        """Test listing user repositories."""
        mock_get.return_value = [mock_repo_response]

        result = github_client.list_repos(username="user")

        assert len(result) == 1
        assert result[0]["full_name"] == "user/test-repo"

    @patch("pyautokit.github_utils.APIClient.get")
    def test_list_repos_authenticated(self, mock_get, github_client, mock_repo_response):
        """Test listing authenticated user repos."""
        mock_get.return_value = [mock_repo_response]

        result = github_client.list_repos()

        assert len(result) == 1
        mock_get.assert_called_once_with("/user/repos", params={"type": "owner"})

    @patch("pyautokit.github_utils.APIClient.get")
    def test_list_repos_org(self, mock_get, github_client, mock_repo_response):
        """Test listing organization repositories."""
        mock_get.return_value = [mock_repo_response]

        result = github_client.list_repos(org="myorg")

        assert len(result) == 1
        mock_get.assert_called_once_with("/orgs/myorg/repos", params={})

    @patch("pyautokit.github_utils.APIClient.delete")
    def test_delete_repo_success(self, mock_delete, github_client):
        """Test successful repository deletion."""
        mock_delete.return_value = True

        result = github_client.delete_repo("user", "test-repo")

        assert result is True
        mock_delete.assert_called_once_with("/repos/user/test-repo")

    @patch("pyautokit.github_utils.APIClient.delete")
    def test_delete_repo_failure(self, mock_delete, github_client):
        """Test repository deletion failure."""
        mock_delete.return_value = None

        result = github_client.delete_repo("user", "test-repo")

        assert result is False

    # Issue Tests

    @patch("pyautokit.github_utils.APIClient.post")
    def test_create_issue_success(self, mock_post, github_client, mock_issue_response):
        """Test successful issue creation."""
        mock_post.return_value = mock_issue_response

        result = github_client.create_issue(
            owner="user",
            repo="repo",
            title="Test issue",
            body="Issue body",
            labels=["bug", "help wanted"],
            assignees=["user1"]
        )

        assert result is not None
        assert result["number"] == 1
        assert result["title"] == "Test issue"

    @patch("pyautokit.github_utils.APIClient.get")
    def test_list_issues_success(self, mock_get, github_client, mock_issue_response):
        """Test successful issue listing."""
        mock_get.return_value = [mock_issue_response]

        result = github_client.list_issues("user", "repo", state="open")

        assert len(result) == 1
        assert result[0]["number"] == 1

    @patch("pyautokit.github_utils.APIClient.get")
    def test_list_issues_with_labels(self, mock_get, github_client, mock_issue_response):
        """Test issue listing with label filter."""
        mock_get.return_value = [mock_issue_response]

        result = github_client.list_issues(
            "user",
            "repo",
            labels=["bug", "urgent"]
        )

        assert len(result) == 1
        # Verify labels were passed as comma-separated string
        call_args = mock_get.call_args
        assert call_args[1]["params"]["labels"] == "bug,urgent"

    @patch("pyautokit.github_utils.APIClient.patch")
    def test_close_issue_success(self, mock_patch, github_client, mock_issue_response):
        """Test successful issue closing."""
        closed_issue = mock_issue_response.copy()
        closed_issue["state"] = "closed"
        mock_patch.return_value = closed_issue

        result = github_client.close_issue("user", "repo", 1)

        assert result is not None
        assert result["state"] == "closed"

    # Pull Request Tests

    @patch("pyautokit.github_utils.APIClient.post")
    def test_create_pr_success(self, mock_post, github_client, mock_pr_response):
        """Test successful PR creation."""
        mock_post.return_value = mock_pr_response

        result = github_client.create_pull_request(
            owner="user",
            repo="repo",
            title="Test PR",
            head="feature",
            base="main",
            body="PR description"
        )

        assert result is not None
        assert result["number"] == 10
        assert result["title"] == "Test PR"

    @patch("pyautokit.github_utils.APIClient.get")
    def test_list_prs_success(self, mock_get, github_client, mock_pr_response):
        """Test successful PR listing."""
        mock_get.return_value = [mock_pr_response]

        result = github_client.list_pull_requests("user", "repo", state="open")

        assert len(result) == 1
        assert result[0]["number"] == 10

    @patch("pyautokit.github_utils.APIClient.put")
    def test_merge_pr_success(self, mock_put, github_client):
        """Test successful PR merge."""
        mock_put.return_value = {"merged": True, "sha": "abc123"}

        result = github_client.merge_pull_request(
            "user",
            "repo",
            10,
            commit_title="Merge PR #10",
            merge_method="squash"
        )

        assert result is not None
        assert result["merged"] is True

    # Release Tests

    @patch("pyautokit.github_utils.APIClient.post")
    def test_create_release_success(self, mock_post, github_client, mock_release_response):
        """Test successful release creation."""
        mock_post.return_value = mock_release_response

        result = github_client.create_release(
            owner="user",
            repo="repo",
            tag_name="v1.0.0",
            name="Release 1.0.0",
            body="Release notes",
            draft=False,
            prerelease=False
        )

        assert result is not None
        assert result["tag_name"] == "v1.0.0"
        assert result["name"] == "Release 1.0.0"

    @patch("pyautokit.github_utils.APIClient.get")
    def test_list_releases_success(self, mock_get, github_client, mock_release_response):
        """Test successful release listing."""
        mock_get.return_value = [mock_release_response]

        result = github_client.list_releases("user", "repo")

        assert len(result) == 1
        assert result[0]["tag_name"] == "v1.0.0"

    @patch("pyautokit.github_utils.APIClient.get")
    def test_get_latest_release_success(self, mock_get, github_client, mock_release_response):
        """Test successful latest release retrieval."""
        mock_get.return_value = mock_release_response

        result = github_client.get_latest_release("user", "repo")

        assert result is not None
        assert result["tag_name"] == "v1.0.0"

    # Workflow Tests

    @patch("pyautokit.github_utils.APIClient.get")
    def test_list_workflows_success(self, mock_get, github_client):
        """Test successful workflow listing."""
        mock_get.return_value = {
            "workflows": [
                {"id": 1, "name": "CI", "path": ".github/workflows/ci.yml"},
                {"id": 2, "name": "Deploy", "path": ".github/workflows/deploy.yml"},
            ]
        }

        result = github_client.list_workflows("user", "repo")

        assert len(result) == 2
        assert result[0]["name"] == "CI"

    @patch("pyautokit.github_utils.APIClient.get")
    def test_list_workflows_empty(self, mock_get, github_client):
        """Test workflow listing with empty response."""
        mock_get.return_value = {}

        result = github_client.list_workflows("user", "repo")

        assert len(result) == 0

    @patch("pyautokit.github_utils.APIClient.post")
    def test_trigger_workflow_success(self, mock_post, github_client):
        """Test successful workflow trigger."""
        mock_post.return_value = True

        result = github_client.trigger_workflow(
            "user",
            "repo",
            "ci.yml",
            ref="main",
            inputs={"debug": "true"}
        )

        assert result is True

    @patch("pyautokit.github_utils.APIClient.post")
    def test_trigger_workflow_failure(self, mock_post, github_client):
        """Test workflow trigger failure."""
        mock_post.return_value = None

        result = github_client.trigger_workflow("user", "repo", "ci.yml")

        assert result is False


class TestCLI:
    """Test CLI functionality."""

    @patch("pyautokit.github_utils.GitHubClient.create_repo")
    @patch("sys.argv", ["github", "--token", "test", "repo", "create", "--name", "test-repo"])
    def test_cli_create_repo(self, mock_create, capsys):
        """Test CLI repo creation."""
        mock_create.return_value = {"html_url": "https://github.com/user/test-repo"}

        main()

        captured = capsys.readouterr()
        assert "https://github.com/user/test-repo" in captured.out

    @patch("pyautokit.github_utils.GitHubClient.list_repos")
    @patch("sys.argv", ["github", "repo", "list"])
    def test_cli_list_repos(self, mock_list, capsys):
        """Test CLI repo listing."""
        mock_list.return_value = [
            {"full_name": "user/repo1", "description": "Desc 1"},
            {"full_name": "user/repo2", "description": "Desc 2"},
        ]

        main()

        captured = capsys.readouterr()
        assert "user/repo1" in captured.out
        assert "user/repo2" in captured.out

    @patch("pyautokit.github_utils.GitHubClient.create_issue")
    @patch(
        "sys.argv",
        ["github", "issue", "create", "--owner", "user", "--repo", "repo", "--title", "Bug"]
    )
    def test_cli_create_issue(self, mock_create, capsys):
        """Test CLI issue creation."""
        mock_create.return_value = {
            "number": 1,
            "html_url": "https://github.com/user/repo/issues/1"
        }

        main()

        captured = capsys.readouterr()
        assert "#1" in captured.out

    @patch("pyautokit.github_utils.GitHubClient.list_issues")
    @patch(
        "sys.argv",
        ["github", "issue", "list", "--owner", "user", "--repo", "repo"]
    )
    def test_cli_list_issues(self, mock_list, capsys):
        """Test CLI issue listing."""
        mock_list.return_value = [
            {"number": 1, "title": "Bug fix"},
            {"number": 2, "title": "Feature request"},
        ]

        main()

        captured = capsys.readouterr()
        assert "#1: Bug fix" in captured.out
        assert "#2: Feature request" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
