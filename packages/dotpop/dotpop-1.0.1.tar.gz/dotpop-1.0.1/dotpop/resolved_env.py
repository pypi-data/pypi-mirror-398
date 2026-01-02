from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .exceptions import ImmutableVariableError, ModificationError


@dataclass
class SourceInfo:
    file: str
    line: int


@dataclass
class ResolvedEnv:
    
    values: Dict[str, str] = field(default_factory=dict)
    typed: Dict[str, Any] = field(default_factory=dict)
    sources: Dict[str, SourceInfo] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    _types: Dict[str, str] = field(default_factory=dict)
    _validators: Dict[str, Dict[str, str]] = field(default_factory=dict)
    _mutable_vars: Set[str] = field(default_factory=set)
    _conditional_vars: Set[str] = field(default_factory=set)
    _lazy: bool = False
    _resolver: Optional[Any] = None
    
    def get(self, key: str, default: Any = None) -> Any:
        if self._lazy and key in self.values and key not in self.typed:
            self._resolve_lazy(key)
        return self.typed.get(key, default)
    
    def get_str(self, key: str, default: str = None) -> Optional[str]:
        if self._lazy and key in self.values:
            if key not in self.typed:
                self._resolve_lazy(key)
            return str(self.typed.get(key, default))
        return self.values.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        if self._lazy and key in self.values and key not in self.typed:
            self._resolve_lazy(key)
        return self.typed[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.values
    
    def keys(self):
        return self.values.keys()
    
    def items(self):
        if self._lazy:
            for key in self.values.keys():
                if key not in self.typed:
                    self._resolve_lazy(key)
        return self.typed.items()
    
    def _resolve_lazy(self, key: str):
        from .types import convert_type
        from .validators import validate_value
        
        if self._resolver is None:
            raise ModificationError("Resolver not available for lazy loading")
        
        raw_value = self.values[key]
        source = self.sources[key]
        
        resolved_value = self._resolver.resolve(raw_value, key, source.file, source.line)
        
        type_name = self._types.get(key, "str")
        typed_value = convert_type(
            resolved_value,
            type_name,
            key,
            source.file,
            source.line
        )
        
        if key in self._validators:
            validate_value(
                key,
                typed_value,
                self._validators[key],
                source.file,
                source.line
            )
        
        self.typed[key] = typed_value
    
    def set(self, key: str, value: Any, force: bool = False) -> None:
        if key not in self.values:
            raise ModificationError(f"Variable '{key}' does not exist. Cannot set undefined variables.")
        
        if not force and key not in self._mutable_vars:
            raise ImmutableVariableError(
                f"Variable '{key}' is immutable. It was not defined in a conditional block. "
                f"Use force=True to override, or make it appear in a conditional."
            )
        
        from .types import convert_type
        from .validators import validate_value
        
        value_str = str(value)
        type_name = self._types.get(key, "str")
        
        try:
            typed_value = convert_type(
                value_str,
                type_name,
                key,
                self.sources[key].file,
                self.sources[key].line
            )
        except Exception as e:
            raise ModificationError(
                f"Failed to convert value for '{key}': {e}",
                self.sources[key].file,
                self.sources[key].line
            )
        
        if key in self._validators:
            try:
                validate_value(
                    key,
                    typed_value,
                    self._validators[key],
                    self.sources[key].file,
                    self.sources[key].line
                )
            except Exception as e:
                raise ModificationError(
                    f"Validation failed for '{key}': {e}",
                    self.sources[key].file,
                    self.sources[key].line
                )
        
        self.values[key] = value_str
        self.typed[key] = typed_value
    
    def set_conditional_var(self, key: str, value: Any) -> None:
        if key not in self._conditional_vars:
            raise ModificationError(
                f"Variable '{key}' is not a conditional variable. "
                f"Only variables used in @if/@elif conditions can be set with this method. "
                f"Conditional variables: {', '.join(sorted(self._conditional_vars))}"
            )
        
        self.set(key, value, force=True)
    
    def is_mutable(self, key: str) -> bool:
        return key in self._mutable_vars
    
    def is_conditional(self, key: str) -> bool:
        return key in self._conditional_vars
    
    def get_type(self, key: str) -> Optional[str]:
        return self._types.get(key)
    
    def get_validators(self, key: str) -> Optional[Dict[str, str]]:
        return self._validators.get(key)
    
    def get_mutable_vars(self) -> Set[str]:
        return self._mutable_vars.copy()
    
    def get_conditional_vars(self) -> Set[str]:
        return self._conditional_vars.copy()
    
    def __repr__(self) -> str:
        return f"ResolvedEnv(keys={list(self.values.keys())})"
