"""
Tests for the Agent class (AgentContext API: run/execute, unwind, health).
"""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from agent_sdk import Agent, AgentConfig, AgentContext, AgentRequest


class TestAgent:
    """Test cases for the Agent class"""

    @pytest.fixture
    def mock_run_function(self):
        """Mock execution function for testing (takes AgentContext, returns None)."""

        def mock_func(agent: AgentContext) -> None:
            agent.log("Test execution")

        return mock_func

    @pytest.fixture
    def mock_unwind_function(self):
        """Mock unwind function for testing (takes AgentContext + positions, returns None)."""

        def mock_func(agent: AgentContext, positions: list) -> None:
            agent.log(f"Test unwind: {len(positions)} positions")

        return mock_func

    @pytest.fixture
    def sample_current_positions(self):
        """Sample current positions for testing."""
        return [
            {
                "network": "ethereum:1",
                "assetAddress": "0x1234567890abcdef",
                "tokenId": None,
                "avgUnitCost": "100.00",
                "currentQty": "1.5",
            }
        ]

    def test_agent_initialization(self, mock_run_function):
        """Test basic agent initialization."""
        agent = Agent(run_function=mock_run_function)

        assert agent.run_function == mock_run_function
        assert agent.unwind_function is None
        assert agent.health_check_function is not None
        assert agent.config is not None
        assert agent.logger is not None

    def test_agent_initialization_with_unwind_function(
        self, mock_run_function, mock_unwind_function
    ):
        """Test agent initialization with an unwind handler."""
        agent = Agent(
            run_function=mock_run_function, unwind_function=mock_unwind_function
        )

        assert agent.run_function == mock_run_function
        assert agent.unwind_function == mock_unwind_function

    def test_agent_initialization_with_config(self, mock_run_function):
        """Test agent initialization with a custom config."""
        config = AgentConfig(
            title="Test Agent",
            description="A test agent",
            version="2.0.0",
        )

        agent = Agent(run_function=mock_run_function, config=config)

        assert agent.config.title == "Test Agent"
        assert agent.config.description == "A test agent"
        assert agent.config.version == "2.0.0"

    def test_agent_initialization_missing_run_function(self):
        """Test that the Agent enforces a required run_function."""
        with pytest.raises(TypeError):
            Agent()  # type: ignore[call-arg]

    def test_process_request_success(self, mock_run_function, sample_current_positions):
        """Test a successful `process_request` call (execute)."""
        agent = Agent(run_function=mock_run_function)

        result = agent.process_request(
            session_id=123,
            session_wallet_address="0x1234567890abcdef",
            current_positions=sample_current_positions,
            command="execute",
        )

        assert result["success"] is True

    def test_process_request_with_error(self, sample_current_positions):
        """Test `process_request` error handling."""

        def error_function(agent: AgentContext) -> None:
            raise Exception("Test error")

        agent = Agent(run_function=error_function)

        result = agent.process_request(
            session_id=123,
            session_wallet_address="0x1234567890abcdef",
            current_positions=sample_current_positions,
            command="execute",
        )

        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]

    def test_default_health_function(self, mock_run_function):
        """Test the default health check response shape."""
        agent = Agent(run_function=mock_run_function)

        result = agent.health_check_function()

        assert isinstance(result, dict)
        assert result["status"] == "healthy"

    def test_get_handler(self, mock_run_function):
        """Test that a handler function is returned."""
        agent = Agent(run_function=mock_run_function)
        handler = agent.get_handler()
        assert callable(handler)

    def test_get_worker_export(self, mock_run_function):
        """Test that a worker export is returned (FastAPI app or handler)."""
        agent = Agent(run_function=mock_run_function)
        worker_export = agent.get_worker_export()
        assert worker_export is not None

    @patch("agent_sdk.agent.FASTAPI_AVAILABLE", False)
    def test_agent_without_fastapi(self, mock_run_function):
        """Test agent initialization when FastAPI is not available."""
        agent = Agent(run_function=mock_run_function)
        assert agent.app is None

    @patch("agent_sdk.agent.FASTAPI_AVAILABLE", True)
    def test_agent_with_fastapi(self, mock_run_function):
        """Test agent initialization when FastAPI is available."""
        agent = Agent(run_function=mock_run_function)
        assert agent.app is not None

    def test_agent_dict_style_initialization(self, mock_run_function):
        """Test Agent initialization via dict-style parameters."""
        params = {
            "run_function": mock_run_function,
            "title": "Test Agent",
            "description": "A test agent",
        }

        agent = Agent(**params)

        assert agent.run_function == mock_run_function
        assert agent.config.title == "Test Agent"
        assert agent.config.description == "A test agent"


class TestAgentIntegration:
    """Integration-ish tests for Agent request processing."""

    def test_full_agent_workflow(self):
        """Test a complete basic run workflow via `process_request`."""

        def execution_func(agent: AgentContext) -> None:
            agent.log(f"Processed session {agent.sessionId}")

        agent = Agent(run_function=execution_func)

        exec_result = agent.process_request(
            session_id=123,
            session_wallet_address="0x1234567890abcdef",
            current_positions=[],
            command="execute",
        )

        assert exec_result["success"] is True


class TestAgentLambdaHandler:
    """Test cases for Lambda/handler functionality (direct invocation + HTTP event shapes)."""

    @pytest.fixture
    def mock_run_function(self):
        """Mock execution function for handler tests."""

        def mock_func(agent: AgentContext) -> None:
            agent.log("Test execution")

        return mock_func

    def test_handler_http_event(self, mock_run_function):
        """Test handler with an HTTP event (should use Mangum when FastAPI is available)."""
        with patch("agent_sdk.agent.FASTAPI_AVAILABLE", True):
            agent = Agent(run_function=mock_run_function)

            mock_mangum_response = {"statusCode": 200, "body": '{"success": true}'}
            agent._handler = MagicMock(return_value=mock_mangum_response)

            http_event = {
                "httpMethod": "POST",
                "path": "/run",
                "body": '{"sessionId": 123, "sessionWalletAddress": "0x123", "currentPositions": []}',
                "headers": {"Content-Type": "application/json"},
            }

            handler_func = agent.get_handler()
            result = handler_func(http_event, {})

            assert result == mock_mangum_response

    def test_handler_direct_invocation_run(self, mock_run_function):
        """Test handler with direct invocation for /run."""
        agent = Agent(run_function=mock_run_function)

        event = {
            "body": json.dumps(
                {
                    "sessionId": 123,
                    "sessionWalletAddress": "0x1234567890abcdef",
                    "currentPositions": [],
                }
            ),
            "rawPath": "/run",
        }

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 200
        response_body = json.loads(result["body"])
        assert response_body["success"] is True

    def test_handler_direct_invocation_execute(self, mock_run_function):
        """Test handler with direct invocation for /execute (backward compatibility)."""
        agent = Agent(run_function=mock_run_function)

        event = {
            "body": json.dumps(
                {
                    "sessionId": 123,
                    "sessionWalletAddress": "0x1234567890abcdef",
                    "currentPositions": [],
                }
            ),
            "rawPath": "/execute",
        }

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 200
        response_body = json.loads(result["body"])
        assert response_body["success"] is True

    def test_handler_direct_invocation_unwind(self, mock_run_function):
        """Test handler with direct invocation for /unwind."""
        called = {"unwind": 0}

        def unwind(agent: AgentContext, positions: list) -> None:
            assert isinstance(positions, list)
            called["unwind"] += 1

        agent = Agent(run_function=mock_run_function, unwind_function=unwind)

        event = {
            "body": json.dumps(
                {
                    "sessionId": 123,
                    "sessionWalletAddress": "0x1234567890abcdef",
                    "currentPositions": [],
                }
            ),
            "rawPath": "/unwind",
        }

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 200
        response_body = json.loads(result["body"])
        assert response_body["success"] is True
        assert called["unwind"] == 1

    def test_handler_direct_invocation_health(self, mock_run_function):
        """Test handler with /health."""
        agent = Agent(run_function=mock_run_function)

        event = {"body": "{}", "rawPath": "/health"}

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 200
        response_body = json.loads(result["body"])
        assert response_body["status"] == "healthy"

    def test_handler_missing_parameters(self, mock_run_function):
        """Test handler validation errors for missing required parameters."""
        agent = Agent(run_function=mock_run_function)

        event = {
            "body": json.dumps({}),  # Missing sessionId and sessionWalletAddress
            "rawPath": "/run",
        }

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 400
        assert "sessionId" in result["body"]

    def test_handler_base64_encoded_body(self, mock_run_function):
        """Test handler with base64 encoded request body."""
        agent = Agent(run_function=mock_run_function)

        body_data = {
            "sessionId": 123,
            "sessionWalletAddress": "0x123",
            "currentPositions": [],
        }
        encoded_body = base64.b64encode(json.dumps(body_data).encode()).decode()

        event = {"body": encoded_body, "isBase64Encoded": True, "rawPath": "/run"}

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 200

    def test_handler_error_handling(self):
        """Test handler surfaces exceptions as a 500 response."""

        def error_function(agent: AgentContext) -> None:
            raise Exception("Test error")

        agent = Agent(run_function=error_function)

        event = {
            "body": json.dumps(
                {
                    "sessionId": 123,
                    "sessionWalletAddress": "0x123",
                    "currentPositions": [],
                }
            ),
            "rawPath": "/run",
        }

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "Test error" in body["error"]

    def test_is_http_event(self, mock_run_function):
        """Test the `_is_http_event` helper with multiple event shapes."""
        agent = Agent(run_function=mock_run_function)

        assert (
            agent._is_http_event({"httpMethod": "POST", "headers": {}, "path": "/test"})
            is True
        )
        assert agent._is_http_event({"httpMethod": "POST"}) is False
        assert agent._is_http_event({"requestContext": {"http": {}}}) is True
        assert agent._is_http_event({"requestContext": {}}) is False
        assert agent._is_http_event({"body": "{}"}) is False

    def test_parse_event_body_json_string(self, mock_run_function):
        """Test `_parse_event_body` with a JSON string body."""
        agent = Agent(run_function=mock_run_function)
        event = {"body": '{"key": "value"}'}
        assert agent._parse_event_body(event) == {"key": "value"}

    def test_parse_event_body_invalid_json(self, mock_run_function):
        """Test `_parse_event_body` with invalid JSON."""
        agent = Agent(run_function=mock_run_function)
        event = {"body": "invalid json"}
        assert agent._parse_event_body(event) == {}

    def test_parse_event_body_dict(self, mock_run_function):
        """Test `_parse_event_body` when body is already a dict."""
        agent = Agent(run_function=mock_run_function)
        event = {"body": {"key": "value"}}
        assert agent._parse_event_body(event) == {"key": "value"}

    def test_parse_event_body_base64_error(self, mock_run_function):
        """Test `_parse_event_body` with base64 decode errors."""
        agent = Agent(run_function=mock_run_function)
        event = {"body": "invalid_base64", "isBase64Encoded": True}
        assert agent._parse_event_body(event) == {}

    def test_extract_command(self, mock_run_function):
        """Test `_extract_command` from rawPath formats."""
        agent = Agent(run_function=mock_run_function)

        assert agent._extract_command({"rawPath": "/run"}) == "run"
        assert agent._extract_command({"rawPath": "/execute"}) == "execute"
        assert agent._extract_command({"rawPath": "/unwind"}) == "unwind"

        runtime_path = "/2015-03-31/functions/function/invocations/health"
        assert agent._extract_command({"rawPath": runtime_path}) == "health"
        assert agent._extract_command({}) == ""


class TestAgentCommandProcessing:
    """Test cases for command processing (`process_request`) and unwind signatures."""

    @pytest.fixture
    def mock_run_function(self):
        """Mock execution function for command processing tests."""

        def mock_func(agent: AgentContext) -> None:
            agent.log("Executed")

        return mock_func

    def test_process_request_unwind_command(self, mock_run_function):
        """Test `process_request` with the unwind command."""
        calls = {"unwind": 0}

        def unwind(agent: AgentContext, positions: list) -> None:
            calls["unwind"] += 1

        agent = Agent(run_function=mock_run_function, unwind_function=unwind)

        result = agent.process_request(
            123, "0x123", current_positions=[], command="unwind"
        )

        assert result["success"] is True
        assert calls["unwind"] == 1

    def test_process_request_unwind_defaults_when_missing_unwind(
        self, mock_run_function
    ):
        """Test that unwind defaults to the SDK-provided unwind implementation when missing."""
        agent = Agent(run_function=mock_run_function)
        result = agent.process_request(
            123, "0x123", current_positions=[], command="unwind"
        )
        assert result["success"] is True

    def test_process_request_stop_is_unknown(self, mock_run_function):
        """Test that stop is not a supported command in the new interface."""
        agent = Agent(run_function=mock_run_function)
        result = agent.process_request(
            123, "0x123", current_positions=[], command="stop"
        )
        assert result["success"] is False
        assert "Unknown command" in result["error"]

    def test_unwind_signature_positions_only(self, mock_run_function):
        """Unwind can be defined as `unwind(positions)` and will receive a list."""
        seen = {"positions": None}

        def unwind(positions: list) -> None:
            seen["positions"] = positions

        agent = Agent(run_function=mock_run_function, unwind_function=unwind)
        current_positions = [
            {
                "network": "ethereum:1",
                "assetAddress": "0x1234567890abcdef",
                "tokenId": None,
                "avgUnitCost": "100.00",
                "currentQty": "1.5",
            }
        ]

        result = agent.process_request(
            123, "0x123", current_positions=current_positions, command="unwind"
        )

        assert result["success"] is True
        assert isinstance(seen["positions"], list)
        assert len(seen["positions"]) == 1
        assert getattr(seen["positions"][0], "network", None) == "ethereum:1"

    def test_unwind_signature_agent_only(self, mock_run_function):
        """Unwind can be defined as `unwind(agent)` and will receive an AgentContext."""
        seen = {"agent": None}

        def unwind(agent: AgentContext) -> None:
            seen["agent"] = agent

        agent = Agent(run_function=mock_run_function, unwind_function=unwind)

        result = agent.process_request(
            123, "0x123", current_positions=[], command="unwind"
        )

        assert result["success"] is True
        assert seen["agent"] is not None
        assert getattr(seen["agent"], "sessionId", None) == 123

    def test_unwind_positions_subset_field(self, mock_run_function):
        """If `AgentRequest.unwindPositions` is provided, it is passed as the unwind set."""
        observed: dict[str, int] = {}

        def unwind(agent: AgentContext, positions: list) -> None:
            observed["full"] = len(agent.currentPositions)
            observed["subset"] = len(positions)

        agent = Agent(run_function=mock_run_function, unwind_function=unwind)

        pos1 = {
            "network": "ethereum:1",
            "assetAddress": "0x1111111111111111",
            "tokenId": None,
            "avgUnitCost": "100.00",
            "currentQty": "1.0",
        }
        pos2 = {
            "network": "ethereum:1",
            "assetAddress": "0x2222222222222222",
            "tokenId": None,
            "avgUnitCost": "200.00",
            "currentQty": "2.0",
        }
        request = AgentRequest(
            sessionId=123,
            sessionWalletAddress="0x123",
            currentPositions=[pos1, pos2],
            unwindPositions=[pos1],
        )

        response = agent._execute_unwind_with_job_tracking(request, unwind)

        assert response.success is True
        assert observed["full"] == 2
        assert observed["subset"] == 1

    def test_process_request_health_command(self, mock_run_function):
        """Test `process_request` with the health command."""
        agent = Agent(run_function=mock_run_function)
        result = agent.process_request(
            123, "0x123", current_positions=[], command="health"
        )
        assert result["status"] == "healthy"

    def test_process_request_unknown_command(self, mock_run_function):
        """Test `process_request` with an unknown command returns an error response."""
        agent = Agent(run_function=mock_run_function)
        result = agent.process_request(
            123, "0x123", current_positions=[], command="unknown"
        )
        assert result["success"] is False
        assert "Unknown command" in result["error"]

    def test_process_request_run_command(self, mock_run_function):
        """Test `process_request` with the run command (new standard)."""
        agent = Agent(run_function=mock_run_function)
        result = agent.process_request(
            123, "0x123", current_positions=[], command="run"
        )
        assert result["success"] is True

    def test_process_request_execute_command(self, mock_run_function):
        """Test `process_request` with the execute command (backward compatibility)."""
        agent = Agent(run_function=mock_run_function)
        result = agent.process_request(
            123, "0x123", current_positions=[], command="execute"
        )
        assert result["success"] is True


class TestAgentRunMethod:
    """Test cases for the `Agent.run()` local dev server helper."""

    @pytest.fixture
    def mock_run_function(self):
        """Mock run function for `Agent.run()` tests."""

        def mock_func(agent: AgentContext) -> None:
            pass

        return mock_func

    @patch("agent_sdk.agent.FASTAPI_AVAILABLE", False)
    def test_run_without_fastapi(self, mock_run_function):
        """Test `Agent.run()` behavior when FastAPI is not available."""

        agent = Agent(run_function=mock_run_function)
        agent.run()

    @patch("agent_sdk.agent.FASTAPI_AVAILABLE", True)
    def test_run_without_app(self, mock_run_function):
        """Test `Agent.run()` when FastAPI is available but app is not initialized."""

        agent = Agent(run_function=mock_run_function)
        agent.app = None
        agent.run()

    @patch("agent_sdk.agent.FASTAPI_AVAILABLE", True)
    @patch("uvicorn.run")
    def test_run_with_fastapi(self, mock_uvicorn_run, mock_run_function):
        """Test `Agent.run()` starts Uvicorn when FastAPI app is present."""
        agent = Agent(run_function=mock_run_function)
        agent.run(host="127.0.0.1", port=8080)

        mock_uvicorn_run.assert_called_once_with(
            agent.app, host="127.0.0.1", port=8080, log_config=None
        )


class TestAgentErrorHandling:
    def test_agent_initialization_none_run_function(self):
        """Test that passing None as run_function raises a ValueError."""
        with pytest.raises(ValueError, match="run_function is required"):
            Agent(run_function=None)  # type: ignore[arg-type]

    def test_get_worker_export_without_fastapi(self):
        """Test `get_worker_export` behavior when FastAPI isn't available."""

        def mock_exec(agent: AgentContext) -> None:
            pass

        with patch("agent_sdk.agent.FASTAPI_AVAILABLE", False):
            agent = Agent(run_function=mock_exec)
            result = agent.get_worker_export()
            assert callable(result)
