import json
import re
import os
from typing import Optional
from packaging import version
from github import Github, GithubException
from datetime import datetime, timedelta
from pydantic import BaseModel

class IssueStats(BaseModel):
    total_issues: Optional[int] = None
    open_issues: Optional[int] = None
    closed_issues_this_month: Optional[int] = None

class LaravelStats(BaseModel):
    repo: str
    description: Optional[str] = None
    default_laravel_version: str
    php_version: str
    branches: list[str]
    newest_laravel_branch: str
    newest_laravel_version: str
    commits_this_month: Optional[int] = None
    issue_stats: IssueStats


class LaravelStatsAgent:
    def __init__(self, org_name: str):
        self.org_name = org_name

    def get_github_client(self):
        return Github(os.getenv("GITHUB_API_TOKEN"))

    def get_issues_in_repo(self, repo):
        all_issues = repo.get_issues()
        total_issues = all_issues.totalCount
        if total_issues == 0:
            return IssueStats(
                total_issues=0,
                open_issues=0,
                closed_issues_this_month=0,
            )
        open_issues = repo.get_issues(state="open").totalCount
        closed_issues_this_month = repo.get_issues(state="closed", since=datetime.now() - timedelta(days=30)).totalCount
        return IssueStats(
            total_issues=total_issues,
            open_issues=open_issues,
            closed_issues_this_month=closed_issues_this_month,
        )

    def parse_laravel_version(self, version_str):
        """
        Parse Laravel version string into a sortable version object.
        Extracts only the major version number (e.g. "11" from "^11.7.21").
        """
        if not version_str:
            return None

        # Extract just the major version number
        match = re.search(r'(\d+)', version_str)
        if not match:
            return None

        major_version = int(match.group(1))

        # Handle version ranges, take the minimum required major version
        if "|" in version_str:
            versions = version_str.split("|")
            parsed_versions = [self.parse_laravel_version(v) for v in versions if self.parse_laravel_version(v)]
            if parsed_versions:
                return min(parsed_versions)
            return None

        return version.parse(f"{major_version}.0")

    def get_laravel_version_from_branch(self, app, branch_name):
        """
        Get Laravel version from composer.json in a specific branch
        """
        try:
            composer_json = app.get_contents("composer.json", ref=branch_name)
            composer_json_content = json.loads(composer_json.decoded_content.decode("utf-8"))
            laravel_version = composer_json_content["require"].get("laravel/framework")
            return laravel_version
        except GithubException:
            return None

    def should_skip_branch(self, branch_name):
        skipped_branches = ["dependabot", "snyk", "experiment", "feature"]
        for skipped_branch in skipped_branches:
            if branch_name.startswith(skipped_branch):
                return True
        return False

    def find_newest_laravel_version_branch(self, app, branches):
        """
        Find the branch with the newest Laravel version
        """
        newest_version = None
        newest_branch = None
        newest_version_str = None

        for branch in branches:
            if self.should_skip_branch(branch.name):
                continue

            laravel_version_str = self.get_laravel_version_from_branch(app, branch.name)
            if not laravel_version_str:
                continue

            parsed_version = self.parse_laravel_version(laravel_version_str)
            if not parsed_version:
                continue

            if newest_version is None or parsed_version > newest_version:
                newest_version = parsed_version
                newest_branch = branch.name
                newest_version_str = laravel_version_str

        return newest_branch, newest_version_str

    def get_laravel_versions_in_projects(self):
        client = self.get_github_client()
        org = client.get_organization(self.org_name)
        repos = org.get_repos()

        results = []

        for repo in repos:
            full_name = f"{self.org_name}/{repo.name}"
            app = client.get_repo(full_name)

            try:
                # Get composer.json from the default branch
                composer_json = app.get_contents("composer.json")
                composer_json_content = json.loads(composer_json.decoded_content.decode("utf-8"))
                laravel_version = composer_json_content["require"].get("laravel/framework")
                php_version = composer_json_content["require"].get("php")

                if not php_version:
                    print(f"No PHP version found in {full_name}")
                    continue

                if not laravel_version:
                    print(f"No Laravel version found in {full_name}")
                    continue

                print(f"Found composer.json in {full_name}:")
                print(f"Laravel version: {laravel_version}")
                print(f"PHP version: {php_version}")
                recent_commits = app.get_commits(since=datetime.now() - timedelta(days=30))
                print(f"Recent commits: {recent_commits}")
                issues = self.get_issues_in_repo(app)
                print(f"Issues: {issues}")
                # Get all branches
                branches = list(app.get_branches())
                branch_names = [branch.name for branch in branches]
                print("Branches:")
                for name in branch_names:
                    print(f"- {name}")

                # Find the branch with the newest Laravel version
                newest_branch, newest_version = self.find_newest_laravel_version_branch(app, branches)

                if newest_branch:
                    print(f"Newest Laravel version ({newest_version}) found in branch: {newest_branch}")
                else:
                    print("No Laravel version found in any branch")

                print(f"Repo description: {repo.description}")
                results.append(LaravelStats(
                    repo=full_name,
                    description=repo.description or 'No description',
                    default_laravel_version=laravel_version,
                    php_version=php_version,
                    branches=branch_names,
                    newest_laravel_branch=newest_branch,
                    newest_laravel_version=newest_version,
                    commits_this_month=recent_commits.totalCount,
                    issue_stats=issues,
                ))

                print("-" * 80)

            except GithubException as e:
                print(f"No composer.json in {full_name}: skipping")

        return results

if __name__ == "__main__":
    agent = LaravelStatsAgent("UoGSoE")
    results = agent.get_laravel_versions_in_projects()

    # Optionally, save results to a JSON file
    with open("laravel_versions.json", "w") as f:
        json.dump(results, f, indent=2)
