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
    def __init__(self, repos: list[RepoStats]):
        self.repos = repos
        self.env = Environment(loader=FileSystemLoader('templates'))


    def get_report(self) -> Report:
        # run the sections below and combine the results into a report
        pass

    def get_summary_stats(self) -> dict:
        # get the stats for each repo and return a summary of the stats
        pass

    def get_summary_tables(self) -> list[str]:
        # get the stats for each repo and return a simplified list the combined stats
        pass

    def get_summary_text(self, prompt: str) -> LlmResponse:
        # build the prompt for the summary text
        # then call the llm with the prompt
        # then return the response
        pass

    def get_summary_review(self, prompt: str) -> LlmResponse:
        # build the prompt for the summary review
        # then call the llm with the prompt
        # then return the response
        pass

    def get_recommendations(self, prompt: str) -> LlmResponse:
        # build the prompt for the recommendations
        # then call the llm with the prompt
        # then return the response
        pass

    def get_repo_report(self, repo: RepoStats) -> str:
        # build the prompt for the repo
        # get the summary etc as above
        # then pull out some of the stats and and add them to the combined report
        # then return the report
        pass

    def get_llm_response(self, prompt: str) -> LlmResponse:
        response = completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000,
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
