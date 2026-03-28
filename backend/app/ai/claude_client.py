import anthropic
from app.config import get_settings


class ClaudeClient:
    """Client for interacting with Claude API."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    async def evaluate(self, prompt: str) -> str:
        """Send an evaluation prompt to Claude and get the response."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return message.content[0].text
