from pydantic import BaseModel
from agents.composer_stats import ComposerStats
from agents.github_stats import GithubStats
from agents.laravel_stats import LaravelStats
from agents.code_stats import CodeStats

class RepoStats(BaseModel):
    repo_name: str
    repo_url: str
    repo_description: str
    repo_type: str
    composer_stats: ComposerStats
    github_stats: GithubStats
    laravel_stats: LaravelStats
    code_stats: CodeStats
