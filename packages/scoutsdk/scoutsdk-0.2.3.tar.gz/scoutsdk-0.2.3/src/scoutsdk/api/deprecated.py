import warnings
import functools
from typing import Any, Callable, Optional, TypeVar, cast, Type

F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T", bound=Type[Any])


def deprecated(
    reason: Optional[str] = None,
    version: Optional[str] = None,
    removal_version: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator to mark functions/methods as deprecated."""

    def decorator(obj: F) -> F:
        @functools.wraps(obj)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            message = f"{obj.__name__} is deprecated"
            if version:
                message += f" since version {version}"
            if removal_version:
                message += f" and will be removed in version {removal_version}"
            if reason:
                message += f". {reason}"

            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return obj(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def deprecated_class(
    reason: Optional[str] = None,
    version: Optional[str] = None,
    removal_version: Optional[str] = None,
) -> Callable[[T], T]:
    """Decorator to mark classes as deprecated."""

    def decorator(cls: T) -> T:
        original_init = cls.__init__

        @functools.wraps(original_init)
        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            message = f"{cls.__name__} is deprecated"
            if version:
                message += f" since version {version}"
            if removal_version:
                message += f" and will be removed in version {removal_version}"
            if reason:
                message += f". {reason}"

            warnings.warn(message, DeprecationWarning, stacklevel=2)
            original_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return decorator


# Configure deprecation warnings
warnings.filterwarnings("default", category=DeprecationWarning, module=__name__)
