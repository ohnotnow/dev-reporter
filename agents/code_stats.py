from agents.base import BaseAgent, LlmResponse

class CodeStatsAgent(BaseAgent):
    # this agent will be used to get the LOC, COCOMO, and other stats for a given codebase
    def __init__(self, model: str = "o4-mini", provider: str = "openai"):
        super().__init__(model, provider)

    def run(self, prompt: str) -> LlmResponse:
        pass
