from litellm import completion
from pydantic import BaseModel

class LlmResponse(BaseModel):
    message: str
    cost: float
    tokens: int
    model: str

class BaseAgent:
    def __init__(self, model: str = "o4-mini", provider: str = "openai"):
        self.model = model
        self.provider = provider
        self.model_name = f"{self.provider}/{self.model}"  # litellm expects this format

    def get_llm_response(self, prompt: str) -> LlmResponse:
        response = completion(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
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
