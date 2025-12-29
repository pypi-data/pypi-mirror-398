"""Agent deployment manager for subprocess-based agent execution.

This module provides AgentDeployer, which manages the deployment and
execution of review agents. Each agent runs in isolation and returns
structured results.

Architecture:
    - AgentDeployer receives ReviewRequest from orchestrator
    - Deploys specified agents (sequentially or in parallel)
    - Each agent analyzes code and returns AgentResult
    - Deployer collects results and returns to orchestrator

Execution Modes:
    - Sequential: Run agents one at a time (default, safer)
    - Parallel: Run agents concurrently (faster, more memory)

Timeout Handling:
    - Each agent has a timeout (default 60s)
    - If agent exceeds timeout, result status is "timeout"
    - Deployer continues with remaining agents

Related:
    - obra/agents/base.py
    - obra/agents/registry.py
    - obra/hybrid/handlers/review.py
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Any

from obra.agents.base import AgentResult, BaseAgent
from obra.agents.registry import get_registry
from obra.api.protocol import AgentType

logger = logging.getLogger(__name__)


class AgentDeployer:
    """Manages agent deployment and execution.

    AgentDeployer is responsible for:
    - Creating agent instances from registry
    - Running agents with timeout enforcement
    - Collecting and aggregating results
    - Handling errors gracefully

    Example:
        >>> deployer = AgentDeployer(Path("/workspace"))
        >>> results = deployer.run_agents(
        ...     agents=[AgentType.SECURITY, AgentType.TESTING],
        ...     item_id="T1",
        ...     timeout_ms=60000
        ... )
        >>> for result in results:
        ...     print(f"{result.agent_type.value}: {len(result.issues)} issues")
    """

    def __init__(
        self,
        working_dir: Path,
        parallel: bool = False,
        max_workers: int = 4,
    ) -> None:
        """Initialize agent deployer.

        Args:
            working_dir: Working directory for agents
            parallel: Whether to run agents in parallel
            max_workers: Maximum concurrent agents if parallel=True
        """
        self._working_dir = working_dir
        self._parallel = parallel
        self._max_workers = max_workers
        self._registry = get_registry()

        logger.info(
            f"AgentDeployer initialized: working_dir={working_dir}, "
            f"parallel={parallel}, max_workers={max_workers}"
        )

    @property
    def working_dir(self) -> Path:
        """Get working directory."""
        return self._working_dir

    def run_agents(
        self,
        agents: list[AgentType],
        item_id: str,
        changed_files: list[str] | None = None,
        timeout_ms: int = 60000,
        budgets: dict[str, dict[str, Any]] | None = None,
        production_logger: Any | None = None,
        session_id: str | None = None,
        task_id: int | None = None,
    ) -> list[AgentResult]:
        """Run specified agents and collect results.

        Args:
            agents: List of agent types to run
            item_id: Plan item ID being reviewed
            changed_files: List of files that changed (for focused review)
            timeout_ms: Default timeout per agent in milliseconds
            budgets: Per-agent budget overrides {agent_name: {"timeout_ms": int}}
            production_logger: Optional ProductionLogger for event logging
            session_id: Optional session ID for event logging
            task_id: Optional task ID for event logging

        Returns:
            List of AgentResult from each agent
        """
        budgets = budgets or {}
        results: list[AgentResult] = []

        logger.info(
            f"Running {len(agents)} agents for item {item_id}: "
            f"{[a.value for a in agents]}"
        )

        if self._parallel:
            results = self._run_parallel(
                agents=agents,
                item_id=item_id,
                changed_files=changed_files,
                timeout_ms=timeout_ms,
                budgets=budgets,
                production_logger=production_logger,
                session_id=session_id,
                task_id=task_id,
            )
        else:
            results = self._run_sequential(
                agents=agents,
                item_id=item_id,
                changed_files=changed_files,
                timeout_ms=timeout_ms,
                budgets=budgets,
                production_logger=production_logger,
                session_id=session_id,
                task_id=task_id,
            )

        total_issues = sum(len(r.issues) for r in results)
        logger.info(
            f"Agent run complete: {len(results)} agents, {total_issues} total issues"
        )

        return results

    def run_agent(
        self,
        agent_type: AgentType,
        item_id: str,
        changed_files: list[str] | None = None,
        timeout_ms: int = 60000,
        production_logger: Any | None = None,
        session_id: str | None = None,
        task_id: int | None = None,
    ) -> AgentResult:
        """Run a single agent.

        Args:
            agent_type: Type of agent to run
            item_id: Plan item ID being reviewed
            changed_files: List of files that changed
            timeout_ms: Timeout in milliseconds
            production_logger: Optional ProductionLogger for event logging
            session_id: Optional session ID for event logging
            task_id: Optional task ID for event logging

        Returns:
            AgentResult from agent execution
        """
        start_time = time.time()
        logger.debug(f"Deploying {agent_type.value} agent for {item_id}")

        # Create agent instance
        agent = self._registry.create_agent(agent_type, self._working_dir)
        if agent is None:
            logger.error(f"No agent registered for type: {agent_type.value}")

            # Log task failure if production logger available
            if production_logger and session_id and task_id is not None:
                import traceback
                production_logger.log_task_failed(
                    session_id=session_id,
                    task_id=task_id,
                    error_type="AgentRegistrationError",
                    error_message=f"Agent type not registered: {agent_type.value}",
                    stack_trace=None,
                )

            return AgentResult(
                agent_type=agent_type,
                status="error",
                error=f"Agent type not registered: {agent_type.value}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Run with timeout
        try:
            result = self._run_with_timeout(
                agent=agent,
                item_id=item_id,
                changed_files=changed_files,
                timeout_ms=timeout_ms,
            )
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            return result

        except TimeoutError:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.warning(
                f"Agent {agent_type.value} timed out after {execution_time_ms}ms"
            )

            # Log task failure if production logger available
            if production_logger and session_id and task_id is not None:
                import traceback
                production_logger.log_task_failed(
                    session_id=session_id,
                    task_id=task_id,
                    error_type="TimeoutError",
                    error_message=f"Agent {agent_type.value} timed out after {execution_time_ms}ms",
                    stack_trace=traceback.format_exc(),
                )

            return AgentResult(
                agent_type=agent_type,
                status="timeout",
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Agent {agent_type.value} failed: {e}")

            # Log task failure if production logger available
            if production_logger and session_id and task_id is not None:
                import traceback
                production_logger.log_task_failed(
                    session_id=session_id,
                    task_id=task_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                )

            return AgentResult(
                agent_type=agent_type,
                status="error",
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    def _run_sequential(
        self,
        agents: list[AgentType],
        item_id: str,
        changed_files: list[str] | None,
        timeout_ms: int,
        budgets: dict[str, dict[str, Any]],
        production_logger: Any | None = None,
        session_id: str | None = None,
        task_id: int | None = None,
    ) -> list[AgentResult]:
        """Run agents sequentially.

        Args:
            agents: Agent types to run
            item_id: Plan item ID
            changed_files: Changed files
            timeout_ms: Default timeout
            budgets: Per-agent budgets
            production_logger: Optional ProductionLogger for event logging
            session_id: Optional session ID for event logging
            task_id: Optional task ID for event logging

        Returns:
            List of results
        """
        results: list[AgentResult] = []

        for agent_type in agents:
            # Get per-agent timeout
            agent_timeout = budgets.get(agent_type.value, {}).get(
                "timeout_ms", timeout_ms
            )

            result = self.run_agent(
                agent_type=agent_type,
                item_id=item_id,
                changed_files=changed_files,
                timeout_ms=agent_timeout,
                production_logger=production_logger,
                session_id=session_id,
                task_id=task_id,
            )
            results.append(result)

        return results

    def _run_parallel(
        self,
        agents: list[AgentType],
        item_id: str,
        changed_files: list[str] | None,
        timeout_ms: int,
        budgets: dict[str, dict[str, Any]],
        production_logger: Any | None = None,
        session_id: str | None = None,
        task_id: int | None = None,
    ) -> list[AgentResult]:
        """Run agents in parallel using thread pool.

        Args:
            agents: Agent types to run
            item_id: Plan item ID
            changed_files: Changed files
            timeout_ms: Default timeout
            budgets: Per-agent budgets
            production_logger: Optional ProductionLogger for event logging
            session_id: Optional session ID for event logging
            task_id: Optional task ID for event logging

        Returns:
            List of results
        """
        results: list[AgentResult] = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit all agents
            futures = {}
            for agent_type in agents:
                agent_timeout = budgets.get(agent_type.value, {}).get(
                    "timeout_ms", timeout_ms
                )
                future = executor.submit(
                    self.run_agent,
                    agent_type=agent_type,
                    item_id=item_id,
                    changed_files=changed_files,
                    timeout_ms=agent_timeout,
                    production_logger=production_logger,
                    session_id=session_id,
                    task_id=task_id,
                )
                futures[future] = agent_type

            # Collect results
            for future in futures:
                agent_type = futures[future]
                try:
                    result = future.result(timeout=timeout_ms / 1000 + 5)
                    results.append(result)
                except FutureTimeoutError:
                    # Log task failure if production logger available
                    if production_logger and session_id and task_id is not None:
                        import traceback
                        production_logger.log_task_failed(
                            session_id=session_id,
                            task_id=task_id,
                            error_type="FutureTimeoutError",
                            error_message=f"Agent {agent_type.value} parallel execution timed out",
                            stack_trace=traceback.format_exc(),
                        )

                    results.append(
                        AgentResult(
                            agent_type=agent_type,
                            status="timeout",
                            execution_time_ms=timeout_ms,
                        )
                    )
                except Exception as e:
                    # Log task failure if production logger available
                    if production_logger and session_id and task_id is not None:
                        import traceback
                        production_logger.log_task_failed(
                            session_id=session_id,
                            task_id=task_id,
                            error_type=type(e).__name__,
                            error_message=f"Agent {agent_type.value} parallel execution failed: {e!s}",
                            stack_trace=traceback.format_exc(),
                        )

                    results.append(
                        AgentResult(
                            agent_type=agent_type,
                            status="error",
                            error=str(e),
                        )
                    )

        return results

    def _run_with_timeout(
        self,
        agent: BaseAgent,
        item_id: str,
        changed_files: list[str] | None,
        timeout_ms: int,
    ) -> AgentResult:
        """Run agent with timeout using thread pool.

        Args:
            agent: Agent instance
            item_id: Plan item ID
            changed_files: Changed files
            timeout_ms: Timeout in milliseconds

        Returns:
            AgentResult from agent

        Raises:
            TimeoutError: If agent exceeds timeout
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                agent.analyze,
                item_id=item_id,
                changed_files=changed_files,
                timeout_ms=timeout_ms,
            )
            try:
                return future.result(timeout=timeout_ms / 1000)
            except FutureTimeoutError:
                raise TimeoutError(f"Agent timed out after {timeout_ms}ms")


def create_deployer(
    working_dir: Path,
    parallel: bool = False,
) -> AgentDeployer:
    """Factory function to create an AgentDeployer.

    Args:
        working_dir: Working directory for agents
        parallel: Whether to run agents in parallel

    Returns:
        Configured AgentDeployer instance
    """
    return AgentDeployer(working_dir=working_dir, parallel=parallel)


__all__ = ["AgentDeployer", "create_deployer"]
