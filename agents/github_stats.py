from agents.base import BaseAgent
from github.Repository import Repository
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional

class DependabotAlertModel(BaseModel):
    number: int
    state: str
    dependency: Optional[str]
    severity: Optional[str]
    security_advisory_summary: Optional[str]
    security_advisory_description: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    dismissed_at: Optional[str]
    dismissed_by: Optional[str]
    dismissed_reason: Optional[str]
    html_url: Optional[str]

class GithubStats(BaseModel):
    name: str
    url: str
    description: str
    primary_language: str
    num_open_issues: int
    num_closed_issues_30d: int
    num_open_prs: int
    num_merged_prs_30d: int
    dependabot_issues: list[DependabotAlertModel]


class GithubStatsAgent(BaseAgent):
    # this agent will be used to get the github-provided stats for a given github repo
    def __init__(self, model: str = "o4-mini", provider: str = "openai"):
        super().__init__(model, provider)

    def run(self, repo: Repository) -> GithubStats:
        stats = self.get_stats(repo)
        return stats

    def get_stats(self, repo: Repository) -> GithubStats:
        now = datetime.now(datetime.timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        # Basic info
        name = repo.name
        description = repo.description
        language = repo.language

        # Issues
        open_issues = repo.get_issues(state="open")
        closed_issues = repo.get_issues(state="closed", since=thirty_days_ago)
        num_open_issues = open_issues.totalCount
        num_closed_issues_30d = closed_issues.totalCount

        # PRs
        open_prs = repo.get_pulls(state="open")
        merged_prs = repo.get_pulls(state="closed")
        num_open_prs = open_prs.totalCount
        # Count merged PRs in last 30 days
        merged_prs_30d = [pr for pr in merged_prs if pr.merged_at and pr.merged_at >= thirty_days_ago]
        num_merged_prs_30d = len(merged_prs_30d)

        # Dependabot alerts: use GitHub API
        alerts = repo.get_dependabot_alerts()
        dependabot_alerts = []
        for alert in alerts:
            dependabot_alerts.append(
                DependabotAlertModel(
                    number=getattr(alert, 'number', None),
                    state=getattr(alert, 'state', None),
                    dependency=getattr(alert.dependency, 'package', None) if hasattr(alert, 'dependency') else None,
                    severity=getattr(alert, 'severity', None),
                    security_advisory_summary=getattr(alert.security_advisory, 'summary', None) if hasattr(alert, 'security_advisory') else None,
                    security_advisory_description=getattr(alert.security_advisory, 'description', None) if hasattr(alert, 'security_advisory') else None,
                    created_at=str(getattr(alert, 'created_at', None)),
                    updated_at=str(getattr(alert, 'updated_at', None)),
                    dismissed_at=str(getattr(alert, 'dismissed_at', None)),
                    dismissed_by=getattr(alert, 'dismissed_by', None),
                    dismissed_reason=getattr(alert, 'dismissed_reason', None),
                    html_url=getattr(alert, 'html_url', None),
                )
            )

        return GithubStats(
            name=name,
            url=repo.html_url,
            description=description,
            primary_language=language,
            num_open_issues=num_open_issues,
            num_closed_issues_30d=num_closed_issues_30d,
            num_open_prs=num_open_prs,
            num_merged_prs_30d=num_merged_prs_30d,
            dependabot_issues=dependabot_alerts,
        )
