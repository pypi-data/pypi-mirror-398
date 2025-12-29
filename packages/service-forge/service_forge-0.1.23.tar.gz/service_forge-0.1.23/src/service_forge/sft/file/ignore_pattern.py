import fnmatch
import re
from pathlib import Path
from typing import List


class IgnorePattern:
    def __init__(self, patterns: List[str], base_path: Path):
        self.base_path = base_path.resolve()
        self.patterns: List[tuple[str, bool]] = []
        
        for pattern in patterns:
            pattern = pattern.strip()
            if not pattern or pattern.startswith('#'):
                continue
            
            is_negation = pattern.startswith('!')
            if is_negation:
                pattern = pattern[1:].strip()
            
            pattern = pattern.replace('\\', '/')
            
            if pattern.startswith('/'):
                pattern = pattern[1:]
            
            self.patterns.append((pattern, is_negation))
    
    def should_ignore(self, file_path: Path) -> bool:
        file_path = file_path.resolve()
        
        try:
            relative_path = file_path.relative_to(self.base_path)
        except ValueError:
            return False
        
        path_str = str(relative_path).replace('\\', '/')
        
        ignored = False
        for pattern, is_negation in self.patterns:
            if self._match_pattern(pattern, path_str, file_path):
                if is_negation:
                    ignored = False
                else:
                    ignored = True
        
        return ignored
    
    def _match_pattern(self, pattern: str, path_str: str, file_path: Path) -> bool:
        if pattern.endswith('/'):
            pattern = pattern[:-1]
            if not file_path.is_dir():
                return False
        
        if '**' in pattern:
            regex_pattern = pattern.replace('**', '.*')
            regex_pattern = fnmatch.translate(regex_pattern)
            return bool(re.match(regex_pattern, path_str))
        
        path_parts = path_str.split('/')
        
        if '/' in pattern:
            return fnmatch.fnmatch(path_str, pattern)
        
        return any(fnmatch.fnmatch(part, pattern) for part in path_parts)


def load_ignore_patterns(project_path: Path) -> IgnorePattern:
    project_path = project_path.resolve()
    ignore_file = project_path / '.sftignore'
    
    if not ignore_file.exists():
        return IgnorePattern([], project_path)
    
    try:
        with open(ignore_file, 'r', encoding='utf-8') as f:
            patterns = f.readlines()
        return IgnorePattern(patterns, project_path)
    except Exception:
        return IgnorePattern([], project_path)

