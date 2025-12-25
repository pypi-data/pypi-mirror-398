import httpx
from typing import Any, Optional


class OpenrouterAi:
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, token: str):
        self.token = token

    def _auth_headers(self, extra: Optional[dict] = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    def get_credits(self) -> dict[str, Any]:
        response = httpx.get(f"{self.BASE_URL}/credits", headers=self._auth_headers())
        response.raise_for_status()
        return response.json()

    def get_models(self) -> dict[str, Any]:
        response = httpx.get(f"{self.BASE_URL}/models", headers=self._auth_headers())
        response.raise_for_status()
        return response.json()

    def is_model_available(self, model: str) -> bool:
        models_data = self.get_models()
        for m in models_data.get("data", []):
            if m.get("id") == model:
                return True
        return False

    def prompt_structured(
        self,
        *,
        model: str,
        messages: list[dict],
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Send a structured chat prompt to the /api/v1/chat/completions endpoint.
        Only model, messages, and max_tokens are supported.
        """
        data = {"model": model, "messages": messages}
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        response = httpx.post(
            f"{self.BASE_URL}/chat/completions",
            headers=self._auth_headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    def prompt_simplified(
        self,
        *,
        model: str,
        prompt: str,
    ) -> dict[str, Any]:
        """
        Send a simple text-only prompt to the /api/v1/completions endpoint.
        Only model and prompt are supported.
        """
        data = {"model": model, "prompt": prompt}
        response = httpx.post(
            f"{self.BASE_URL}/completions",
            headers=self._auth_headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()


# TODO: get_image_description -> padaryt prompta per kuri aprasytu perduota img.


if __name__ == "__main__":
    token = "YOUR_OPENAPI_API_KEY"
    model = "google/gemini-2.5-flash"
    client = OpenrouterAi(token=token)

    # Step 1: Check credits
    credits = client.get_credits()
    print("Credits:", credits)

    # Step 2: Check if model is available
    if not client.is_model_available(model):
        print(f"Model '{model}' is not available.")
        exit(1)
    print(f"Model '{model}' is available.")

    # Step 3: Structured prompt example
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Answer concisely and clearly.",
        },
        {
            "role": "user",
            "content": "I'm planning a trip to Japan for two weeks. What are the top 5 must-see places and why? Please include a mix of cultural, historical, and natural attractions.",
        },
    ]
    result = client.prompt_structured(model=model, messages=messages, max_tokens=300)
    print("Prompt result (structured):", result)

    # Step 4: Simplified prompt example
    simple_model = model  # or use a different model if desired
    simple_prompt = "Write a short poem about the sunrise."
    simple_result = client.prompt_simplified(model=simple_model, prompt=simple_prompt)
    print("Prompt result (simplified):", simple_result)
