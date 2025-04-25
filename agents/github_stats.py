from agents.base import BaseAgent, LlmResponse

class GithubStatsAgent(BaseAgent):
    # this agent will be used to get the github-provided stats for a given github repo
    def __init__(self, model: str = "o4-mini", provider: str = "openai"):
        super().__init__(model, provider)

    def run(self, prompt: str) -> LlmResponse:
        pass
