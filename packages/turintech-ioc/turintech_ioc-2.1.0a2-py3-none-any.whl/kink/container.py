from types import LambdaType
from typing import TYPE_CHECKING, Any, Callable, Dict, Generic, List, Type, TypeVar, Union, overload, cast

from kink.errors.service_error import ServiceError
from kink.typing_support import is_optional, unpack_optional

_MISSING_SERVICE = object()


T = TypeVar("T")


class LazyProxy(Generic[T]):
    """Proxy object that delays service resolution until first access."""
    
    def __init__(self, container: "Container", service_key: Union[str, Type[T]]):
        self._container = container
        self._service_key = service_key
        self._resolved = False
        self._instance: Union[T, None] = None
    
    def _resolve(self) -> T:
        """Resolve the actual service instance."""
        if not self._resolved:
            # Set flag to prevent infinite recursion
            original_resolving = getattr(self._container, '_resolving_lazy', False)
            self._container._resolving_lazy = True
            try:
                self._instance = self._container[self._service_key]
            finally:
                self._container._resolving_lazy = original_resolving
            self._resolved = True
        return cast(T, self._instance)
    
    def __getattr__(self, name: str):
        """Delegate attribute access to the resolved instance."""
        return getattr(self._resolve(), name)
    
    def __getitem__(self, item):
        """Support subscript access if the wrapped object supports it."""
        return self._resolve()[item]
    
    def __call__(self, *args, **kwargs):
        """Support callable objects."""
        return self._resolve()(*args, **kwargs)
    
    def __repr__(self):
        """Provide a meaningful representation."""
        return repr(self._resolve())
    
    def __str__(self):
        """String representation."""
        return str(self._resolve())
    
    def __setattr__(self, name: str, value: Any):
        """Handle attribute setting."""
        if name in ('_container', '_service_key', '_resolved', '_instance'):
            object.__setattr__(self, name, value)
        else:
            setattr(self._resolve(), name, value)
    
    # Comparison operators
    def __eq__(self, other):
        """Equality comparison."""
        return self._resolve() == other
    
    def __ne__(self, other):
        """Inequality comparison."""
        return self._resolve() != other
    
    def __lt__(self, other):
        """Less than comparison."""
        return self._resolve() < other
    
    def __le__(self, other):
        """Less than or equal comparison."""
        return self._resolve() <= other
    
    def __gt__(self, other):
        """Greater than comparison."""
        return self._resolve() > other
    
    def __ge__(self, other):
        """Greater than or equal comparison."""
        return self._resolve() >= other
    
    # Container/sequence methods
    def __len__(self):
        """Length of the proxied object."""
        return len(self._resolve())
    
    def __contains__(self, item):
        """Check if item is in the proxied object."""
        return item in self._resolve()
    
    def __iter__(self):
        """Iterate over the proxied object."""
        return iter(self._resolve())
    
    # Type checking - Note: this doesn't work for isinstance checks on the proxy itself
    def __instancecheck__(self, instance):
        """Check if instance is of the proxied type."""
        return isinstance(instance, type(self._resolve()))
    
    @property  
    def __class__(self):
        """Return the class of the proxied object for isinstance checks."""
        return self._resolve().__class__
    
    # Numeric operators (for completeness)
    def __add__(self, other):
        """Addition."""
        return self._resolve() + other
    
    def __sub__(self, other):
        """Subtraction."""
        return self._resolve() - other
    
    def __mul__(self, other):
        """Multiplication."""
        return self._resolve() * other
    
    def __truediv__(self, other):
        """True division."""
        return self._resolve() / other
    
    def __floordiv__(self, other):
        """Floor division."""
        return self._resolve() // other
    
    def __mod__(self, other):
        """Modulo."""
        return self._resolve() % other
    
    def __pow__(self, other):
        """Power."""
        return self._resolve() ** other
    
    # Boolean
    def __bool__(self):
        """Boolean value of the proxied object."""
        return bool(self._resolve())
    
    # Hash
    def __hash__(self):
        """Hash of the proxied object."""
        return hash(self._resolve())


class Container:
    def __init__(self):
        self._memoized_services: Dict[Union[str, Type], Any] = {}
        self._services: Dict[Union[str, Type], Any] = {}
        self._factories: Dict[Union[str, Type], Callable[[Container], Any]] = {}
        self._aliases: Dict[Union[str, Type], List[Union[str, Type]]] = {}
        self._lazy_proxies: Dict[Union[str, Type], LazyProxy] = {}

    def __setitem__(self, key: Union[str, Type], value: Any) -> None:
        self._services[key] = value

        if key in self._memoized_services:
            del self._memoized_services[key]
        
        if key in self._lazy_proxies:
            del self._lazy_proxies[key]

    def __delitem__(self, key):
        if key in self._services:
            del self._services[key]

        if key in self._memoized_services:
            del self._memoized_services[key]

        if key in self._aliases:
            del self._aliases[key]
        
        if key in self._lazy_proxies:
            del self._lazy_proxies[key]

    def add_alias(self, name: Union[str, Type], target: Union[str, Type]):
        if List[target] in self._memoized_services:  # type: ignore
            del self._memoized_services[List[target]]  # type: ignore

        if name not in self._aliases:
            self._aliases[name] = []
        self._aliases[name].append(target)

    @overload
    def __getitem__(self, key: str) -> Any:
        ...

    @overload
    def __getitem__(self, key: Type[T]) -> T:
        ...

    def __getitem__(self, key: Union[str, Type[T]]) -> Union[Any, T]:
        # Always return a lazy proxy unless we're already resolving one (to avoid infinite recursion)
        if not getattr(self, '_resolving_lazy', False):
            # Special case: if the service is None, return it directly without lazy proxy
            # This allows "is None" checks to work correctly
            if key in self._services and self._services[key] is None:
                return None
            
            # Don't cache lazy proxies for factories - they should create new instances each time
            if key in self._factories:
                return LazyProxy(self, key)  # type: ignore[return-value]
            
            # Check if we already have a lazy proxy for this key
            if key not in self._lazy_proxies:
                self._lazy_proxies[key] = LazyProxy(self, key)  # type: ignore[assignment]
            return self._lazy_proxies[key]  # type: ignore[return-value]
        
        if key in self._factories:
            return self._factories[key](self)

        if is_optional(key):
            return self[unpack_optional(key)]

        service = self._get(key)

        if service is not _MISSING_SERVICE:
            return service

        if key in self._aliases:
            unaliased_key = self._aliases[key][0]  # By default return first aliased service
            if unaliased_key in self._factories:
                return self._factories[unaliased_key](self)
            service = self._get(unaliased_key)

        if service is not _MISSING_SERVICE:
            return service

        # Support aliasing
        if self._has_alias_list_for(key):
            result = [self._get(alias) for alias in self._aliases[key.__args__[0]]]  # type: ignore
            self._memoized_services[key] = result
            return result

        raise ServiceError(f"Service {key} is not registered.")

    def _get(self, key: Union[str, Type]) -> Any:
        if key in self._memoized_services:
            return self._memoized_services[key]

        if key not in self._services:
            return _MISSING_SERVICE

        value = self._services[key]

        if isinstance(value, LambdaType) and value.__name__ == "<lambda>":
            self._memoized_services[key] = value(self)
            return self._memoized_services[key]

        return value

    def __contains__(self, key) -> bool:
        contains = key in self._services or key in self._factories or key in self._aliases

        if contains:
            return contains

        if self._has_alias_list_for(key):
            return True

        if is_optional(key):
            return unpack_optional(key) in self

        return False

    def _has_alias_list_for(self, key: Union[str, Type]) -> bool:
        return hasattr(key, "__origin__") and hasattr(key, "__args__") and key.__origin__ == list and key.__args__[0] in self._aliases  # type: ignore

    @property
    def factories(self) -> Dict[Union[str, Type], Callable[["Container"], Any]]:
        return self._factories

    def clear_cache(self) -> None:
        self._memoized_services = {}
        self._lazy_proxies = {}
    
    def validate_dependencies(self) -> None:
        """
        Validate that all registered services can be resolved.
        
        This method attempts to resolve all services and their dependencies,
        raising an error if any service cannot be instantiated. This is useful
        for validating the container configuration at application startup.
        
        Raises:
            ServiceError: If any service cannot be resolved.
            ExecutionError: If any service is missing required dependencies.
        """
        from kink.errors.execution_error import ExecutionError
        
        errors = []
        
        # Temporarily set flag to bypass lazy loading
        original_resolving = getattr(self, '_resolving_lazy', False)
        self._resolving_lazy = True
        
        try:
            # Check all registered services
            for key in list(self._services.keys()):
                try:
                    # Attempt to resolve the service
                    _ = self[key]
                except (ServiceError, ExecutionError) as e:
                    errors.append(f"Service '{key}': {str(e)}")
                except Exception as e:
                    errors.append(f"Service '{key}': Unexpected error - {type(e).__name__}: {str(e)}")
            
            # Check all aliased services
            for alias_key, targets in self._aliases.items():
                for target in targets:
                    try:
                        # Attempt to resolve via alias
                        _ = self[alias_key]
                    except (ServiceError, ExecutionError) as e:
                        errors.append(f"Alias '{alias_key}' -> '{target}': {str(e)}")
                    except Exception as e:
                        errors.append(f"Alias '{alias_key}' -> '{target}': Unexpected error - {type(e).__name__}: {str(e)}")
        
        finally:
            self._resolving_lazy = original_resolving
        
        if errors:
            error_message = "Container validation failed with the following errors:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ServiceError(error_message)


di: Container = Container()


__all__ = ["Container", "di"]
