import json
import re
import os
from typing import Optional
from packaging import version
from github import Github, GithubException
from datetime import datetime, timedelta
from pydantic import BaseModel
from agents.base import BaseAgent
from github.Repository import Repository

class LaravelStats(BaseModel):
    name: str
    php_version: str
    current_laravel_version: str
    newest_laravel_branch: str
    newest_laravel_version: str


class LaravelStatsAgent(BaseAgent):
    def run(self, repo: Repository) -> LaravelStats:
        pass

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

    def get_laravel_version_from_branch(self, repo: Repository, branch_name: str):
        """
        Get Laravel version from composer.json in a specific branch
        """
        try:
            composer_json = repo.get_contents("composer.json", ref=branch_name)
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

    def get_composer_stats(self, app):
        # make a temp dir
        # download composer.json and composer.lock into the temp dir
        #
        # to use composer.lock without installing the packages :
        # composer audit --format=json --locked --no-dev
        # composer show --latest --format=json --locked --no-dev
        # composer licenses --no-dev --format=json
        #
        # For each package we want to know
        # - name
        # - description
        # - installed version
        # - latest version
        # - license
        # - list of security advisories
        pass

    def get_laravel_version(self, repo: Repository):
        full_name = f"{self.entity.login}/{repo.name}"
        app = self.client.get_repo(full_name)

        try:
            # Get composer.json from the default branch
            composer_json = app.get_contents("composer.json")
            composer_json_content = json.loads(composer_json.decoded_content.decode("utf-8"))
            laravel_version = composer_json_content["require"].get("laravel/framework")
            php_version = composer_json_content["require"].get("php")

            if not php_version:
                print(f"No PHP version found in {full_name}")
                return None

            if not laravel_version:
                print(f"No Laravel version found in {full_name}")
                return None

            print(f"Found composer.json in {full_name}:")
            print(f"Laravel version: {laravel_version}")
            print(f"PHP version: {php_version}")
            branches = list(app.get_branches())
            branch_names = [branch.name for branch in branches]

            # Find the branch with the newest Laravel version
            newest_branch, newest_version = self.find_newest_laravel_version_branch(app, branches)

            return LaravelStats(
                repo=full_name,
                description=repo.description or 'No description',
                default_laravel_version=laravel_version,
                php_version=php_version,
                branches=branch_names,
                newest_laravel_branch=newest_branch,
                newest_laravel_version=newest_version,
            )

        except GithubException as e:
            print(f"No composer.json in {full_name}: skipping")

        return None

if __name__ == "__main__":
    agent = LaravelStatsAgent("UoGSoE")
    results = agent.get_laravel_versions_in_projects()

    # Optionally, save results to a JSON file
    with open("laravel_versions.json", "w") as f:
        json.dump(results, f, indent=2)
