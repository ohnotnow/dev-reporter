import dotenv
import os
import json
from github import Github
from github import Auth
from github import GithubException
from agents.laravel_stats import LaravelStatsAgent
# from agents.composer_stats_agent import ComposerStatsAgent
# from agents.github_agent import GithubAgent

dotenv.load_dotenv(override=True)

def get_github_auth() -> Auth.Token:
    print(os.getenv("GITHUB_API_TOKEN"))
    return Auth.Token(os.getenv("GITHUB_API_TOKEN"))

def get_github_client() -> Github:
    return Github(os.getenv("GITHUB_API_TOKEN"))

def get_list_of_projects(overall_projects_repo_name: str) -> list[str]:
    github_client = get_github_client()
    repo = github_client.get_repo(overall_projects_repo_name)
    contents = repo.get_contents("projects.json")
    projects = json.loads(contents.decoded_content)['projects']
    return projects

def main(overall_projects_repo_name: str):
    github_client = get_github_client()
    projects = get_list_of_projects(overall_projects_repo_name)
    agents = [
        ComposerStatsAgent(projects),
    ]
    composer_stats_agent = ComposerStatsAgent()
    github_agent = GithubAgent()

    composer_stats_agent.run()
    github_agent.run()

def test_get_list_of_projects():
    stats = LaravelStatsAgent("UoGSoE").get_laravel_versions_in_projects()
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
    test_get_list_of_projects()

    # overall_projects_repo = os.getenv("PROJECTS_REPO_NAME")
    # main(overall_projects_repo)
