"""Agent type registry for dynamic agent discovery.

This module provides a registry for agent types, enabling dynamic agent
discovery and instantiation. Agents can be registered by type and retrieved
by name.

Pattern:
    Registry pattern with singleton instance for global access.

Example:
    >>> from obra.agents.registry import get_registry, register_agent
    >>>
    >>> @register_agent(AgentType.SECURITY)
    ... class MySecurityAgent(BaseAgent):
    ...     pass
    >>>
    >>> registry = get_registry()
    >>> agent_class = registry.get_agent(AgentType.SECURITY)
    >>> agent = agent_class(Path("/workspace"))

Related:
    - obra/agents/base.py
    - obra/api/protocol.py
"""

import logging
from collections.abc import Callable
from pathlib import Path

from obra.agents.base import BaseAgent
from obra.api.protocol import AgentType

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry for agent types.

    Maintains a mapping of AgentType to agent class. Agents can be
    registered using the @register_agent decorator or by calling
    register() directly.

    Attributes:
        _agents: Internal mapping of type to class
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._agents: dict[AgentType, type[BaseAgent]] = {}
        logger.debug("AgentRegistry initialized")

    def register(
        self,
        agent_type: AgentType,
        agent_class: type[BaseAgent],
    ) -> None:
        """Register an agent class for a type.

        Args:
            agent_type: Agent type to register
            agent_class: Agent class to register

        Raises:
            ValueError: If agent_type is already registered
        """
        if agent_type in self._agents:
            existing = self._agents[agent_type].__name__
            logger.warning(
                f"Overwriting agent registration for {agent_type.value}: "
                f"{existing} -> {agent_class.__name__}"
            )

        self._agents[agent_type] = agent_class
        logger.info(f"Registered agent: {agent_type.value} -> {agent_class.__name__}")

    def get_agent(self, agent_type: AgentType) -> type[BaseAgent] | None:
        """Get agent class for type.

        Args:
            agent_type: Agent type to look up

        Returns:
            Agent class or None if not registered
        """
        return self._agents.get(agent_type)

    def get_agent_by_name(self, name: str) -> type[BaseAgent] | None:
        """Get agent class by type name string.

        Args:
            name: Agent type name (e.g., "security", "testing")

        Returns:
            Agent class or None if not registered
        """
        try:
            agent_type = AgentType(name)
            return self.get_agent(agent_type)
        except ValueError:
            logger.warning(f"Unknown agent type: {name}")
            return None

    def create_agent(
        self,
        agent_type: AgentType,
        working_dir: Path,
    ) -> BaseAgent | None:
        """Create an agent instance.

        Args:
            agent_type: Type of agent to create
            working_dir: Working directory for agent

        Returns:
            Agent instance or None if type not registered
        """
        agent_class = self.get_agent(agent_type)
        if agent_class is None:
            logger.warning(f"No agent registered for type: {agent_type.value}")
            return None

        try:
            return agent_class(working_dir)
        except Exception as e:
            logger.error(f"Failed to create agent {agent_type.value}: {e}")
            return None

    def list_agents(self) -> list[AgentType]:
        """List all registered agent types.

        Returns:
            List of registered agent types
        """
        return list(self._agents.keys())

    def is_registered(self, agent_type: AgentType) -> bool:
        """Check if agent type is registered.

        Args:
            agent_type: Agent type to check

        Returns:
            True if registered, False otherwise
        """
        return agent_type in self._agents

    def clear(self) -> None:
        """Clear all registered agents (for testing)."""
        self._agents.clear()


# Global registry instance
_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry.

    Returns:
        Global AgentRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def register_agent(
    agent_type: AgentType,
) -> Callable[[type[BaseAgent]], type[BaseAgent]]:
    """Decorator to register an agent class.

    Usage:
        >>> @register_agent(AgentType.SECURITY)
        ... class SecurityAgent(BaseAgent):
        ...     pass

    Args:
        agent_type: Agent type to register

    Returns:
        Decorator function
    """

    def decorator(cls: type[BaseAgent]) -> type[BaseAgent]:
        registry = get_registry()
        registry.register(agent_type, cls)
        return cls

    return decorator


__all__ = ["AgentRegistry", "get_registry", "register_agent"]
