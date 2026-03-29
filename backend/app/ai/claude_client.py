import anthropic
from typing import AsyncGenerator
from app.config import get_settings


class ClaudeClient:
    """Client for interacting with Claude API."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    async def evaluate(self, prompt: str) -> str:
        """Send an evaluation prompt to Claude and get the response."""
        message = await self.async_client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0,  # Deterministic output for consistent scoring
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return message.content[0].text

    async def evaluate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream evaluation response from Claude."""
        async with self.async_client.messages.stream(
            model=self.model,
            max_tokens=4096,
            temperature=0,  # Deterministic output for consistent scoring
            messages=[
                {"role": "user", "content": prompt}
            ],
        ) as stream:
            async for text in stream.text_stream:
                yield text
