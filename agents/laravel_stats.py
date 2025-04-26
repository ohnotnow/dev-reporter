import json
import re
import os
import subprocess
import sys
from typing import Optional
from packaging import version
from pydantic import BaseModel

class LaravelStats(BaseModel):
    name: str
    php_version: str
    current_laravel_version: str
    newest_laravel_branch: str
    newest_laravel_version: str

class LaravelStatsAgent():
    def __init__(self, code_path: str):
        self.code_path = code_path

    def run(self) -> LaravelStats:
        # Get all branches
        branches = self.get_all_branches()
        # Get current branch
        current_branch = self.get_current_branch()
        # Get composer.json from current branch
        composer_json = self.read_composer_json()
        if not composer_json:
            raise RuntimeError(f"No composer.json found in {self.code_path}")
        laravel_version = composer_json["require"].get("laravel/framework")
        php_version = composer_json["require"].get("php")
        if not laravel_version or not php_version:
            raise RuntimeError(f"composer.json missing laravel/framework or php in {self.code_path}")
        # Find the branch with the newest Laravel version
        newest_branch, newest_version = self.find_newest_laravel_version_branch(branches)
        # Restore original branch
        self.checkout_branch(current_branch)
        return LaravelStats(
            name=os.path.basename(self.code_path),
            php_version=php_version,
            current_laravel_version=laravel_version,
            newest_laravel_branch=newest_branch,
            newest_laravel_version=newest_version,
        )

    def parse_laravel_version(self, version_str):
        if not version_str:
            return None
        match = re.search(r'(\d+)', version_str)
        if not match:
            return None
        major_version = int(match.group(1))
        if "|" in version_str:
            versions = version_str.split("|")
            parsed_versions = [self.parse_laravel_version(v) for v in versions if self.parse_laravel_version(v)]
            if parsed_versions:
                return min(parsed_versions)
            return None
        return version.parse(f"{major_version}.0")

    def get_all_branches(self):
        result = subprocess.run(["git", "branch", "-a", "--format=%(refname:short)"], cwd=self.code_path, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"git branch failed: {result.stderr}")
        branches = [b.strip() for b in result.stdout.splitlines() if b.strip()]
        # Remove duplicates
        return list(sorted(set(branches)))

    def get_current_branch(self):
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=self.code_path, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"git rev-parse failed: {result.stderr}")
        return result.stdout.strip()

    def checkout_branch(self, branch_name):
        result = subprocess.run(["git", "checkout", branch_name], cwd=self.code_path, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"git checkout {branch_name} failed: {result.stderr}")

    def read_composer_json(self):
        composer_path = os.path.join(self.code_path, "composer.json")
        if not os.path.exists(composer_path):
            return None
        with open(composer_path, "r") as f:
            return json.load(f)

    def should_skip_branch(self, branch_name):
        skipped_branches = ["dependabot", "snyk", "experiment", "feature"]
        for skipped_branch in skipped_branches:
            if branch_name.startswith(skipped_branch):
                return True
        return False

    def get_laravel_version_from_branch(self, branch_name):
        try:
            self.checkout_branch(branch_name)
            composer_json = self.read_composer_json()
            if not composer_json:
                return None
            laravel_version = composer_json["require"].get("laravel/framework")
            return laravel_version
        except Exception:
            return None

    def find_newest_laravel_version_branch(self, branches):
        newest_version = None
        newest_branch = None
        newest_version_str = None
        for branch in branches:
            if self.should_skip_branch(branch):
                continue
            laravel_version_str = self.get_laravel_version_from_branch(branch)
            if not laravel_version_str:
                continue
            parsed_version = self.parse_laravel_version(laravel_version_str)
            if not parsed_version:
                continue
            if newest_version is None or parsed_version > newest_version:
                newest_version = parsed_version
                newest_branch = branch
                newest_version_str = laravel_version_str
        return newest_branch, newest_version_str

if __name__ == "__main__":
    agent = LaravelStatsAgent(sys.argv[1])
    result = agent.run()
    print(result)
