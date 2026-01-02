import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .exceptions import ParseError


@dataclass
class ParsedLine:
    type: str
    key: Optional[str] = None
    value: Optional[str] = None
    type_name: Optional[str] = None
    validators: Optional[Dict[str, str]] = None
    condition: Optional[str] = None
    include_path: Optional[str] = None
    override: bool = False
    line_number: int = 0
    raw_line: str = ""


class Parser:
    
    COMMENT_PATTERN = re.compile(r'^\s*#')
    BLANK_PATTERN = re.compile(r'^\s*$')
    INCLUDE_PATTERN = re.compile(r'^\s*@include\s+"([^"]+)"')
    CONDITION_PATTERN = re.compile(r'^\s*@(if|elif)\s+(.+)')
    ELSE_PATTERN = re.compile(r'^\s*@else\s*$')
    END_PATTERN = re.compile(r'^\s*@end\s*$')
    HEREDOC_START_PATTERN = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)(?::([a-z]+))?\s*=\s*<<<(\w+)\s*$')
    INHERIT_PATTERN = re.compile(r'^\s*@inherit\s+"([^"]+)"')
    
    OVERRIDE_PATTERN = re.compile(r'^\s*(!|@override\s+)(.+)')
    EXPORT_PATTERN = re.compile(r'^\s*export\s+(.+)')
    ASSIGNMENT_PATTERN = re.compile(
        r'^\s*([A-Za-z_][A-Za-z0-9_]*)'
        r'(?::([a-z]+))?'
        r'\s*=\s*'
        r'(.*?)'
        r'(?:\s*\|\s*(.+))?$'
    )
    
    def __init__(self, text: str, file: str = "<string>"):
        self.text = text
        self.file = file
        self.lines = text.splitlines()
    
    def parse(self) -> List[ParsedLine]:
        parsed_lines = []
        
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            
            heredoc_match = self.HEREDOC_START_PATTERN.match(line)
            if heredoc_match:
                parsed, lines_consumed = self._parse_heredoc(i)
                parsed_lines.append(parsed)
                i += lines_consumed
                continue
            
            parsed = self._parse_line(line, i + 1)
            parsed_lines.append(parsed)
            i += 1
        
        return parsed_lines
    
    def _parse_heredoc(self, start_line: int) -> Tuple[ParsedLine, int]:
        line = self.lines[start_line]
        match = self.HEREDOC_START_PATTERN.match(line)
        
        key = match.group(1)
        type_name = match.group(2) or "str"
        delimiter = match.group(3)
        
        value_lines = []
        i = start_line + 1
        
        while i < len(self.lines):
            if self.lines[i].strip() == delimiter:
                break
            value_lines.append(self.lines[i])
            i += 1
        
        if i >= len(self.lines):
            raise ParseError(
                f"Unterminated heredoc: missing '{delimiter}'",
                self.file,
                start_line + 1
            )
        
        value = '\n'.join(value_lines)
        lines_consumed = i - start_line + 1
        
        return ParsedLine(
            type='assignment',
            key=key,
            value=value,
            type_name=type_name,
            validators={},
            override=False,
            line_number=start_line + 1,
            raw_line=line
        ), lines_consumed
    
    def _parse_line(self, line: str, line_num: int) -> ParsedLine:
        
        if self.COMMENT_PATTERN.match(line):
            return ParsedLine(type='comment', line_number=line_num, raw_line=line)
        
        if self.BLANK_PATTERN.match(line):
            return ParsedLine(type='blank', line_number=line_num, raw_line=line)
        
        inherit_match = self.INHERIT_PATTERN.match(line)
        if inherit_match:
            return ParsedLine(
                type='inherit',
                include_path=inherit_match.group(1),
                line_number=line_num,
                raw_line=line
            )
        
        include_match = self.INCLUDE_PATTERN.match(line)
        if include_match:
            return ParsedLine(
                type='include',
                include_path=include_match.group(1),
                line_number=line_num,
                raw_line=line
            )
        
        condition_match = self.CONDITION_PATTERN.match(line)
        if condition_match:
            return ParsedLine(
                type=condition_match.group(1),
                condition=condition_match.group(2).strip(),
                line_number=line_num,
                raw_line=line
            )
        
        if self.ELSE_PATTERN.match(line):
            return ParsedLine(type='else', line_number=line_num, raw_line=line)
        
        if self.END_PATTERN.match(line):
            return ParsedLine(type='end', line_number=line_num, raw_line=line)
        
        override_match = self.OVERRIDE_PATTERN.match(line)
        override = False
        if override_match:
            override = True
            line = override_match.group(2)
        
        export_match = self.EXPORT_PATTERN.match(line)
        if export_match:
            line = export_match.group(1)
        
        assignment_match = self.ASSIGNMENT_PATTERN.match(line)
        if assignment_match:
            key = assignment_match.group(1)
            type_name = assignment_match.group(2) or "str"
            raw_value = assignment_match.group(3)
            validators_str = assignment_match.group(4)
            
            value = self._parse_value(raw_value)
            
            validators = self._parse_validators(validators_str) if validators_str else {}
            
            return ParsedLine(
                type='assignment',
                key=key,
                value=value,
                type_name=type_name,
                validators=validators,
                override=override,
                line_number=line_num,
                raw_line=line
            )
        
        raise ParseError(f"Invalid syntax: {line}", self.file, line_num)
    
    def _parse_value(self, raw_value: str) -> str:
        raw_value = raw_value.strip()
        
        if (raw_value.startswith('"') and raw_value.endswith('"')) or \
           (raw_value.startswith("'") and raw_value.endswith("'")):
            value = raw_value[1:-1]
            value = value.replace('\\n', '\n')
            value = value.replace('\\t', '\t')
            value = value.replace('\\r', '\r')
            value = value.replace('\\"', '"')
            value = value.replace("\\'", "'")
            value = value.replace('\\\\', '\\')
            return value
        
        return raw_value
    
    def _parse_validators(self, validators_str: str) -> Dict[str, str]:
        validators = {}
        
        parts = [p.strip() for p in validators_str.split('|')]
        for part in parts:
            if '=' in part:
                name, value = part.split('=', 1)
                validators[name.strip()] = value.strip()
            else:
                validators[part] = ""
        
        return validators


def parse_file(path: Path) -> List[ParsedLine]:
    try:
        text = path.read_text(encoding='utf-8')
        parser = Parser(text, str(path))
        return parser.parse()
    except FileNotFoundError:
        raise ParseError(f"File not found: {path}")
    except UnicodeDecodeError as e:
        raise ParseError(f"Cannot decode file: {e}", str(path))


def parse_string(text: str, file: str = "<string>") -> List[ParsedLine]:
    parser = Parser(text, file)
    return parser.parse()
