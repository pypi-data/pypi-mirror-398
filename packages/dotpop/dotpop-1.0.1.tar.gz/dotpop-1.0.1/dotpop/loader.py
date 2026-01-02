import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from .conditions import ConditionEvaluator
from .exceptions import CircularIncludeError, ConditionError, IncludeError
from .parser import ParsedLine, parse_file, parse_string
from .resolved_env import ResolvedEnv, SourceInfo
from .resolver import Resolver
from .types import convert_type
from .validators import validate_value


class Loader:
    
    def __init__(self, strict: bool = True, use_os_env: bool = True, lazy: bool = False, random_seed: Optional[int] = None):
        self.strict = strict
        self.use_os_env = use_os_env
        self.lazy = lazy
        self.random_seed = random_seed
        self.included_files: Set[Path] = set()
        self.warnings: List[str] = []
        self.inherit_base: Optional[Path] = None
        self.main_file: Optional[str] = None
    
    def load_file(self, path: Path, format: str = "auto") -> ResolvedEnv:
        
        if path.name == ".dpop" or path.name.startswith(".dpop."):
            format = "dpop"
        else:
            raise ValueError(
                f"Only .dpop or .dpop.* files are supported, got: {path.name}. "
                f"Examples: .dpop, .dpop.production, .dpop.database"
            )
        
        self.included_files = set()
        self.warnings = []
        self.inherit_base = None
        self.main_file = str(path)
        
        raw_env = {}
        sources = {}
        types = {}
        validators_map = {}
        
        self._process_file(
            path,
            raw_env,
            sources,
            types,
            validators_map,
            format == "dpop"
        )
        
        if self.lazy:
            resolver = Resolver(raw_env, self.use_os_env, self.random_seed)
            
            resolved_env = ResolvedEnv(
                values=raw_env,
                typed={},
                sources=sources,
                warnings=self.warnings
            )
            resolved_env._types = types
            resolved_env._validators = validators_map
            resolved_env._resolver = resolver
            resolved_env._lazy = True
            
            mutable_vars = set()
            conditional_vars = set()
            parsed_lines = parse_file(path)
            self._identify_conditional_vars(parsed_lines, mutable_vars, conditional_vars)
            resolved_env._mutable_vars = mutable_vars
            resolved_env._conditional_vars = conditional_vars
            
            return resolved_env
        
        resolver = Resolver(raw_env, self.use_os_env, self.random_seed)
        resolved_values = resolver.resolve_all(raw_env, str(path))
        
        typed_values = {}
        for key, value in resolved_values.items():
            type_name = types.get(key, "str")
            source = sources[key]
            
            typed_value = convert_type(
                value,
                type_name,
                key,
                source.file,
                source.line
            )
            typed_values[key] = typed_value
            
            if key in validators_map:
                validate_value(
                    key,
                    typed_value,
                    validators_map[key],
                    source.file,
                    source.line
                )
        
        mutable_vars = set()
        conditional_vars = set()
        
        parsed_lines = parse_file(path)
        self._identify_conditional_vars(
            parsed_lines,
            mutable_vars,
            conditional_vars
        )
        
        resolved_env = ResolvedEnv(
            values=resolved_values,
            typed=typed_values,
            sources=sources,
            warnings=self.warnings
        )
        resolved_env._types = types
        resolved_env._validators = validators_map
        resolved_env._mutable_vars = mutable_vars
        resolved_env._conditional_vars = conditional_vars
        
        return resolved_env
    
    def load_string(self, text: str, format: str = "auto", file: str = "<string>") -> ResolvedEnv:
        
        if format in ("dotpop", "dpop"):
            format = "dpop"
        elif format == "auto":
            if "@include" in text or "@if" in text or (":" in text and "=" in text):
                format = "dpop"
            else:
                format = "env"
        
        self.included_files = set()
        self.warnings = []
        self.inherit_base = None
        self.main_file = file
        
        parsed_lines = parse_string(text, file)
        
        raw_env = {}
        sources = {}
        types = {}
        validators_map = {}
        
        self._process_lines(
            parsed_lines,
            Path(file).parent if file != "<string>" else Path.cwd(),
            raw_env,
            sources,
            types,
            validators_map,
            format == "dpop",
            file
        )
        
        resolver = Resolver(raw_env, self.use_os_env, self.random_seed)
        resolved_values = resolver.resolve_all(raw_env, file)
        
        typed_values = {}
        for key, value in resolved_values.items():
            type_name = types.get(key, "str")
            source = sources[key]
            
            typed_value = convert_type(
                value,
                type_name,
                key,
                source.file,
                source.line
            )
            typed_values[key] = typed_value
            
            if key in validators_map:
                validate_value(
                    key,
                    typed_value,
                    validators_map[key],
                    source.file,
                    source.line
                )
        
        return ResolvedEnv(
            values=resolved_values,
            typed=typed_values,
            sources=sources,
            warnings=self.warnings
        )
    
    def _process_file(
        self,
        path: Path,
        raw_env: Dict[str, str],
        sources: Dict[str, SourceInfo],
        types: Dict[str, str],
        validators_map: Dict[str, Dict[str, str]],
        is_dpop: bool
    ):
        
        abs_path = path.resolve()
        if abs_path in self.included_files:
            raise CircularIncludeError(f"Circular include detected: {path}")
        
        self.included_files.add(abs_path)
        
        try:
            parsed_lines = parse_file(path)
            self._process_lines(
                parsed_lines,
                path.parent,
                raw_env,
                sources,
                types,
                validators_map,
                is_dpop,
                str(path)
            )
        finally:
            self.included_files.discard(abs_path)
    
    def _evaluate_condition_with_typed_values(
        self,
        condition: str,
        raw_env: Dict[str, str],
        types_map: Dict[str, str],
        file: str,
        line: int
    ) -> bool:
        env_for_eval = {}
        resolver = Resolver(raw_env, self.use_os_env, self.random_seed)
        
        for key, raw_value in raw_env.items():
            try:
                resolved = resolver.resolve(raw_value, key)
            except:
                resolved = raw_value
            
            type_name = types_map.get(key, "str")
            
            if type_name == "secret" and resolved.startswith("ENC("):
                try:
                    typed_value = convert_type(resolved, type_name, key, file, line)
                    env_for_eval[key] = str(typed_value)
                except:
                    env_for_eval[key] = resolved
            else:
                env_for_eval[key] = resolved
        
        evaluator = ConditionEvaluator(env_for_eval)
        return evaluator.evaluate(condition, file, line)
    
    def _process_lines(
        self,
        parsed_lines: List[ParsedLine],
        base_dir: Path,
        raw_env: Dict[str, str],
        sources: Dict[str, SourceInfo],
        types: Dict[str, str],
        validators_map: Dict[str, Dict[str, str]],
        is_dpop: bool,
        current_file: str
    ):
        
        condition_stack = []
        skip_stack = [False]
        
        i = 0
        while i < len(parsed_lines):
            line = parsed_lines[i]
            
            current_skip = skip_stack[-1]
            
            if line.type == 'blank' or line.type == 'comment':
                i += 1
                continue
            
            elif line.type == 'inherit':
                if not is_dpop:
                    raise IncludeError(
                        "Inheritance not allowed in .env files",
                        current_file,
                        line.line_number
                    )
                
                if current_skip:
                    i += 1
                    continue
                
                if self.inherit_base is not None:
                    raise IncludeError(
                        "Multiple @inherit directives not allowed",
                        current_file,
                        line.line_number
                    )
                
                base_path = base_dir / line.include_path
                
                if not base_path.exists():
                    base_path_candidates = [
                        base_dir / f".dpop.{line.include_path}",
                        base_dir / line.include_path
                    ]
                    
                    for candidate in base_path_candidates:
                        if candidate.exists():
                            base_path = candidate
                            break
                    else:
                        raise IncludeError(
                            f"Inherit base file not found: {line.include_path}",
                            current_file,
                            line.line_number
                        )
                
                self.inherit_base = base_path
                self._process_file(
                    base_path,
                    raw_env,
                    sources,
                    types,
                    validators_map,
                    is_dpop
                )
                
                i += 1
                continue
            
            elif line.type == 'if':
                if not is_dpop:
                    raise ConditionError(
                        "Conditions not allowed in .env files",
                        current_file,
                        line.line_number
                    )
                
                result = self._evaluate_condition_with_typed_values(
                    line.condition,
                    raw_env,
                    types,
                    current_file,
                    line.line_number
                )
                
                condition_stack.append({'type': 'if', 'matched': result})
                skip_stack.append(current_skip or not result)
                
                i += 1
                continue
            
            elif line.type == 'elif':
                if not condition_stack:
                    raise ConditionError(
                        "@elif without matching @if",
                        current_file,
                        line.line_number
                    )
                
                current_block = condition_stack[-1]
                if current_block['type'] not in ('if', 'elif'):
                    raise ConditionError(
                        "@elif after @else",
                        current_file,
                        line.line_number
                    )
                
                result = self._evaluate_condition_with_typed_values(
                    line.condition,
                    raw_env,
                    types,
                    current_file,
                    line.line_number
                )
                
                matched_before = current_block['matched']
                current_block['type'] = 'elif'
                current_block['matched'] = matched_before or result
                
                skip_stack[-1] = current_skip or matched_before or not result
                
                i += 1
                continue
            
            elif line.type == 'else':
                if not condition_stack:
                    raise ConditionError(
                        "@else without matching @if",
                        current_file,
                        line.line_number
                    )
                
                current_block = condition_stack[-1]
                if current_block['type'] == 'else':
                    raise ConditionError(
                        "Multiple @else blocks",
                        current_file,
                        line.line_number
                    )
                
                matched_before = current_block['matched']
                current_block['type'] = 'else'
                
                skip_stack[-1] = current_skip or matched_before
                
                i += 1
                continue
            
            elif line.type == 'end':
                if not condition_stack:
                    raise ConditionError(
                        "@end without matching @if",
                        current_file,
                        line.line_number
                    )
                
                condition_stack.pop()
                skip_stack.pop()
                
                i += 1
                continue
            
            elif line.type == 'include':
                if not is_dpop:
                    raise IncludeError(
                        "Includes not allowed in .env files",
                        current_file,
                        line.line_number
                    )
                
                if current_skip:
                    i += 1
                    continue
                
                include_path = base_dir / line.include_path
                
                resolver = Resolver(raw_env, self.use_os_env, self.random_seed)
                resolved_path_str = resolver.resolve(
                    str(include_path),
                    None,
                    current_file,
                    line.line_number
                )
                include_path = Path(resolved_path_str)
                
                if not include_path.exists():
                    raise IncludeError(
                        f"Include file not found: {include_path}",
                        current_file,
                        line.line_number
                    )
                
                import sys
                print(f"[DEBUG] Including {include_path} from {current_file}", file=sys.stderr)
                
                self._process_file(
                    include_path,
                    raw_env,
                    sources,
                    types,
                    validators_map,
                    is_dpop
                )
                
                print(f"[DEBUG] After include, raw_env has {len(raw_env)} keys", file=sys.stderr)
                
                i += 1
                continue
            
            elif line.type == 'assignment':
                if current_skip:
                    i += 1
                    continue
                
                from_inherited_base = self.inherit_base and line.key in raw_env and sources.get(line.key).file == str(self.inherit_base)
                from_main_file = current_file == self.main_file
                can_override_includes = from_main_file and line.key in raw_env
                
                should_set = (
                    line.override or
                    line.key not in raw_env or
                    from_inherited_base or
                    can_override_includes
                )
                
                if should_set:
                    raw_env[line.key] = line.value
                    sources[line.key] = SourceInfo(current_file, line.line_number)
                    types[line.key] = line.type_name
                    
                    if line.validators:
                        validators_map[line.key] = line.validators
                
                i += 1
                continue
            
            i += 1
        
        if condition_stack:
            raise ConditionError(
                f"Unclosed condition block (missing @end)",
                current_file
            )
    
    def _identify_conditional_vars(
        self,
        parsed_lines: List[ParsedLine],
        mutable_vars: Set[str],
        conditional_vars: Set[str]
    ):
        import re
        
        in_conditional = False
        
        for line in parsed_lines:
            if line.type in ('if', 'elif'):
                in_conditional = True
                var_match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*[!=]=', line.condition)
                if var_match:
                    conditional_vars.add(var_match.group(1))
                defined_match = re.search(r'(?:not_)?defined\(([A-Za-z_][A-Za-z0-9_]*)\)', line.condition)
                if defined_match:
                    conditional_vars.add(defined_match.group(1))
            
            elif line.type == 'end':
                in_conditional = False
            
            elif line.type == 'assignment' and in_conditional:
                mutable_vars.add(line.key)


def load(
    path: str,
    format: str = "auto",
    strict: bool = True,
    use_os_env: bool = True,
    lazy: bool = False,
    random_seed: Optional[int] = None
) -> ResolvedEnv:
    loader = Loader(strict=strict, use_os_env=use_os_env, lazy=lazy, random_seed=random_seed)
    return loader.load_file(Path(path), format=format)


def loads(
    text: str,
    format: str = "auto",
    strict: bool = True,
    use_os_env: bool = True,
    file: str = "<string>"
) -> ResolvedEnv:
    loader = Loader(strict=strict, use_os_env=use_os_env)
    return loader.load_string(text, format=format, file=file)
