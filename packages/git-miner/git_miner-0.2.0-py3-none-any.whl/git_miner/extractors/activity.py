from typing import Any

from ..api.models import CommitActivity, IssueStats, PullRequestStats
from .base import BaseExtractor


class ActivityExtractor(BaseExtractor):
    """Extractor for repository activity statistics."""

    async def extract_commits(self, owner: str, repo: str) -> CommitActivity:
        """Extract commit activity statistics.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            CommitActivity with commit statistics
        """
        page = 1
        total_commits = 0
        total_additions = 0
        total_deletions = 0

        while True:
            commits = await self.client.get_commits(owner, repo, page=page)
            if not commits:
                break

            total_commits += len(commits)

            for commit in commits:
                if "stats" in commit:
                    total_additions += commit["stats"].get("additions", 0)
                    total_deletions += commit["stats"].get("deletions", 0)

            if len(commits) < 100:
                break

            page += 1

        return CommitActivity(
            total=total_commits, additions=total_additions, deletions=total_deletions
        )

    async def extract_issues(self, owner: str, repo: str) -> IssueStats:
        """Extract issue statistics.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            IssueStats with issue counts
        """
        open_issues = 0
        page = 1

        while True:
            issues = await self.client.get_issues(owner, repo, state="open", page=page)
            if not issues:
                break
            open_issues += len(issues)
            if len(issues) < 100:
                break
            page += 1

        closed_issues = 0
        page = 1

        while True:
            issues = await self.client.get_issues(owner, repo, state="closed", page=page)
            if not issues:
                break
            closed_issues += len(issues)
            if len(issues) < 100:
                break
            page += 1

        return IssueStats(open_issues=open_issues, closed_issues=closed_issues)

    async def extract_pull_requests(self, owner: str, repo: str) -> PullRequestStats:
        """Extract pull request statistics.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            PullRequestStats with PR counts
        """
        open_prs = 0
        closed_prs = 0
        merged_prs = 0
        page = 1

        while True:
            prs = await self.client.get_pull_requests(owner, repo, state="open", page=page)
            if not prs:
                break
            open_prs += len(prs)
            if len(prs) < 100:
                break
            page += 1

        page = 1
        while True:
            prs = await self.client.get_pull_requests(owner, repo, state="closed", page=page)
            if not prs:
                break
            for pr in prs:
                if pr.get("merged_at"):
                    merged_prs += 1
                else:
                    closed_prs += 1
            if len(prs) < 100:
                break
            page += 1

        return PullRequestStats(open_prs=open_prs, closed_prs=closed_prs, merged_prs=merged_prs)

    async def extract(self, owner: str, repo: str) -> dict[str, Any]:
        """Extract all activity statistics.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary with all activity statistics
        """
        commits = await self.extract_commits(owner, repo)
        issues = await self.extract_issues(owner, repo)
        prs = await self.extract_pull_requests(owner, repo)

        return {
            "commit_total": commits.total,
            "commit_additions": commits.additions,
            "commit_deletions": commits.deletions,
            "issues_open": issues.open_issues,
            "issues_closed": issues.closed_issues,
            "issues_total": issues.open_issues + issues.closed_issues,
            "prs_open": prs.open_prs,
            "prs_closed": prs.closed_prs,
            "prs_merged": prs.merged_prs,
            "prs_total": prs.open_prs + prs.closed_prs + prs.merged_prs,
        }
