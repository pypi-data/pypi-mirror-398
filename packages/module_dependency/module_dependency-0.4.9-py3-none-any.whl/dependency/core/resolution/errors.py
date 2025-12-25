import logging
from dependency.core.injection.injectable import Injectable
from dependency.core.resolution.utils import find_cycles
from dependency.core.exceptions import ResolutionError
_logger = logging.getLogger("DependencyLoader")

def raise_circular_error(
    injectables: list[Injectable]
) -> bool:
    """Raise an error if circular dependencies are detected.

    Args:
        injectables (list[Injectable]): The list of provider injections to check for cycles.

    Returns:
        bool: True if cycles were detected and errors were raised, False otherwise.
    """
    cycles = find_cycles(lambda i: i.imports, injectables)
    for cycle in cycles:
        _logger.error(f"Circular import: {cycle}")
    return len(cycles) > 0

def raise_dependency_error(
    unresolved: list[Injectable],
) -> bool:
    """Raise an error when unresolved dependencies are detected.

    Args:
        unresolved (list[Injectable]): The list of unresolved provider injections.

    Returns:
        bool: True if unresolved dependencies were detected and errors were raised, False otherwise.
    """
    for injectable in unresolved:
        unresolved_imports = filter(lambda d: not d.is_resolved, injectable.imports)
        _logger.error(f"Provider {injectable} has unresolved dependencies: {unresolved_imports}")
    return len(unresolved) > 0

def raise_resolution_error(
    injectables: list[Injectable],
    unresolved: list[Injectable],
) -> None:
    """Raise an error if unresolved provider imports are detected.

    Args:
        providers (list[ProviderInjection]): The list of provider injections to check.
        unresolved (list[ProviderInjection]): The resolved providers to check against.

    Raises:
        ResolutionError: If unresolved dependencies or cycles are detected.
    """
    circular_error = raise_circular_error(injectables)
    dependency_error = raise_dependency_error(unresolved)
    if circular_error or dependency_error:
        raise ResolutionError("Errors detected during provider resolution.")
