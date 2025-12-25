from dependency.core.exceptions import ResolutionError as ResolutionError
from dependency.core.injection.injectable import Injectable as Injectable
from dependency.core.resolution.utils import find_cycles as find_cycles

def raise_circular_error(injectables: list[Injectable]) -> bool:
    """Raise an error if circular dependencies are detected.

    Args:
        injectables (list[Injectable]): The list of provider injections to check for cycles.

    Returns:
        bool: True if cycles were detected and errors were raised, False otherwise.
    """
def raise_dependency_error(unresolved: list[Injectable]) -> bool:
    """Raise an error when unresolved dependencies are detected.

    Args:
        unresolved (list[Injectable]): The list of unresolved provider injections.

    Returns:
        bool: True if unresolved dependencies were detected and errors were raised, False otherwise.
    """
def raise_resolution_error(injectables: list[Injectable], unresolved: list[Injectable]) -> None:
    """Raise an error if unresolved provider imports are detected.

    Args:
        providers (list[ProviderInjection]): The list of provider injections to check.
        unresolved (list[ProviderInjection]): The resolved providers to check against.

    Raises:
        ResolutionError: If unresolved dependencies or cycles are detected.
    """
