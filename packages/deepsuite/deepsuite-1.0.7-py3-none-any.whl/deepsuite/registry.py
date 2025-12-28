"""Global Head Registry for DeepSuite.

Provides decorator-based registration for pluggable heads across projects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class HeadRegistry:
    """Registry for head classes used with DeepSuite-based projects.

    Allows dynamic registration, retrieval, and listing of head classes.
    """

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type], type]:
        """Decorator to register a head class under a given name.

        Args:
            name: Unique head identifier.

        Returns:
            Callable: Class decorator that registers the class.
        """

        def decorator(head_cls: type) -> type:
            if name in cls._registry:
                raise ValueError(f"Head '{name}' already registered")
            cls._registry[name] = head_cls
            return head_cls

        return decorator

    @classmethod
    def get(cls, name: str) -> type:
        """Retrieve a registered head class by name.

        Args:
            name: Registered head identifier.

        Returns:
            Type: Head class.
        """
        if name not in cls._registry:
            raise KeyError(f"Head '{name}' not found in registry")
        return cls._registry[name]

    @classmethod
    def list(cls) -> dict[str, type]:
        """List all registered heads.

        Returns:
            Dict[str, Type]: Mapping of head names to classes.
        """
        return dict(cls._registry)
