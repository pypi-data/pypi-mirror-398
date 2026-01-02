"""
A2A Extension Validator
----------------------
Validates extension declarations, negotiation, and activation
according to the A2A Extensions specification.

This module is protocol-level (no framework/runtime coupling).
"""

from __future__ import annotations

from typing import Dict, List, Set, Any
from urllib.parse import urlparse

from a2a.extensions.models import AgentExtension


# ---------------------------------------------------------------------
# EXCEPTIONS
# ---------------------------------------------------------------------

class ExtensionValidationError(Exception):
    """Base exception for extension validation errors."""


class InvalidExtensionURI(ExtensionValidationError):
    pass


class MissingRequiredExtension(ExtensionValidationError):
    pass


class UnsupportedExtension(ExtensionValidationError):
    pass


class ExtensionDependencyError(ExtensionValidationError):
    pass


class ExtensionParameterError(ExtensionValidationError):
    pass


# ---------------------------------------------------------------------
# VALIDATION UTILITIES
# ---------------------------------------------------------------------

def validate_extension_uri(uri: str) -> None:
    """
    Ensure extension URI is a valid absolute URI.
    Required by A2A spec.
    """
    parsed = urlparse(uri)

    if not parsed.scheme or not parsed.netloc:
        raise InvalidExtensionURI(
            f"Invalid extension URI: {uri}. Must be absolute URI."
        )


def validate_extension_parameters(
    extension: AgentExtension,
    provided_params: Dict[str, Any] | None = None,
) -> None:
    """
    Validate provided parameters against extension declaration.
    """
    if not extension.params:
        return

    provided_params = provided_params or {}

    for param, rules in extension.params.items():
        if rules.get("required") and param not in provided_params:
            raise ExtensionParameterError(
                f"Missing required parameter '{param}' for extension {extension.uri}"
            )

        if param in provided_params:
            expected_type = rules.get("type")
            if expected_type and not isinstance(
                provided_params[param], expected_type
            ):
                raise ExtensionParameterError(
                    f"Parameter '{param}' for extension {extension.uri} "
                    f"must be of type {expected_type.__name__}"
                )


# ---------------------------------------------------------------------
# CORE VALIDATION LOGIC
# ---------------------------------------------------------------------

def validate_agent_extensions(
    declared: List[AgentExtension] | None,
) -> None:
    """
    Validate agent-declared extensions in AgentCard.
    """
    if not declared:
        return

    seen: Set[str] = set()

    for ext in declared:
        validate_extension_uri(ext.uri)

        if ext.uri in seen:
            raise ExtensionValidationError(
                f"Duplicate extension declaration: {ext.uri}"
            )

        seen.add(ext.uri)


def validate_extension_negotiation(
    agent_extensions: List[AgentExtension] | None,
    requested_extensions: List[str] | None,
) -> List[str]:
    """
    Validate requested extensions against agent-declared extensions.
    Returns list of activated extensions.
    """

    agent_extensions = agent_extensions or []
    requested_extensions = requested_extensions or []

    declared_map: Dict[str, AgentExtension] = {
        ext.uri: ext for ext in agent_extensions
    }

    # Validate required extensions
    for ext in agent_extensions:
        if ext.required and ext.uri not in requested_extensions:
            raise MissingRequiredExtension(
                f"Required extension not requested: {ext.uri}"
            )

    activated: List[str] = []

    for uri in requested_extensions:
        if uri not in declared_map:
            raise UnsupportedExtension(
                f"Extension not supported by agent: {uri}"
            )
        activated.append(uri)

    return activated


def validate_extension_dependencies(
    activated_extensions: List[str],
    dependency_map: Dict[str, List[str]],
) -> None:
    """
    Ensure extension dependencies are satisfied.
    """
    activated_set = set(activated_extensions)

    for ext, deps in dependency_map.items():
        if ext in activated_set:
            for dep in deps:
                if dep not in activated_set:
                    raise ExtensionDependencyError(
                        f"Extension '{ext}' requires '{dep}'"
                    )


# ---------------------------------------------------------------------
# HIGH-LEVEL VALIDATION ENTRYPOINT
# ---------------------------------------------------------------------

def validate_extensions_end_to_end(
    *,
    agent_extensions: List[AgentExtension] | None,
    requested_extensions: List[str] | None,
    dependency_map: Dict[str, List[str]] | None = None,
    extension_params: Dict[str, Dict[str, Any]] | None = None,
) -> List[str]:
    """
    Full extension validation lifecycle.
    """

    dependency_map = dependency_map or {}
    extension_params = extension_params or {}

    # 1. Validate agent declarations
    validate_agent_extensions(agent_extensions)

    # 2. Validate negotiation
    activated = validate_extension_negotiation(
        agent_extensions, requested_extensions
    )

    # 3. Validate dependencies
    validate_extension_dependencies(activated, dependency_map)

    # 4. Validate parameters
    declared_map = {ext.uri: ext for ext in (agent_extensions or [])}

    for uri in activated:
        validate_extension_parameters(
            declared_map[uri],
            extension_params.get(uri),
        )

    return activated
