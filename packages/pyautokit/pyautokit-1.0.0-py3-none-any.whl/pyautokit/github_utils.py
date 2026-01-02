"""GitHub utilities for repository and issue management."""

import argparse
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .logger import setup_logger
from .config import Config
from .api_client import APIClient
from .utils import save_json, load_json

logger = setup_logger("GitHubUtils", level=Config.LOG_LEVEL)


class GitHubClient:
    """GitHub API client for automation."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (or from env GITHUB_TOKEN)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.warning("No GitHub token provided. Some operations may fail.")
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        self.client = APIClient(
            base_url="https://api.github.com",
            headers=headers
        )

    # Repository Management

    def create_repo(
        self,
        name: str,
        description: str = "",
        private: bool = False,
        auto_init: bool = True
    ) -> Optional[Dict]:
        """Create a new repository.
        
        Args:
            name: Repository name
            description: Repository description
            private: Make repository private
            auto_init: Initialize with README
            
        Returns:
            Repository data or None
        """
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init,
        }
        
        result = self.client.post("/user/repos", json=data)
        
        if result:
            logger.info(f"Created repository: {result['full_name']}")
            return result
        
        return None

    def get_repo(self, owner: str, repo: str) -> Optional[Dict]:
        """Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository data or None
        """
        result = self.client.get(f"/repos/{owner}/{repo}")
        
        if result:
            logger.info(f"Retrieved repo: {result['full_name']}")
            return result
        
        return None

    def list_repos(
        self,
        username: Optional[str] = None,
        org: Optional[str] = None,
        type_filter: str = "owner"
    ) -> List[Dict]:
        """List repositories.
        
        Args:
            username: GitHub username (uses authenticated user if None)
            org: Organization name (takes precedence over username)
            type_filter: owner, member, all
            
        Returns:
            List of repository dicts
        """
        if org:
            endpoint = f"/orgs/{org}/repos"
            params = {}
        elif username:
            endpoint = f"/users/{username}/repos"
            params = {"type": type_filter}
        else:
            endpoint = "/user/repos"
            params = {"type": type_filter}
        
        result = self.client.get(endpoint, params=params)
        
        if result:
            logger.info(f"Retrieved {len(result)} repositories")
            return result
        
        return []

    def delete_repo(self, owner: str, repo: str) -> bool:
        """Delete a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            True if successful
        """
        result = self.client.delete(f"/repos/{owner}/{repo}")
        
        if result is not None:
            logger.info(f"Deleted repository: {owner}/{repo}")
            return True
        
        return False

    # Issue Management

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """Create an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body
            labels: Issue labels
            assignees: Issue assignees
            
        Returns:
            Issue data or None
        """
        data = {
            "title": title,
            "body": body,
        }
        
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        
        result = self.client.post(f"/repos/{owner}/{repo}/issues", json=data)
        
        if result:
            logger.info(f"Created issue #{result['number']}: {title}")
            return result
        
        return None

    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[List[str]] = None
    ) -> List[Dict]:
        """List issues.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: open, closed, all
            labels: Filter by labels
            
        Returns:
            List of issue dicts
        """
        params = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)
        
        result = self.client.get(f"/repos/{owner}/{repo}/issues", params=params)
        
        if result:
            logger.info(f"Retrieved {len(result)} issues")
            return result
        
        return []

    def close_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict]:
        """Close an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            Updated issue data or None
        """
        data = {"state": "closed"}
        
        result = self.client.patch(
            f"/repos/{owner}/{repo}/issues/{issue_number}",
            json=data
        )
        
        if result:
            logger.info(f"Closed issue #{issue_number}")
            return result
        
        return None

    # Pull Request Management

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = ""
    ) -> Optional[Dict]:
        """Create a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Head branch
            base: Base branch
            body: PR description
            
        Returns:
            Pull request data or None
        """
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
        }
        
        result = self.client.post(f"/repos/{owner}/{repo}/pulls", json=data)
        
        if result:
            logger.info(f"Created PR #{result['number']}: {title}")
            return result
        
        return None

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open"
    ) -> List[Dict]:
        """List pull requests.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: open, closed, all
            
        Returns:
            List of PR dicts
        """
        params = {"state": state}
        
        result = self.client.get(f"/repos/{owner}/{repo}/pulls", params=params)
        
        if result:
            logger.info(f"Retrieved {len(result)} pull requests")
            return result
        
        return []

    def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_title: Optional[str] = None,
        merge_method: str = "merge"
    ) -> Optional[Dict]:
        """Merge a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            commit_title: Merge commit title
            merge_method: merge, squash, rebase
            
        Returns:
            Merge result or None
        """
        data = {"merge_method": merge_method}
        if commit_title:
            data["commit_title"] = commit_title
        
        result = self.client.put(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/merge",
            json=data
        )
        
        if result:
            logger.info(f"Merged PR #{pr_number}")
            return result
        
        return None

    # Release Management

    def create_release(
        self,
        owner: str,
        repo: str,
        tag_name: str,
        name: str,
        body: str = "",
        draft: bool = False,
        prerelease: bool = False
    ) -> Optional[Dict]:
        """Create a release.
        
        Args:
            owner: Repository owner
            repo: Repository name
            tag_name: Git tag name
            name: Release name
            body: Release notes
            draft: Create as draft
            prerelease: Mark as prerelease
            
        Returns:
            Release data or None
        """
        data = {
            "tag_name": tag_name,
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease,
        }
        
        result = self.client.post(f"/repos/{owner}/{repo}/releases", json=data)
        
        if result:
            logger.info(f"Created release: {name} ({tag_name})")
            return result
        
        return None

    def list_releases(self, owner: str, repo: str) -> List[Dict]:
        """List releases.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of release dicts
        """
        result = self.client.get(f"/repos/{owner}/{repo}/releases")
        
        if result:
            logger.info(f"Retrieved {len(result)} releases")
            return result
        
        return []

    def get_latest_release(self, owner: str, repo: str) -> Optional[Dict]:
        """Get latest release.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Release data or None
        """
        result = self.client.get(f"/repos/{owner}/{repo}/releases/latest")
        
        if result:
            logger.info(f"Latest release: {result['name']} ({result['tag_name']})")
            return result
        
        return None

    # Workflow Management

    def list_workflows(self, owner: str, repo: str) -> List[Dict]:
        """List GitHub Actions workflows.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of workflow dicts
        """
        result = self.client.get(f"/repos/{owner}/{repo}/actions/workflows")
        
        if result and "workflows" in result:
            workflows = result["workflows"]
            logger.info(f"Retrieved {len(workflows)} workflows")
            return workflows
        
        return []

    def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[Dict] = None
    ) -> bool:
        """Trigger a workflow dispatch.
        
        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow file name or ID
            ref: Git ref (branch, tag, SHA)
            inputs: Workflow inputs
            
        Returns:
            True if successful
        """
        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs
        
        result = self.client.post(
            f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            json=data
        )
        
        if result is not None:
            logger.info(f"Triggered workflow: {workflow_id}")
            return True
        
        return False


def main() -> None:
    """CLI for GitHub utilities."""
    parser = argparse.ArgumentParser(description="GitHub utilities")
    parser.add_argument("--token", help="GitHub personal access token")
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Repository commands
    repo_parser = subparsers.add_parser("repo", help="Repository operations")
    repo_parser.add_argument("action", choices=["create", "list", "get", "delete"])
    repo_parser.add_argument("--owner", help="Repository owner")
    repo_parser.add_argument("--repo", help="Repository name")
    repo_parser.add_argument("--name", help="New repository name")
    repo_parser.add_argument("--description", default="", help="Repository description")
    repo_parser.add_argument("--private", action="store_true", help="Private repository")
    repo_parser.add_argument("--output", "-o", help="Output file")
    
    # Issue commands
    issue_parser = subparsers.add_parser("issue", help="Issue operations")
    issue_parser.add_argument("action", choices=["create", "list", "close"])
    issue_parser.add_argument("--owner", required=True, help="Repository owner")
    issue_parser.add_argument("--repo", required=True, help="Repository name")
    issue_parser.add_argument("--number", type=int, help="Issue number")
    issue_parser.add_argument("--title", help="Issue title")
    issue_parser.add_argument("--body", help="Issue body")
    issue_parser.add_argument("--labels", nargs="*", help="Issue labels")
    issue_parser.add_argument("--state", default="open", choices=["open", "closed", "all"])
    issue_parser.add_argument("--output", "-o", help="Output file")
    
    # PR commands
    pr_parser = subparsers.add_parser("pr", help="Pull request operations")
    pr_parser.add_argument("action", choices=["create", "list", "merge"])
    pr_parser.add_argument("--owner", required=True, help="Repository owner")
    pr_parser.add_argument("--repo", required=True, help="Repository name")
    pr_parser.add_argument("--number", type=int, help="PR number")
    pr_parser.add_argument("--title", help="PR title")
    pr_parser.add_argument("--head", help="Head branch")
    pr_parser.add_argument("--base", default="main", help="Base branch")
    pr_parser.add_argument("--body", help="PR description")
    pr_parser.add_argument("--state", default="open", choices=["open", "closed", "all"])
    pr_parser.add_argument("--output", "-o", help="Output file")
    
    # Release commands
    release_parser = subparsers.add_parser("release", help="Release operations")
    release_parser.add_argument("action", choices=["create", "list", "latest"])
    release_parser.add_argument("--owner", required=True, help="Repository owner")
    release_parser.add_argument("--repo", required=True, help="Repository name")
    release_parser.add_argument("--tag", help="Git tag name")
    release_parser.add_argument("--name", help="Release name")
    release_parser.add_argument("--body", help="Release notes")
    release_parser.add_argument("--output", "-o", help="Output file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = GitHubClient(token=args.token)
    
    # Repository operations
    if args.command == "repo":
        if args.action == "create":
            result = client.create_repo(
                name=args.name,
                description=args.description,
                private=args.private
            )
            if result:
                print(f"Created: {result['html_url']}")
                if args.output:
                    save_json(result, Config.DATA_DIR / args.output)
        
        elif args.action == "list":
            repos = client.list_repos()
            for repo in repos:
                print(f"{repo['full_name']} - {repo.get('description', 'No description')}")
            if args.output:
                save_json(repos, Config.DATA_DIR / args.output)
        
        elif args.action == "get":
            result = client.get_repo(args.owner, args.repo)
            if result:
                print(f"Name: {result['full_name']}")
                print(f"Stars: {result['stargazers_count']}")
                print(f"Forks: {result['forks_count']}")
                if args.output:
                    save_json(result, Config.DATA_DIR / args.output)
        
        elif args.action == "delete":
            if client.delete_repo(args.owner, args.repo):
                print(f"Deleted: {args.owner}/{args.repo}")
    
    # Issue operations
    elif args.command == "issue":
        if args.action == "create":
            result = client.create_issue(
                owner=args.owner,
                repo=args.repo,
                title=args.title,
                body=args.body or "",
                labels=args.labels
            )
            if result:
                print(f"Created issue #{result['number']}: {result['html_url']}")
                if args.output:
                    save_json(result, Config.DATA_DIR / args.output)
        
        elif args.action == "list":
            issues = client.list_issues(
                owner=args.owner,
                repo=args.repo,
                state=args.state,
                labels=args.labels
            )
            for issue in issues:
                print(f"#{issue['number']}: {issue['title']}")
            if args.output:
                save_json(issues, Config.DATA_DIR / args.output)
        
        elif args.action == "close":
            result = client.close_issue(args.owner, args.repo, args.number)
            if result:
                print(f"Closed issue #{args.number}")
    
    # PR operations
    elif args.command == "pr":
        if args.action == "create":
            result = client.create_pull_request(
                owner=args.owner,
                repo=args.repo,
                title=args.title,
                head=args.head,
                base=args.base,
                body=args.body or ""
            )
            if result:
                print(f"Created PR #{result['number']}: {result['html_url']}")
                if args.output:
                    save_json(result, Config.DATA_DIR / args.output)
        
        elif args.action == "list":
            prs = client.list_pull_requests(
                owner=args.owner,
                repo=args.repo,
                state=args.state
            )
            for pr in prs:
                print(f"#{pr['number']}: {pr['title']}")
            if args.output:
                save_json(prs, Config.DATA_DIR / args.output)
        
        elif args.action == "merge":
            result = client.merge_pull_request(args.owner, args.repo, args.number)
            if result:
                print(f"Merged PR #{args.number}")
    
    # Release operations
    elif args.command == "release":
        if args.action == "create":
            result = client.create_release(
                owner=args.owner,
                repo=args.repo,
                tag_name=args.tag,
                name=args.name,
                body=args.body or ""
            )
            if result:
                print(f"Created release: {result['html_url']}")
                if args.output:
                    save_json(result, Config.DATA_DIR / args.output)
        
        elif args.action == "list":
            releases = client.list_releases(args.owner, args.repo)
            for release in releases:
                print(f"{release['tag_name']}: {release['name']}")
            if args.output:
                save_json(releases, Config.DATA_DIR / args.output)
        
        elif args.action == "latest":
            result = client.get_latest_release(args.owner, args.repo)
            if result:
                print(f"Latest: {result['tag_name']} - {result['name']}")
                print(f"URL: {result['html_url']}")
                if args.output:
                    save_json(result, Config.DATA_DIR / args.output)


if __name__ == "__main__":
    main()
