import dotenv
import os
import json
import argparse
import subprocess
from pydantic import BaseModel
from github import Github, Auth, GithubException
from github.Repository import Repository
from agents.laravel_stats import LaravelStatsAgent
# from agents.composer_stats_agent import ComposerStatsAgent
# from agents.github_agent import GithubAgent

dotenv.load_dotenv(override=True)

class RepoStats(BaseModel):
    name: str
    url: str
    description: str
    github_stats: dict
    composer_stats: dict
    laravel_stats: dict
    code_stats: dict

def get_github_auth():
    return Auth.Token(os.getenv("GITHUB_API_TOKEN"))

def get_github_client() -> Github:
    return Github(get_github_auth())

def get_list_of_repos(entity_type: str, entity_name: str) -> list[Repository]:
    github_client = get_github_client()
    if entity_type == "team":
        return github_client.get_team(entity_name).get_repos()
    elif entity_type == "org":
        return github_client.get_organization(entity_name).get_repos()
    elif entity_type == "repo":
        return [github_client.get_repo(entity_name)]
    else:
        raise ValueError(f"Invalid entity type: {entity_type}")

def main(entity_type: str, entity_name: str):
    repos = get_list_of_repos(entity_type, entity_name)
    results = {}
    for i, repo in enumerate(repos):
        results[repo.name] = {}
        print(f"- Processing {repo.name} ({i+1}/{len(repos)})")
        agent = GithubStatsAgent(repo)
        github_stats = agent.run()
        temp_dir = checkout_repo(repo.clone_url)
        composer_stats_agent = ComposerStatsAgent(temp_dir)
        composer_stats = composer_stats_agent.run()
        laravel_stats_agent = LaravelStatsAgent(temp_dir)
        laravel_stats = laravel_stats_agent.run()
        code_stats_agent = CodeStatsAgent(temp_dir)
        code_stats = code_stats_agent.run()
        results[repo.name] = RepoStats(
            name=repo.name,
            url=repo.clone_url,
            description=repo.description,
            github_stats=github_stats,
            composer_stats=composer_stats,
            laravel_stats=laravel_stats,
            code_stats=code_stats,
        )
    print(results)
    print(temp_dir)

def test_get_list_of_projects(base_type: str, name: str):
    stats_agent = LaravelStatsAgent(base_type, name)
    stats = stats_agent.get_laravel_versions_in_projects()
    print(stats)
    exit()

    org_name = "UoGSoE"
    client = get_github_client()
    org = client.get_organization(org_name)
    repos = org.get_repos()
    for repo in repos:
        full_name = f"{org_name}/{repo.name}"
        app = client.get_repo(full_name)
        try:
            composer_json = app.get_contents("composer.json")
            print(f"Found composer.json in {full_name}:")
            composer_json_content = json.loads(composer_json.decoded_content.decode("utf-8"))
            laravel_version = composer_json_content["require"].get("laravel/framework")
            print(f"Laravel version: {laravel_version}")
            php_version = composer_json_content["require"].get("php")
            print(f"PHP version: {php_version}")
            branches = app.get_branches()
            for branch in branches:
                print(f"- {branch.name}")
            # print(composer_json_content)
        except GithubException as e:
            print(f"No composer.json in {full_name}: skipping")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', type=str, choices=['team', 'repo', 'org'], help='Type of base to use', required=True)
    parser.add_argument('--name', type=str, help='Name of the base', required=True)
    args = parser.parse_args()

    print(f"Processing report for {args.type}: {args.name}")

    test_get_list_of_projects(base_type=args.type, name=args.name)
    # overall_projects_repo = os.getenv("PROJECTS_REPO_NAME")
    # main(overall_projects_repo)
