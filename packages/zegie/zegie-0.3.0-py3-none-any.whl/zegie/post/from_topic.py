# Copyright 2025 Clivern
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage


class PostFromTopic:
    """Generate posts from a topic or description using AI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5.2",
        temperature: float = 0.7,
        base_url: Optional[str] = "https://api.openai.com/v1",
    ):
        """
        Initialize the PostFromTopic.

        Args:
            api_key: OpenAI API key.
            model: OpenAI model to use for generation.
            temperature: Temperature for generation (0.0 to 2.0).
            base_url: Base URL for the API.
        """
        kwargs = {
            "openai_api_key": api_key,
            "model": model,
            "temperature": temperature,
            "base_url": base_url,
        }
        self.llm = ChatOpenAI(**kwargs)

    def generate(self, user_prompt: str) -> Dict[str, Any]:
        """
        Generate a post based on a user's natural language prompt.

        Args:
            user_prompt: A natural language prompt describing what to generate
                        (e.g., "generate a casual post for linkedin with a limit 100 characters")

        Returns:
            Dictionary with 'content' (str) and 'token_usage' (dict with 'prompt_tokens',
            'completion_tokens', 'total_tokens').
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content="You are a skilled content creator who generates engaging social media posts and blog content based on user instructions."
                ),
                HumanMessage(
                    content=f"""Follow the user's instructions to create a post:
User Request: {user_prompt}
Generate the post according to the user's specifications:
IMPORTANT: Return ONLY the post content itself. Do NOT include any introductory text, explanations, or quotes around the content. Return the post text directly without any wrapper text."""
                ),
            ]
        )

        messages = prompt.format_messages()
        response = self.llm.invoke(messages)

        token_usage_dict = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        if hasattr(response, "response_metadata") and response.response_metadata:
            token_usage = response.response_metadata.get("token_usage", {})
            token_usage_dict = {
                "prompt_tokens": token_usage.get("prompt_tokens", 0),
                "completion_tokens": token_usage.get("completion_tokens", 0),
                "total_tokens": token_usage.get("total_tokens", 0),
            }

        return {"content": response.content, "token_usage": token_usage_dict}
