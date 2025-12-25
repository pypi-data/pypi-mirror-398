"""LLM request builder with Jinja2 template support and JSON validation.

This module provides a builder pattern for constructing LLM completion requests with:
- Jinja2 template rendering for message prompts
- Support for system, user, and assistant message types
- Automatic JSON extraction from responses (plain, backticks, etc.)
- JSON Schema validation of LLM responses
"""

import json
import re
from pathlib import Path
from typing import Any

import jsonschema
from jinja2 import Environment, FileSystemLoader, Template

from zecmf.clients.llm import CompletionMessage, CompletionRequest, LLMClient


class LLMRequestBuilder:
    """Builder for constructing LLM completion requests with template support."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the LLM request builder.

        Args:
            llm_client: The LLM client instance to use for requests.

        """
        self._llm_client = llm_client
        self._messages: list[CompletionMessage] = []
        self._model_display_name: str | None = None
        self._json_schema: dict[str, Any] | None = None

    def system_message(
        self, template_path: str, context: dict[str, Any] | None = None
    ) -> "LLMRequestBuilder":
        """Add a system message using a Jinja2 template.

        Args:
            template_path: Path to the Jinja2 template file.
            context: Dictionary of variables to pass to the template.

        Returns:
            Self for method chaining.

        """
        content = self._render_template(template_path, context or {})
        self._messages.append(CompletionMessage(role="system", content=content))
        return self

    def user_message(
        self, template_path: str, context: dict[str, Any] | None = None
    ) -> "LLMRequestBuilder":
        """Add a user message using a Jinja2 template.

        Args:
            template_path: Path to the Jinja2 template file.
            context: Dictionary of variables to pass to the template.

        Returns:
            Self for method chaining.

        """
        content = self._render_template(template_path, context or {})
        self._messages.append(CompletionMessage(role="user", content=content))
        return self

    def system_message_text(self, content: str) -> "LLMRequestBuilder":
        """Add a system message with direct text content.

        Args:
            content: The message content.

        Returns:
            Self for method chaining.

        """
        self._messages.append(CompletionMessage(role="system", content=content))
        return self

    def user_message_text(self, content: str) -> "LLMRequestBuilder":
        """Add a user message with direct text content.

        Args:
            content: The message content.

        Returns:
            Self for method chaining.

        """
        self._messages.append(CompletionMessage(role="user", content=content))
        return self

    def assistant_message(
        self, template_path: str, context: dict[str, Any] | None = None
    ) -> "LLMRequestBuilder":
        """Add an assistant message using a Jinja2 template.

        Args:
            template_path: Path to the Jinja2 template file.
            context: Dictionary of variables to pass to the template.

        Returns:
            Self for method chaining.

        """
        content = self._render_template(template_path, context or {})
        self._messages.append(CompletionMessage(role="assistant", content=content))
        return self

    def assistant_message_text(self, content: str) -> "LLMRequestBuilder":
        """Add an assistant message with direct text content.

        Args:
            content: The message content.

        Returns:
            Self for method chaining.

        """
        self._messages.append(CompletionMessage(role="assistant", content=content))
        return self

    def model(self, display_name: str) -> "LLMRequestBuilder":
        """Set the model to use for the completion.

        Args:
            display_name: The display name of the model.

        Returns:
            Self for method chaining.

        """
        self._model_display_name = display_name
        return self

    def expect_json(self, schema_path: str) -> "LLMRequestBuilder":
        """Configure JSON response validation with a JSON Schema.

        Args:
            schema_path: Path to the JSON Schema file.

        Returns:
            Self for method chaining.

        """
        schema_file = Path(schema_path)
        with schema_file.open("r", encoding="utf-8") as f:
            self._json_schema = json.load(f)
        return self

    def execute(self) -> str:
        """Execute the completion request and return the response content.

        Returns:
            The response content as plain text.

        Raises:
            ValueError: If required parameters are missing.

        """
        if not self._messages:
            raise ValueError("At least one message is required")
        if not self._model_display_name:
            raise ValueError("Model display name is required")

        request = CompletionRequest(
            messages=self._messages,
            model_display_name=self._model_display_name,
        )

        response = self._llm_client.create_completion(request)

        if not response.choices:
            raise ValueError("No completion choices returned")

        return response.choices[0].message.content

    def execute_json(self) -> dict[str, Any]:
        """Execute the completion request and return validated JSON response.

        Returns:
            The parsed and validated JSON response.

        Raises:
            ValueError: If JSON cannot be extracted or validation fails.
            jsonschema.ValidationError: If JSON doesn't match schema.

        """
        content = self.execute()
        json_data = self._extract_json(content)

        if self._json_schema is not None:
            jsonschema.validate(instance=json_data, schema=self._json_schema)

        return json_data

    def _render_template(self, template_path: str, context: dict[str, Any]) -> str:
        """Render a Jinja2 template with the given context.

        Args:
            template_path: Path to the template file.
            context: Variables to pass to the template.

        Returns:
            The rendered template content.

        """
        template_file = Path(template_path)

        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        # If the template path is absolute, use it directly
        if template_file.is_absolute():
            env = Environment(
                loader=FileSystemLoader(str(template_file.parent)),
                autoescape=False,  # noqa: S701 - LLM prompts are not HTML
            )
            template = env.get_template(template_file.name)
        else:
            # For relative paths, load directly
            with template_file.open("r", encoding="utf-8") as f:
                template = Template(f.read())

        return template.render(**context)

    def _extract_json(self, content: str) -> dict[str, Any]:
        """Extract JSON from LLM response content.

        Supports various formats:
        - Direct JSON
        - JSON in markdown code blocks (```json ... ```)
        - JSON in plain code blocks (``` ... ```)
        - JSON in backticks (` ... `)

        Args:
            content: The response content.

        Returns:
            The parsed JSON data.

        Raises:
            ValueError: If JSON cannot be extracted or parsed.

        """
        # Try to parse directly first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code blocks
        patterns = [
            r"```json\s*(.*?)\s*```",  # ```json ... ```
            r"```\s*(.*?)\s*```",  # ``` ... ```
            r"`(.*?)`",  # ` ... `
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    continue

        raise ValueError("Could not extract valid JSON from response")
