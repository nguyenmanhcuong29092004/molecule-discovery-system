"""
Base Agent Module

Provides abstract base class for all agents with automatic timing,
logging, and error handling.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# Configure logger
logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Base exception for agent errors."""

    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    pass


class AgentValidationError(AgentError):
    """Raised when agent input validation fails."""

    pass


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Provides automatic timing, logging, and error handling for agent execution.
    All agents must inherit from this class and implement the _execute() method.
    
    Attributes:
        name: Agent name for logging
        
    Example:
        ```python
        class MyAgent(BaseAgent):
            def __init__(self):
                super().__init__(name="MyAgent")
                
            def _execute(self, input_data: dict) -> dict:
                # Agent logic here
                return {"result": "success"}
                
        agent = MyAgent()
        result = agent.execute({"input": "data"})
        ```
    """

    def __init__(self, name: str):
        """
        Initialize base agent.
        
        Args:
            name: Agent name for logging and identification
        """
        self.name = name
        logger.info(f"Initialized {self.name}")

    @abstractmethod
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic.
        
        This method must be implemented by all subclasses.
        Contains the core agent logic without timing/logging overhead.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Output data from the agent
            
        Raises:
            AgentExecutionError: If execution fails
            AgentValidationError: If input validation fails
        """
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate input data.
        
        Override this method in subclasses to add custom validation.
        
        Args:
            input_data: Input data to validate
            
        Raises:
            AgentValidationError: If validation fails
        """
        if not isinstance(input_data, dict):
            raise AgentValidationError(
                f"Input must be a dictionary, got {type(input_data).__name__}"
            )

    def execute(
        self, input_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute agent with timing, logging, and error handling.
        
        This is the main entry point for agent execution. It wraps the
        _execute() method with automatic timing, logging, and error handling.
        
        Args:
            input_data: Input data for the agent
            metadata: Optional metadata for logging
            
        Returns:
            Dictionary containing:
                - output: Result from _execute()
                - duration_ms: Execution time in milliseconds
                - success: Whether execution succeeded
                - error: Error message if failed (optional)
                
        Example:
            ```python
            result = agent.execute(
                {"seed": "CCO"},
                metadata={"round": 1, "user_id": "123"}
            )
            print(result["output"])
            print(f"Took {result['duration_ms']}ms")
            ```
        """
        # Log start
        logger.info(
            f"Starting {self.name} execution",
            extra={"metadata": metadata or {}},
        )

        # Start timing
        start_time = time.time()

        try:
            # Validate input
            self.validate_input(input_data)

            # Execute agent logic
            output = self._execute(input_data)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log success
            logger.info(
                f"{self.name} completed successfully in {duration_ms}ms",
                extra={"duration_ms": duration_ms, "metadata": metadata or {}},
            )

            return {
                "output": output,
                "duration_ms": duration_ms,
                "success": True,
            }

        except AgentError as e:
            # Agent-specific errors (validation, execution)
            duration_ms = int((time.time() - start_time) * 1000)

            logger.error(
                f"{self.name} failed: {str(e)}",
                extra={
                    "duration_ms": duration_ms,
                    "metadata": metadata or {},
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            return {
                "output": None,
                "duration_ms": duration_ms,
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

        except Exception as e:
            # Unexpected errors
            duration_ms = int((time.time() - start_time) * 1000)

            logger.error(
                f"{self.name} failed with unexpected error: {str(e)}",
                extra={
                    "duration_ms": duration_ms,
                    "metadata": metadata or {},
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            return {
                "output": None,
                "duration_ms": duration_ms,
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": type(e).__name__,
            }

    def __repr__(self) -> str:
        """String representation of agent."""
        return f"<{self.name}>"