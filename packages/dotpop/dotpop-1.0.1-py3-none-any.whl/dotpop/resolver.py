import re
import random
from typing import Dict, Optional, Set

from .exceptions import ResolutionError


class Resolver:
    
    INTERPOLATION_PATTERN = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}')
    LIST_INDEX_PATTERN = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\[(-?\d+)\]\}')
    FUNCTION_PATTERN = re.compile(r'\$\{([a-z_]+)\(([^)]*)\)\}')
    
    def __init__(self, env: Dict[str, str], use_os_env: bool = True, random_seed: Optional[int] = None):
        self.env = env.copy()
        self.use_os_env = use_os_env
        self.random_seed = random_seed
        
        if random_seed is not None:
            random.seed(random_seed)
        
        if use_os_env:
            import os
            for key, value in os.environ.items():
                if key not in self.env:
                    self.env[key] = value
    
    def resolve(self, value: str, key: str = None, file: str = None, line: int = None) -> str:
        resolving = set()
        return self._resolve_recursive(value, key, resolving, file, line)
    
    def _resolve_recursive(
        self,
        value: str,
        key: Optional[str],
        resolving: Set[str],
        file: str = None,
        line: int = None
    ) -> str:
        
        if key and key in resolving:
            cycle = " -> ".join(resolving) + f" -> {key}"
            raise ResolutionError(f"Circular reference detected: {cycle}", file, line)
        
        if key:
            resolving.add(key)
        
        value = self._resolve_functions(value, file, line)
        value = self._resolve_list_indexing(value, resolving, file, line)
        
        def replacer(match):
            var_name = match.group(1)
            default = match.group(2)
            
            if var_name == key and default is not None:
                return default
            
            if var_name in self.env:
                var_value = self.env[var_name]
                return self._resolve_recursive(var_value, var_name, resolving.copy(), file, line)
            elif default is not None:
                return default
            else:
                raise ResolutionError(
                    f"Undefined variable: ${{{var_name}}}",
                    file,
                    line
                )
        
        try:
            resolved = self.INTERPOLATION_PATTERN.sub(replacer, value)
            return resolved
        except ResolutionError:
            raise
        except Exception as e:
            raise ResolutionError(f"Error resolving value: {e}", file, line)
    
    def _resolve_functions(self, value: str, file: str = None, line: int = None) -> str:
        
        def function_replacer(match):
            func_name = match.group(1)
            args_str = match.group(2).strip()
            
            if func_name == "rand":
                return self._call_rand(args_str, file, line)
            else:
                raise ResolutionError(
                    f"Unknown function: {func_name}()",
                    file,
                    line
                )
        
        return self.FUNCTION_PATTERN.sub(function_replacer, value)
    
    def _call_rand(self, args_str: str, file: str = None, line: int = None) -> str:
        
        if not args_str:
            return str(random.random())
        
        args = [arg.strip() for arg in args_str.split(',')]
        
        try:
            if len(args) == 1:
                max_val = int(args[0])
                return str(random.randint(0, max_val - 1))
            elif len(args) == 2:
                min_val = int(args[0])
                max_val = int(args[1])
                if min_val >= max_val:
                    raise ResolutionError(
                        f"rand(min, max): min must be less than max (got {min_val}, {max_val})",
                        file,
                        line
                    )
                return str(random.randint(min_val, max_val - 1))
            else:
                raise ResolutionError(
                    f"rand() takes 0, 1, or 2 arguments, got {len(args)}",
                    file,
                    line
                )
        except ValueError as e:
            raise ResolutionError(
                f"Invalid arguments for rand(): {e}",
                file,
                line
            )
    
    def _resolve_list_indexing(
        self,
        value: str,
        resolving: Set[str],
        file: str = None,
        line: int = None
    ) -> str:
        
        def list_replacer(match):
            var_name = match.group(1)
            index = int(match.group(2))
            
            if var_name not in self.env:
                raise ResolutionError(
                    f"Undefined variable for list access: {var_name}",
                    file,
                    line
                )
            
            var_value = self._resolve_recursive(
                self.env[var_name],
                var_name,
                resolving.copy(),
                file,
                line
            )
            
            items = [item.strip() for item in var_value.split(',')]
            
            try:
                return items[index]
            except IndexError:
                raise ResolutionError(
                    f"List index out of range: {var_name}[{index}] (list has {len(items)} items)",
                    file,
                    line
                )
        
        return self.LIST_INDEX_PATTERN.sub(list_replacer, value)
    
    def resolve_all(self, env: Dict[str, str], file: str = None) -> Dict[str, str]:
        resolved = {}
        
        for key, value in env.items():
            try:
                resolved[key] = self.resolve(value, key, file)
            except ResolutionError:
                raise
        
        return resolved
