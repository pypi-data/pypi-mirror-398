from typing import Optional


class DotpopError(Exception):
    
    def __init__(self, message: str, file: Optional[str] = None, line: Optional[int] = None):
        self.message = message
        self.file = file
        self.line = line
        
        full_message = message
        if file:
            full_message = f"{file}"
            if line is not None:
                full_message += f":{line}"
            full_message += f": {message}"
        
        super().__init__(full_message)
    
    def format_with_context(self, source_lines: list) -> str:
        if not self.file or self.line is None or not source_lines:
            return str(self)
        
        line_idx = self.line - 1
        if line_idx < 0 or line_idx >= len(source_lines):
            return str(self)
        
        error_line = source_lines[line_idx]
        line_num_str = str(self.line)
        
        context_lines = []
        context_lines.append(f"{self.file}:{self.line}: {self.message}")
        context_lines.append("")
        context_lines.append(f"{line_num_str:>4} | {error_line}")
        context_lines.append(" " * (len(line_num_str) + 3) + "| " + "^" * len(error_line.strip()))
        
        return "\n".join(context_lines)


class ParseError(DotpopError):
    pass


class ValidationError(DotpopError):
    pass


class ResolutionError(DotpopError):
    pass


class IncludeError(DotpopError):
    pass


class CircularIncludeError(IncludeError):
    pass


class ConditionError(DotpopError):
    pass


class TypeError_(DotpopError):
    pass


class ImmutableVariableError(DotpopError):
    pass


class ModificationError(DotpopError):
    pass
