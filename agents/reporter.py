from pydantic import BaseModel
from models.repo_stats import RepoStats
from jinja2 import Template, Environment, FileSystemLoader
from litellm import completion

class Report(BaseModel):
    summary_text: str
    summary_stats: dict
    summary_review: str
    recommendations: list[str]
    repositories: list[RepoStats]

class LlmResponse(BaseModel):
    message: str
    cost: float
    tokens: int
    model: str

class Reporter():
    def __init__(self, repos: list[RepoStats], model_name: str = "gpt-4o-mini", provider: str = "openai"):
        self.repos = repos
        self.env = Environment(loader=FileSystemLoader('templates'))
        self.model_name = model_name
        self.provider = provider

    def run(self) -> Report:
        summary_stats = self.get_summary_stats()
        summary_tables = self.get_summary_tables()
        summary_text = self.get_summary_text(f"Provide an executive summary for the following repositories: {summary_stats}").message
        summary_review = self.get_summary_review(f"Provide a technical review for the following repositories: {summary_stats}").message
        recommendations = self.get_recommendations(f"Provide recommendations for the following repositories: {summary_stats}").message.split('\n')
        repo_reports = [self.get_repo_report(repo) for repo in self.repos]

        # Render the full report using the template
        report_template = self.env.get_template('report.md.j2')
        report_md = report_template.render(
            summary_text=summary_text,
            summary_stats=summary_stats,
            summary_review=summary_review,
            recommendations=recommendations,
            repo_reports=repo_reports
        )
        return report_md

    def get_litellm_model(self) -> str:
        return f"{self.provider}/{self.model_name}"

    def get_summary_stats(self) -> dict:
        # Aggregate stats across all repos
        total_open_issues = sum(r.github_stats.num_open_issues for r in self.repos)
        total_closed_issues_30d = sum(r.github_stats.num_closed_issues_30d for r in self.repos)
        total_open_prs = sum(r.github_stats.num_open_prs for r in self.repos)
        total_merged_prs_30d = sum(r.github_stats.num_merged_prs_30d for r in self.repos)
        total_dependabot_alerts = sum(len(r.github_stats.dependabot_issues) for r in self.repos)
        total_packages = sum(len(r.composer_stats.packages) for r in self.repos)
        total_security_advisories = sum(
            sum(len(pkg.security_advisories) for pkg in r.composer_stats.packages)
            for r in self.repos
        )
        total_code = sum(
            sum(lang.code for lang in r.code_stats.language_summary)
            for r in self.repos
        )
        total_cost = sum(r.code_stats.estimated_cost for r in self.repos)
        return {
            'total_repos': len(self.repos),
            'total_open_issues': total_open_issues,
            'total_closed_issues_30d': total_closed_issues_30d,
            'total_open_prs': total_open_prs,
            'total_merged_prs_30d': total_merged_prs_30d,
            'total_dependabot_alerts': total_dependabot_alerts,
            'total_packages': total_packages,
            'total_security_advisories': total_security_advisories,
            'total_code': total_code,
            'total_cost': total_cost,
        }

    def get_summary_tables(self) -> list[str]:
        # Return a markdown table for each repo
        tables = []
        for r in self.repos:
            table = f"""
| Repo | Open Issues | Closed Issues (30d) | Open PRs | Merged PRs (30d) | Dependabot Alerts | Packages | Security Advisories | Code (LOC) | Cost |
|------|-------------|--------------------|----------|------------------|-------------------|----------|---------------------|------------|------|
| {r.repo_name} | {r.github_stats.num_open_issues} | {r.github_stats.num_closed_issues_30d} | {r.github_stats.num_open_prs} | {r.github_stats.num_merged_prs_30d} | {len(r.github_stats.dependabot_issues)} | {len(r.composer_stats.packages)} | {sum(len(pkg.security_advisories) for pkg in r.composer_stats.packages)} | {sum(lang.code for lang in r.code_stats.language_summary)} | ${r.code_stats.estimated_cost:.2f} |
"""
            tables.append(table)
        return tables

    def get_summary_text(self, prompt: str) -> LlmResponse:
        return self.get_llm_response(prompt)

    def get_summary_review(self, prompt: str) -> LlmResponse:
        return self.get_llm_response(prompt)

    def get_recommendations(self, prompt: str) -> LlmResponse:
        return self.get_llm_response(prompt)

    def get_repo_report(self, repo: RepoStats) -> str:
        # Render the appendix for a single repo
        repo_template = self.env.get_template('repo_appendix.md.j2')
        return repo_template.render(repo=repo)

    def get_llm_response(self, prompt: str) -> LlmResponse:
        response = completion(
            model=self.get_litellm_model(),
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides a professional technical review of github repository information."},
                {"role": "developer", "content": "The user will always require your response to be in well structured markdown for clarity."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        cost = self.get_cost(response)
        tokens = response.usage.total_tokens

        return LlmResponse(
            message=self.trim_markdown(response["choices"][0]["message"]["content"]),
            model=self.model_name,
            cost=cost,
            tokens=tokens,
        )

    def trim_markdown(self, text: str) -> str:
        return text.replace("```markdown", "").replace("```text", "").replace("```json", "").replace("```", "").strip()

    def get_cost(self, response: dict) -> float:
        # the response cost can be a little erratic, so we'll just catch any weirdness and set it to 0 if it's gubbed
        try:
            cost = round(response._hidden_params["response_cost"], 5)
        except:
            cost = 0.0
        if not cost:
            cost = 0.0
        return cost
