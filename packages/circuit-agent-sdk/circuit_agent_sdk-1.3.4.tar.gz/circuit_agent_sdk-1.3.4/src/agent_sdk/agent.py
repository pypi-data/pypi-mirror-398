"""
HTTP server wrapper for agent functions.

This module provides the Agent class that exposes agent functions as HTTP endpoints,
supporting both local development via FastAPI and Circuit deployment.

Exposes the following endpoints:
- POST /run — required, calls your execution function
- POST /execute — backward compatibility, maps to run function
- POST /unwind — optional, when an unwind_function is provided
- GET /health — always available
"""

import base64
import inspect
import json
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, Union

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

from .types.common import CurrentPosition
from .utils import get_agent_config_from_pyproject, setup_logging

# FastAPI imports for local development
try:
    from fastapi import FastAPI, HTTPException, Request
    from mangum import Mangum

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# Core models for Agent wrapper
class AgentConfig(BaseModel):
    """Configuration for the Agent"""

    title: str = Field(default="Circuit Agent", description="Agent title")
    description: str = Field(default="A Circuit Agent", description="Agent description")
    version: str = Field(default="1.0.0", description="Agent version")


class AgentRequest(BaseModel):
    """Request structure for agent operations"""

    sessionId: int = Field(..., description="Unique session identifier")
    sessionWalletAddress: str = Field(..., description="Wallet address for the session")
    currentPositions: list[CurrentPosition] = Field(
        default_factory=list,
        description="Current positions allocated to this agent (defaults to empty list)",
    )
    jobId: str | None = Field(None, description="Optional job ID for status tracking")
    executionMode: Literal["auto", "manual", "hybrid"] = Field(
        default="auto",
        description="Execution mode for transaction handling (auto, manual, hybrid)",
    )
    unwindPositions: list[CurrentPosition] | None = Field(
        default=None,
        description=(
            "Optional subset of positions to unwind. If omitted, currentPositions is "
            "treated as the unwind set."
        ),
    )
    model_config = ConfigDict(extra="allow")


class AgentResponse(BaseModel):
    """Response structure for agent operations (run/execute and unwind commands)"""

    success: bool = Field(..., description="Whether the operation was successful")
    error: str | None = Field(None, description="Error message if operation failed")
    message: str | None = Field(
        None, description="Success message if operation succeeded"
    )


class HealthResponse(BaseModel):
    """Response structure for health check operations"""

    status: str = Field(..., description="Health status (healthy/unhealthy)")


class HandlerResponse(BaseModel):
    """Handler response structure for Circuit deployment"""

    statusCode: int = Field(..., description="HTTP status code")
    body: str = Field(..., description="Response body as JSON string")
    headers: dict[str, str] | None = Field(None, description="Response headers")


# Pydantic models for agent contracts
class AgentRequestSchema(BaseModel):
    """Request object for agent functions containing session and wallet information."""

    session_id: int = Field(..., description="Unique session identifier")
    session_wallet_address: str = Field(
        ..., description="Wallet address for the session"
    )
    current_positions: list[CurrentPosition] = Field(
        ..., description="Current positions allocated to this agent"
    )
    job_id: str | None = Field(None, description="Optional job ID for status tracking")
    model_config = ConfigDict(extra="ignore")


class AgentResponseSchema(BaseModel):
    """Standard response format for agent functions (execute/run and unwind commands)."""

    success: bool = Field(..., description="Whether the operation was successful")
    error: str | None = Field(None, description="Error message if operation failed")
    message: str | None = Field(
        None, description="Optional message describing the operation result"
    )


class HealthResponseSchema(BaseModel):
    """Health check response format."""

    status: str = Field(..., description="Health status")


# Import AgentContext type
if TYPE_CHECKING:
    from .agent_context import (
        AgentContext,
        CurrentPosition as AgentContextCurrentPosition,
    )

# Type aliases for function contracts (v1.2 - simplified)
ExecutionFunctionContract = Callable[["AgentContext"], None]
UnwindFunctionContract = Union[  # noqa: UP007 - Callable special forms don't support |
    Callable[["AgentContext", list["AgentContextCurrentPosition"]], None],
    Callable[["AgentContext"], None],
    Callable[[list["AgentContextCurrentPosition"]], None],
]
HealthCheckFunctionContract = Callable[[], dict[str, Any]]


class AgentConfigClass(BaseModel):
    """Configuration object for creating a new agent (v1.2 - simplified)."""

    run_function: ExecutionFunctionContract = Field(
        ...,
        description="Main execution function that implements the agent's core logic",
    )
    unwind_function: UnwindFunctionContract | None = Field(
        None,
        description=(
            "Optional allocation-adjustment function. Called when the agent is asked "
            "to unwind some or all positions."
        ),
    )


class Agent:
    """
    Circuit agent wrapper - handles HTTP requests and routing (v1.2).

    This is used internally by the boilerplate code at the bottom of your agent file.
    You don't need to interact with this class directly - just define your
    run_function and unwind_function.

    Your functions receive an AgentContext object and return None. All error handling
    is automatic - uncaught exceptions are logged and reported to Circuit.

    Example of what you write:
        ```python
        from agent_sdk import AgentContext

        def run_function(agent: AgentContext) -> None:
            agent.log(f"Starting execution for wallet {agent.sessionWalletAddress}")
            agent.memory.set("last_run", str(time.time()))
            # That's it! No need to return anything or handle errors manually

        def unwind_function(agent: AgentContext, positions: list) -> None:
            agent.log(f"Unwinding {len(positions)} positions")
            # Errors are caught automatically

        # The boilerplate code below handles everything else
        ```
    """

    def __init__(
        self,
        run_function: ExecutionFunctionContract,
        config: AgentConfig | None = None,
        base_url: str | None = None,
        unwind_function: UnwindFunctionContract | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Create a new Agent with the provided handlers (v1.2 - simplified).

        Agent functions now receive an AgentContext object and return None.
        All error handling is automatic - uncaught exceptions are logged and
        reported to the backend.

        Args:
            run_function: Main execution function (required) - receives AgentContext, returns None
            config: Optional AgentConfig object
            unwind_function: Optional unwind hook - receives AgentContext (+ positions), returns None
            **kwargs: Additional config parameters
        """
        # Load environment variables from .env file first
        load_dotenv()

        # Set up logging first
        self.logger = setup_logging()

        # Store function references
        self.run_function = run_function
        self.unwind_function = unwind_function
        # Always use default health check (v1.2 - no custom health checks)
        self._health_check_function = self._default_health_check_function

        # Store base URL for SDK operations
        self.base_url = base_url

        # Handle configuration
        config_dict = kwargs
        pyproject_config = get_agent_config_from_pyproject()
        merged_config = {**pyproject_config, **config_dict}

        if config:
            self.config = config
        else:
            self.config = AgentConfig(**merged_config)

        # Validate required functions
        if self.run_function is None:
            raise ValueError("run_function is required")

        # Initialize FastAPI app if available
        self.app: FastAPI | None = None
        self._handler: Mangum | None = None
        if FASTAPI_AVAILABLE:
            self._setup_fastapi()

    def _default_unwind_function(
        self, agent: "AgentContext", positions: list[Any]
    ) -> None:
        """Default unwind function (no-op other than logging)."""
        agent.log(
            f"Unwind requested for session {agent.sessionId} "
            f"(positions={len(positions)}), but no unwind_function was provided"
        )

    def _default_health_check_function(self) -> dict[str, Any]:
        """Default health check function - returns dict matching TypeScript format"""
        return {"status": "healthy"}

    def health_check_function(self) -> dict[str, Any]:
        """
        Health check function that returns a dict matching TypeScript format
        """
        # _health_check_function is never None due to initialization with default
        result = self._health_check_function()
        # The result is always a dict since _default_health_check_function returns dict
        # and user-provided functions are expected to return dict as well
        return result

    def _setup_fastapi(self) -> None:
        """Set up FastAPI application"""
        if not FASTAPI_AVAILABLE:
            return

        self.app = FastAPI(
            title=self.config.title,
            description=self.config.description,
            version=self.config.version,
        )

        # Create Mangum handler for deployment compatibility
        self._handler = Mangum(self.app)

        @self.app.get("/")
        def root() -> dict[str, Any]:
            return {
                "message": f"{self.config.title} is running",
                "mode": "local",
                "version": self.config.version,
            }

        @self.app.get("/health")
        def health() -> dict[str, Any]:
            return self.health_check_function()

        @self.app.post("/run")
        def execute_agent(
            agent_request: AgentRequest, request: Request
        ) -> AgentResponse:
            try:
                authorization_header = request.headers.get("Authorization")
                result = self._execute_with_job_tracking(
                    agent_request, self.run_function, authorization_header
                )
                return result
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Execution error: {str(e)}"
                ) from e

        # Backward compatibility: /execute endpoint maps to run function
        @self.app.post("/execute")
        def execute_agent_legacy(
            agent_request: AgentRequest, request: Request
        ) -> AgentResponse:
            try:
                authorization_header = request.headers.get("Authorization")
                result = self._execute_with_job_tracking(
                    agent_request, self.run_function, authorization_header
                )
                return result
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Execution error: {str(e)}"
                ) from e

        @self.app.post("/unwind")
        def unwind_agent(
            agent_request: AgentRequest, request: Request
        ) -> AgentResponse:
            try:
                authorization_header = request.headers.get("Authorization")
                result = self._execute_unwind_with_job_tracking(
                    agent_request,
                    self.unwind_function or self._default_unwind_function,
                    authorization_header,
                )
                return result
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Unwind error: {str(e)}"
                ) from e

        @self.app.post("/{command}")
        def handle_command(
            command: str, agent_request: AgentRequest, request: Request
        ) -> AgentResponse | dict[str, Any]:
            try:
                authorization_header = request.headers.get("Authorization")
                if command == "execute":
                    result = self._execute_with_job_tracking(
                        agent_request, self.run_function, authorization_header
                    )
                elif command == "unwind":
                    result = self._execute_unwind_with_job_tracking(
                        agent_request,
                        self.unwind_function or self._default_unwind_function,
                        authorization_header,
                    )
                elif command == "health":
                    health_result = self.health_check_function()
                    return health_result
                else:
                    raise HTTPException(
                        status_code=400, detail=f"Unknown command: {command}"
                    )
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Command error: {str(e)}"
                ) from e

        @self.app.get("/{command}")
        def handle_command_get(command: str) -> dict[str, Any]:
            try:
                if command == "health":
                    return self.health_check_function()
                else:
                    raise HTTPException(
                        status_code=400, detail=f"Unknown command: {command}"
                    )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Command error: {str(e)}"
                ) from e

    def process_request(
        self,
        session_id: int,
        session_wallet_address: str,
        current_positions: list[dict[str, Any]],
        command: str = "execute",
        job_id: str | None = None,
        authorization_header: str | None = None,
    ) -> dict[str, Any]:
        """
        Process an agent request

        Args:
            session_id: Session ID
            session_wallet_address: Wallet address
            current_positions: Current positions allocated to this agent
            command: Command to execute
            job_id: Optional job ID for tracking
            authorization_header: Optional Authorization header from incoming request

        Returns:
            Response dictionary
        """
        # Parse currentPositions
        parsed_positions = [CurrentPosition(**pos) for pos in current_positions]

        try:
            if command == "execute" or command == "run":
                request = AgentRequest(
                    sessionId=session_id,
                    sessionWalletAddress=session_wallet_address,
                    currentPositions=parsed_positions,
                    unwindPositions=None,
                    jobId=job_id,
                )
                result = self._execute_with_job_tracking(
                    request, self.run_function, authorization_header
                )
            elif command == "unwind":
                request = AgentRequest(
                    sessionId=session_id,
                    sessionWalletAddress=session_wallet_address,
                    currentPositions=parsed_positions,
                    unwindPositions=None,
                    jobId=job_id,
                )
                result = self._execute_unwind_with_job_tracking(
                    request,
                    self.unwind_function or self._default_unwind_function,
                    authorization_header,
                )
            elif command == "health":
                # Simply call health_check_function which handles all the conversion
                return self.health_check_function()
            else:
                raise ValueError(f"Unknown command: {command}")

            # Convert AgentResponse to dict
            return result.model_dump()

        except Exception as e:
            # Enhanced error logging with more context
            error_msg = self._get_error_message(e)
            self.logger.error(f"Request processing error: {error_msg}")
            self.logger.error(
                f"Session ID: {session_id}, Command: {command}, Job ID: {job_id}"
            )

            # If we have a job_id, report the failure
            if job_id:
                self._update_job_status(
                    session_id,
                    job_id,
                    success=False,
                    error_message=error_msg,
                    authorization_header=authorization_header,
                )

            # Return a proper AgentResponse for consistency
            return AgentResponse(
                success=False,
                error=error_msg,
                message="Request processing failed",
            ).model_dump()

    def _get_error_message(self, error: Exception | None) -> str:
        """
        Safely extract error message from exception with guaranteed fallback.

        This method NEVER raises - always returns a valid string.

        Args:
            error: The exception (or None)

        Returns:
            Clean error message (always succeeds)
        """
        if error is None:
            return "Unknown error"

        try:
            error_type = type(error).__name__
            error_str = str(error) or repr(error)

            # Remove non-printable characters
            error_str = "".join(
                char for char in error_str if char.isprintable() or char in ["\n", "\t"]
            )

            # Combine and limit length
            full_message = f"{error_type}: {error_str}"
            if len(full_message) > 1000:
                full_message = full_message[:997] + "..."

            return full_message

        except Exception:
            # Fallback if extraction fails
            return "Unknown error (details unavailable)"

    def _execute_with_job_tracking(
        self,
        request: AgentRequest,
        function: ExecutionFunctionContract,
        authorization_header: str | None = None,
    ) -> AgentResponse:
        """
        Execute a function with automatic job status tracking (v1.2).

        Creates an AgentContext from the request and passes it to the user function.
        User functions now return None - all error handling is automatic.
        Job tracking is handled entirely by this wrapper - AgentContext doesn't need to know about it.

        This method GUARANTEES that job status will be updated no matter what happens.
        Uses try-finally to ensure status is always set, with multiple retry attempts.

        Args:
            request: The agent request containing jobId for infrastructure tracking
            function: The function to execute (run)
            authorization_header: Optional Authorization header from incoming request

        Returns:
            AgentResponse for HTTP layer (internally generated)
        """
        # Import here to avoid circular import
        from .agent_context import AgentContext, CurrentPosition

        execution_success = False
        execution_error_message: str | None = None

        try:
            # Convert currentPositions to AgentContext format
            current_positions = [
                CurrentPosition(**pos.model_dump()) for pos in request.currentPositions
            ]

            # Create AgentContext - no jobId needed, that's handled by this wrapper
            agent_context = AgentContext(
                sessionId=request.sessionId,
                sessionWalletAddress=request.sessionWalletAddress,
                currentPositions=current_positions,
                executionMode=request.executionMode,
                base_url=self.base_url,
                authorization_header=authorization_header,
            )

            # Execute the user function (no return value expected)
            function(agent_context)

            # If we reach here, execution was successful
            execution_success = True

        except Exception as e:
            # Function threw an uncaught exception - extract error message once
            execution_error_message = self._get_error_message(e)
            execution_success = False

            # Log to console (so dev sees it locally / in cloud logs)
            self.logger.error(
                f"Uncaught exception in agent function: {execution_error_message}"
            )
            self.logger.error(
                f"Session ID: {request.sessionId}, Job ID: {request.jobId}"
            )

        finally:
            # GUARANTEED STATUS UPDATE - This always runs, no matter what
            if request.jobId:
                self._update_job_status(
                    request.sessionId,
                    request.jobId,
                    execution_success,
                    execution_error_message,
                    authorization_header,
                )

        # Return appropriate response
        if execution_success:
            return AgentResponse(
                success=True,
                error=None,
                message="Agent execution completed successfully",
            )
        else:
            return AgentResponse(
                success=False,
                error=execution_error_message,
                message="Agent execution failed due to uncaught exception",
            )

    def _execute_unwind_with_job_tracking(
        self,
        request: AgentRequest,
        function: Callable[..., None],
        authorization_header: str | None = None,
    ) -> AgentResponse:
        """
        Execute an unwind function with automatic job status tracking.

        The unwind hook supports a few signatures for backwards/forwards compatibility:
        - def unwind(agent: AgentContext, positions: list[CurrentPosition]) -> None  (recommended)
        - def unwind(agent: AgentContext) -> None                                  (convenience)
        - def unwind(positions: list[CurrentPosition]) -> None                      (legacy-style)
        """
        # Import here to avoid circular import
        from .agent_context import AgentContext, CurrentPosition

        execution_success = False
        execution_error_message: str | None = None

        try:
            # Full set of positions for this request
            current_positions = [
                CurrentPosition(**pos.model_dump()) for pos in request.currentPositions
            ]

            # Optional subset to unwind (if provided), otherwise use all current_positions
            unwind_source = request.unwindPositions or request.currentPositions
            positions_to_unwind = [
                CurrentPosition(**pos.model_dump()) for pos in unwind_source
            ]

            agent_context = AgentContext(
                sessionId=request.sessionId,
                sessionWalletAddress=request.sessionWalletAddress,
                currentPositions=current_positions,
                base_url=self.base_url,
                authorization_header=authorization_header,
            )

            # Call user function (supports multiple signatures)
            self._call_unwind_function(function, agent_context, positions_to_unwind)

            execution_success = True

        except Exception as e:
            execution_error_message = self._get_error_message(e)
            execution_success = False

            self.logger.error(
                f"Uncaught exception in agent unwind function: {execution_error_message}"
            )
            self.logger.error(
                f"Session ID: {request.sessionId}, Job ID: {request.jobId}"
            )

        finally:
            if request.jobId:
                self._update_job_status(
                    request.sessionId,
                    request.jobId,
                    execution_success,
                    execution_error_message,
                    authorization_header,
                )

        if execution_success:
            return AgentResponse(
                success=True,
                error=None,
                message="Agent unwind completed successfully",
            )
        return AgentResponse(
            success=False,
            error=execution_error_message,
            message="Agent unwind failed due to uncaught exception",
        )

    def _call_unwind_function(
        self,
        function: Callable[..., None],
        agent_context: "AgentContext",
        positions: list[Any],
    ) -> None:
        """
        Call an unwind function while supporting multiple compatible signatures.

        We intentionally use a small amount of signature introspection here so
        that agents can migrate with minimal churn.
        """
        try:
            sig = inspect.signature(function)
        except (TypeError, ValueError):
            # Best-effort fallback when signature is not introspectable
            function(agent_context, positions)
            return

        params = list(sig.parameters.values())
        positional = [
            p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        has_varargs = any(p.kind == p.VAR_POSITIONAL for p in params)

        if has_varargs or len(positional) >= 2:
            function(agent_context, positions)
            return

        if len(positional) == 1:
            # Heuristic: default to AgentContext (matches existing run contract).
            # If the param name suggests "positions", pass positions instead.
            name = positional[0].name.lower()
            if "position" in name:
                function(positions)
            else:
                function(agent_context)
            return

        # Zero-arg function (rare)
        function()

    def _update_job_status(
        self,
        session_id: int,
        job_id: str,
        success: bool,
        error_message: str | None = None,
        authorization_header: str | None = None,
    ) -> None:
        """
        Update job status with retries and fallback. NEVER raises exceptions.

        Strategy:
        1. Try to send status with error message (3 retries)
        2. If that fails, try to send status without error message (final fallback)

        Args:
            session_id: Session ID
            job_id: Job ID to update
            success: Whether execution was successful
            error_message: Error message if execution failed (None if successful)
            authorization_header: Optional Authorization header from incoming request
        """
        status = "success" if success else "failed"

        # Try with error message (3 attempts with exponential backoff)
        for attempt in range(1, 4):
            try:
                self._send_job_status_update(
                    session_id, job_id, status, error_message, authorization_header
                )
                self.logger.debug(
                    f"Job status updated to '{status}' (attempt {attempt})"
                )
                return
            except Exception as e:
                self.logger.error(f"Status update attempt {attempt}/3 failed: {e}")
                if attempt < 3:
                    import time

                    time.sleep(0.1 * (2 ** (attempt - 1)))  # 0.1s, 0.2s

        # Final fallback: Try without error message
        if not success:
            try:
                self._send_job_status_update(
                    session_id, job_id, status, None, authorization_header
                )
                self.logger.warning(
                    f"Job status updated to '{status}' without error message"
                )
                return
            except Exception as e:
                self.logger.critical(
                    f"CRITICAL: Failed to update job {job_id} status. "
                    f"Likely API connectivity issue: {e}"
                )

    def _send_job_status_update(
        self,
        session_id: int,
        job_id: str,
        status: str,
        error_message: str | None = None,
        authorization_header: str | None = None,
    ) -> None:
        """
        Send job status update to the API using the AgentSdk.

        This is the low-level method that makes the actual API call.
        Use _update_job_status() instead, which includes retry logic.

        Args:
            session_id: Session ID for SDK initialization
            job_id: Job ID to update
            status: New status ("success" or "failed")
            error_message: Optional error message for failed status
            authorization_header: Optional Authorization header from incoming request
        """
        try:
            # Import here to avoid circular import
            from .agent_sdk import AgentSdk
            from .types.config import SDKConfig

            # Create SDK instance for this session using the same base URL as the agent
            sdk = AgentSdk(
                SDKConfig(
                    session_id=session_id,
                    base_url=self.base_url,
                    authorization_header=authorization_header,
                )
            )

            # Update job status
            update_request = {
                "jobId": job_id,
                "status": status,
            }
            if error_message:
                update_request["errorMessage"] = error_message

            sdk._update_job_status(update_request)

        except Exception as e:
            self.logger.error(f"Failed to update job status: {e}")
            # Don't re-raise - job status update failures shouldn't break the main flow

    def _handler_func(self, event: dict[str, Any], context: Any) -> dict[str, Any]:
        """
        Handler function for Circuit deployment.

        Args:
            event: Request event
            context: Request context

        Returns:
            Handler response
        """
        self.logger.debug("Handler function called")
        self.logger.debug(f"Event received: {json.dumps(event, default=str)}")

        # If FastAPI is available and this is an HTTP event, use Mangum
        if FASTAPI_AVAILABLE and self.app and self._is_http_event(event):
            if self._handler is None:
                raise RuntimeError("Handler not available")
            return self._handler(event, context)

        # Handle direct invocation
        try:
            # Parse event body
            body = self._parse_event_body(event)

            # Extract command from URL path
            command = self._extract_command(event)

            # Extract required parameters
            session_id = body.get("sessionId")
            session_wallet_address = body.get("sessionWalletAddress")
            job_id = body.get("jobId")
            current_positions = body.get("currentPositions")
            # Extract Authorization header from event
            authorization_header = None
            if "headers" in event and event["headers"]:
                # Check both Authorization and authorization (case-insensitive)
                authorization_header = event["headers"].get("Authorization") or event[
                    "headers"
                ].get("authorization")

            # Single info log with all relevant information
            if command == "health":
                self.logger.info(f"Request: command={command}")
            else:
                self.logger.info(
                    f"Request: command={command}, session={session_id}, wallet={session_wallet_address}"
                )

            # Process the request
            if command == "health":
                # Health check - no sessionId/walletAddress needed
                result: dict[str, Any] = self.health_check_function()
            else:
                # Validate required parameters
                if not all([session_id, session_wallet_address]):
                    self.logger.error(
                        "Missing required parameters: sessionId and sessionWalletAddress"
                    )
                    return HandlerResponse(
                        statusCode=400,
                        body="You must provide 'sessionId' and 'sessionWalletAddress' parameters",
                        headers={},
                    ).model_dump()

                # Default to empty list if not provided
                if current_positions is None:
                    current_positions = []

                # Type validation for mypy
                if not isinstance(session_id, int):
                    self.logger.error("sessionId must be an integer")
                    return HandlerResponse(
                        statusCode=400,
                        body="sessionId must be an integer",
                        headers={},
                    ).model_dump()

                if not isinstance(session_wallet_address, str):
                    self.logger.error("sessionWalletAddress must be a string")
                    return HandlerResponse(
                        statusCode=400,
                        body="sessionWalletAddress must be a string",
                        headers={},
                    ).model_dump()

                result = self.process_request(
                    session_id,
                    session_wallet_address,
                    current_positions,
                    command,
                    job_id,
                    authorization_header,
                )

            self.logger.info(
                f"Response: command={command}, success={result.get('success', True)}"
            )

            # If the result indicates failure, return 500 status code
            if isinstance(result, dict) and result.get("success") is False:
                error_message = result.get("error", "Unknown error")
                # Ensure error message is JSON-safe
                try:
                    error_body = json.dumps(
                        {
                            "success": False,
                            "error": error_message,
                            "message": "Agent execution failed",
                        }
                    )
                except (TypeError, ValueError):
                    # Fallback if error message contains non-JSON-serializable content
                    error_body = json.dumps(
                        {
                            "success": False,
                            "error": str(error_message),
                            "message": "Agent execution failed",
                        }
                    )

                return HandlerResponse(
                    statusCode=500,
                    body=error_body,
                    headers={"Content-Type": "application/json"},
                ).model_dump()

            return HandlerResponse(
                statusCode=200, body=json.dumps(result), headers={}
            ).model_dump()

        except ValueError as e:
            return HandlerResponse(statusCode=400, body=str(e), headers={}).model_dump()
        except Exception as e:
            return HandlerResponse(
                statusCode=500, body=f"Internal server error: {str(e)}", headers={}
            ).model_dump()

    def _is_http_event(self, event: dict[str, Any]) -> bool:
        """Check if event is an HTTP event"""
        # Check for API Gateway v1.0 format
        if "httpMethod" in event:
            # Require additional fields that would be present in a real API Gateway event
            return all(key in event for key in ["httpMethod", "headers", "path"])
        # Check for API Gateway v1.2 format
        if "requestContext" in event:
            return "http" in event.get("requestContext", {})
        return False

    def _parse_event_body(self, event: dict[str, Any]) -> dict[str, Any]:
        """Parse event body from request event"""
        is_base64_encoded: bool = event.get("isBase64Encoded", False)
        if is_base64_encoded:
            try:
                body_str = base64.b64decode(event["body"]).decode("utf-8")
                parsed_result: dict[str, Any] = json.loads(body_str)
                return parsed_result
            except Exception:
                return {}
        else:
            body: Any = event.get("body", {})
            if isinstance(body, str):
                try:
                    parsed_body: dict[str, Any] = json.loads(body)
                    return parsed_body
                except (json.JSONDecodeError, TypeError):
                    return {}
            return body if isinstance(body, dict) else {}

    def _extract_command(self, event: dict[str, Any]) -> str:
        """Extract command from request event path"""
        raw_path: str = event.get("rawPath", "/")

        # Handle runtime URL structure
        if raw_path.startswith("/2015-03-31/functions/function/invocations/"):
            return raw_path.split("/")[-1]
        else:
            return raw_path.lstrip("/")

    def run(self, host: str | None = None, port: int | None = None) -> None:
        """
        Internal method for local testing - handled automatically by the boilerplate code.

        You don't need to call this directly. When you run your agent file locally,
        the code at the bottom handles everything automatically.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        if not FASTAPI_AVAILABLE:
            self.logger.error(
                "FastAPI not available. Install with: uv add fastapi uvicorn mangum"
            )
            return

        if not self.app:
            self.logger.error("FastAPI app not initialized")
            return

        import uvicorn

        host = host or "0.0.0.0"
        # Prefer explicit argument, then environment variables set by the CLI, then default
        env_port_str = os.environ.get("PORT") or os.environ.get("AGENT_PORT")
        env_port: int | None = None
        if env_port_str:
            try:
                env_port = int(env_port_str)
            except ValueError:
                env_port = None
        port = port or env_port or 8000

        uvicorn.run(self.app, host=host, port=port, log_config=None)

    def get_handler(self) -> Any:
        """
        Internal method used by Circuit deployment - you don't need to call this directly.

        This is used in the boilerplate code at the bottom of your agent file.
        Circuit's deployment pipeline handles all of this automatically.

        Returns:
            Handler function for Circuit deployment
        """
        return self._handler_func

    def get_worker_export(self) -> Any:
        """
        Get export for worker environments.
        Currently returns the FastAPI app.

        Returns:
            FastAPI app or handler
        """
        if FASTAPI_AVAILABLE and self.app:
            return self.app
        return self._handler_func


# Simple factory function - just creates an agent
def create_agent_handler(
    run_function: ExecutionFunctionContract,
    base_url: str | None = None,
    unwind_function: UnwindFunctionContract | None = None,
) -> Agent:
    """
    Internal factory to create an Agent - used by the boilerplate code.

    You don't need to call this directly. Just define your run_function
    and unwind_function, and the boilerplate code at the bottom of your agent
    file handles the rest.

    Args:
        run_function: Main execution function - receives AgentContext, returns None

    Returns:
        Agent instance configured with the provided functions
    """
    return Agent(
        run_function=run_function,
        base_url=base_url,
        unwind_function=unwind_function,
    )
