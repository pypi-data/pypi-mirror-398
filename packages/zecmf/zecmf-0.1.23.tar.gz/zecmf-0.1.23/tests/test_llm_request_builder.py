"""Tests for LLM request builder with Jinja2 templates and JSON validation."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import jsonschema
import pytest

from zecmf.clients.llm import (
    CompletionChoice,
    CompletionMessage,
    CompletionModelInfo,
    CompletionResponse,
    CompletionUsage,
    LLMClient,
)
from zecmf.clients.llm_request_builder import LLMRequestBuilder


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    return MagicMock(spec=LLMClient)


@pytest.fixture
def builder(mock_llm_client: MagicMock) -> LLMRequestBuilder:
    """Create a builder instance."""
    return LLMRequestBuilder(mock_llm_client)


@pytest.fixture
def sample_templates(tmp_path: Path) -> dict[str, str]:
    """Create sample Jinja2 templates for testing."""
    system_template = tmp_path / "system.j2"
    system_template.write_text("You are a {{ role }}.")

    user_template = tmp_path / "user.j2"
    user_template.write_text("Please {{ action }} the following: {{ content }}")

    assistant_template = tmp_path / "assistant.j2"
    assistant_template.write_text("I have {{ action }} the {{ item }}.")

    return {
        "system": str(system_template),
        "user": str(user_template),
        "assistant": str(assistant_template),
    }


@pytest.fixture
def sample_schema(tmp_path: Path) -> str:
    """Create a sample JSON schema for testing."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name", "age"],
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))
    return str(schema_path)


def create_mock_response(content: str) -> CompletionResponse:
    """Create a mock completion response."""
    return CompletionResponse(
        id="test-id",
        model=CompletionModelInfo(
            id=1,
            name="test-model",
            provider="test-provider",
        ),
        choices=[
            CompletionChoice(
                index=0,
                message=CompletionMessage(role="assistant", content=content),
                finish_reason="stop",
            )
        ],
        usage=CompletionUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        ),
        created=1234567890,
    )


def test_system_message_with_template(
    builder: LLMRequestBuilder,
    sample_templates: dict[str, str],
    mock_llm_client: MagicMock,
) -> None:
    """Test adding a system message with template."""
    builder.system_message(sample_templates["system"], {"role": "helpful assistant"})
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response(
        "Hello, world!"
    )

    result = builder.execute()

    assert result == "Hello, world!"
    call_args = mock_llm_client.create_completion.call_args[0][0]
    assert len(call_args.messages) == 1
    assert call_args.messages[0].role == "system"
    assert call_args.messages[0].content == "You are a helpful assistant."


def test_user_message_with_template(
    builder: LLMRequestBuilder,
    sample_templates: dict[str, str],
    mock_llm_client: MagicMock,
) -> None:
    """Test adding a user message with template."""
    builder.user_message(
        sample_templates["user"],
        {"action": "analyze", "content": "data"},
    )
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response("Analysis")

    result = builder.execute()

    assert result == "Analysis"
    call_args = mock_llm_client.create_completion.call_args[0][0]
    assert len(call_args.messages) == 1
    assert call_args.messages[0].role == "user"
    assert call_args.messages[0].content == "Please analyze the following: data"


def test_system_message_text(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test adding a system message with direct text."""
    builder.system_message_text("You are a helpful assistant.")
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response("Response")

    builder.execute()

    call_args = mock_llm_client.create_completion.call_args[0][0]
    assert call_args.messages[0].role == "system"
    assert call_args.messages[0].content == "You are a helpful assistant."


def test_user_message_text(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test adding a user message with direct text."""
    builder.user_message_text("Hello!")
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response("Response")

    builder.execute()

    call_args = mock_llm_client.create_completion.call_args[0][0]
    assert call_args.messages[0].role == "user"
    assert call_args.messages[0].content == "Hello!"


def test_multiple_messages(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test adding multiple messages."""
    expected_message_count = 3

    builder.system_message_text("You are helpful.")
    builder.user_message_text("Question 1")
    builder.user_message_text("Question 2")
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response("Answer")

    builder.execute()

    call_args = mock_llm_client.create_completion.call_args[0][0]
    assert len(call_args.messages) == expected_message_count
    assert call_args.messages[0].role == "system"
    assert call_args.messages[1].role == "user"
    assert call_args.messages[2].role == "user"


def test_method_chaining(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test that methods return self for chaining."""
    result = (
        builder.system_message_text("System").user_message_text("User").model("gpt-4")
    )

    assert result is builder


def test_execute_without_messages(builder: LLMRequestBuilder) -> None:
    """Test that execute raises error without messages."""
    builder.model("gpt-4")

    with pytest.raises(ValueError, match="At least one message is required"):
        builder.execute()


def test_execute_without_model(builder: LLMRequestBuilder) -> None:
    """Test that execute raises error without model."""
    builder.user_message_text("Hello")

    with pytest.raises(ValueError, match="Model display name is required"):
        builder.execute()


def test_execute_json_direct(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test execute_json with direct JSON response."""
    builder.user_message_text("Give me JSON")
    builder.model("gpt-4")

    json_response = '{"name": "John", "age": 30}'
    mock_llm_client.create_completion.return_value = create_mock_response(json_response)

    result = builder.execute_json()

    assert result == {"name": "John", "age": 30}


def test_execute_json_in_markdown_json_block(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test execute_json with JSON in markdown json code block."""
    builder.user_message_text("Give me JSON")
    builder.model("gpt-4")

    response = '```json\n{"name": "Jane", "age": 25}\n```'
    mock_llm_client.create_completion.return_value = create_mock_response(response)

    result = builder.execute_json()

    assert result == {"name": "Jane", "age": 25}


def test_execute_json_in_markdown_plain_block(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test execute_json with JSON in plain markdown code block."""
    builder.user_message_text("Give me JSON")
    builder.model("gpt-4")

    response = '```\n{"name": "Bob", "age": 35}\n```'
    mock_llm_client.create_completion.return_value = create_mock_response(response)

    result = builder.execute_json()

    assert result == {"name": "Bob", "age": 35}


def test_execute_json_in_backticks(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test execute_json with JSON in backticks."""
    builder.user_message_text("Give me JSON")
    builder.model("gpt-4")

    response = '`{"name": "Alice", "age": 28}`'
    mock_llm_client.create_completion.return_value = create_mock_response(response)

    result = builder.execute_json()

    assert result == {"name": "Alice", "age": 28}


def test_execute_json_with_validation(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock, sample_schema: str
) -> None:
    """Test execute_json with schema validation."""
    builder.user_message_text("Give me JSON")
    builder.model("gpt-4")
    builder.expect_json(sample_schema)

    json_response = '{"name": "John", "age": 30}'
    mock_llm_client.create_completion.return_value = create_mock_response(json_response)

    result = builder.execute_json()

    assert result == {"name": "John", "age": 30}


def test_execute_json_validation_failure(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock, sample_schema: str
) -> None:
    """Test execute_json with schema validation failure."""
    builder.user_message_text("Give me JSON")
    builder.model("gpt-4")
    builder.expect_json(sample_schema)

    # Invalid: missing required field "age"
    json_response = '{"name": "John"}'
    mock_llm_client.create_completion.return_value = create_mock_response(json_response)

    with pytest.raises(jsonschema.ValidationError):
        builder.execute_json()


def test_execute_json_invalid_json(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test execute_json with invalid JSON."""
    builder.user_message_text("Give me JSON")
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response(
        "This is not JSON"
    )

    with pytest.raises(ValueError, match="Could not extract valid JSON from response"):
        builder.execute_json()


def test_template_not_found(builder: LLMRequestBuilder) -> None:
    """Test that FileNotFoundError is raised for missing template."""
    with pytest.raises(FileNotFoundError):
        builder.system_message("/nonexistent/template.j2", {})


def test_empty_context(
    builder: LLMRequestBuilder,
    sample_templates: dict[str, str],
    mock_llm_client: MagicMock,
) -> None:
    """Test template rendering with empty context."""
    # Create a template without variables
    template_path = Path(sample_templates["system"]).parent / "no_vars.j2"
    template_path.write_text("Static content")

    builder.system_message(str(template_path))
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response("Response")

    builder.execute()

    call_args = mock_llm_client.create_completion.call_args[0][0]
    assert call_args.messages[0].content == "Static content"


def test_model_display_name_set(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test that model display name is correctly set."""
    builder.user_message_text("Test")
    builder.model("claude-3-opus")

    mock_llm_client.create_completion.return_value = create_mock_response("Response")

    builder.execute()

    call_args = mock_llm_client.create_completion.call_args[0][0]
    assert call_args.model_display_name == "claude-3-opus"


def test_no_completion_choices(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test error handling when no completion choices are returned."""
    builder.user_message_text("Test")
    builder.model("gpt-4")

    # Create response with empty choices
    response = CompletionResponse(
        id="test-id",
        model=CompletionModelInfo(id=1, name="test", provider="test"),
        choices=[],
        usage=CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        created=1234567890,
    )
    mock_llm_client.create_completion.return_value = response

    with pytest.raises(ValueError, match="No completion choices returned"):
        builder.execute()


def test_assistant_message_with_template(
    builder: LLMRequestBuilder,
    sample_templates: dict[str, str],
    mock_llm_client: MagicMock,
) -> None:
    """Test adding an assistant message with template."""
    builder.assistant_message(
        sample_templates["assistant"],
        {"action": "analyzed", "item": "request"},
    )
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response("Response")

    result = builder.execute()

    assert result == "Response"
    call_args = mock_llm_client.create_completion.call_args[0][0]
    assert len(call_args.messages) == 1
    assert call_args.messages[0].role == "assistant"
    assert call_args.messages[0].content == "I have analyzed the request."


def test_assistant_message_text(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test adding an assistant message with direct text."""
    builder.assistant_message_text("I understand your request.")
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response("Response")

    builder.execute()

    call_args = mock_llm_client.create_completion.call_args[0][0]
    assert call_args.messages[0].role == "assistant"
    assert call_args.messages[0].content == "I understand your request."


def test_multi_turn_conversation_with_assistant(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test multi-turn conversation with assistant messages."""
    expected_message_count = 5

    builder.system_message_text("You are a helpful assistant.")
    builder.user_message_text("What is 2+2?")
    builder.assistant_message_text("2+2 equals 4.")
    builder.user_message_text("What about 3+3?")
    builder.assistant_message_text("Let me calculate that.")
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response(
        "3+3 equals 6."
    )

    builder.execute()

    call_args = mock_llm_client.create_completion.call_args[0][0]
    assert len(call_args.messages) == expected_message_count
    assert call_args.messages[0].role == "system"
    assert call_args.messages[1].role == "user"
    assert call_args.messages[2].role == "assistant"
    assert call_args.messages[3].role == "user"
    assert call_args.messages[4].role == "assistant"


def test_message_order_preservation(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock
) -> None:
    """Test that message order is preserved across different roles."""
    builder.user_message_text("First user message")
    builder.assistant_message_text("First assistant response")
    builder.user_message_text("Second user message")
    builder.system_message_text("System instruction")
    builder.assistant_message_text("Second assistant response")
    builder.model("gpt-4")

    mock_llm_client.create_completion.return_value = create_mock_response("Done")

    builder.execute()

    call_args = mock_llm_client.create_completion.call_args[0][0]
    messages = call_args.messages

    assert messages[0].role == "user"
    assert messages[0].content == "First user message"
    assert messages[1].role == "assistant"
    assert messages[1].content == "First assistant response"
    assert messages[2].role == "user"
    assert messages[2].content == "Second user message"
    assert messages[3].role == "system"
    assert messages[3].content == "System instruction"
    assert messages[4].role == "assistant"
    assert messages[4].content == "Second assistant response"


def test_assistant_message_in_json_workflow(
    builder: LLMRequestBuilder, mock_llm_client: MagicMock, sample_schema: str
) -> None:
    """Test that assistant messages work correctly with JSON extraction."""
    builder.system_message_text("You produce JSON.")
    builder.user_message_text("Give me a person object.")
    builder.assistant_message_text("I will provide that.")
    builder.model("gpt-4")
    builder.expect_json(sample_schema)

    json_response = '{"name": "Jane", "age": 30}'
    mock_llm_client.create_completion.return_value = create_mock_response(json_response)

    result = builder.execute_json()

    assert result == {"name": "Jane", "age": 30}
    call_args = mock_llm_client.create_completion.call_args[0][0]
    expected_message_count = 3  # system + user + assistant
    assert len(call_args.messages) == expected_message_count
    assert call_args.messages[2].role == "assistant"
