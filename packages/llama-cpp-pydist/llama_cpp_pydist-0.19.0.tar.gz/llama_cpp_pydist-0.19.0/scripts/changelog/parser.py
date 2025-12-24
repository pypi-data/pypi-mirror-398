"""Parser for extracting structured information from release notes and commits."""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChangeParser:
    """Parser for extracting change information from text."""
    
    # Pattern for PR references: #1234 or (#1234)
    PR_PATTERN = re.compile(r'#(\d+)')
    
    # Pattern for breaking change markers
    BREAKING_PATTERNS = [
        re.compile(r'BREAKING[\s:]', re.IGNORECASE),
        re.compile(r'breaking[\s-]change', re.IGNORECASE),
        re.compile(r'\[breaking\]', re.IGNORECASE),
    ]
    
    # Pattern for conventional commit prefixes
    COMMIT_PREFIX_PATTERN = re.compile(
        r'^(feat|fix|docs|style|refactor|perf|test|chore|build|ci)(\(.+?\))?:\s*(.+)',
        re.IGNORECASE
    )
    
    def __init__(self):
        """Initialize the parser."""
        pass
    
    def parse_release_notes(self, notes: str) -> Dict[str, Any]:
        """
        Parse release notes to extract structured information.
        
        Args:
            notes: Release notes text
            
        Returns:
            Dict with parsed information
        """
        if not notes:
            return {
                'summary': '',
                'pr_references': [],
                'breaking_changes': [],
                'features': [],
                'fixes': []
            }
        
        # Extract PR references
        pr_refs = self.extract_pr_references(notes)
        
        # Detect breaking changes
        is_breaking = self.detect_breaking_changes(notes)
        
        # Split into lines for analysis
        lines = notes.strip().split('\n')
        
        # Try to identify different sections
        summary = self._extract_summary(lines)
        features = self._extract_features(lines)
        fixes = self._extract_fixes(lines)
        breaking_changes = self._extract_breaking_changes(lines) if is_breaking else []
        
        return {
            'summary': summary,
            'pr_references': pr_refs,
            'breaking_changes': breaking_changes,
            'features': features,
            'fixes': fixes,
            'is_breaking': is_breaking,
            'raw_text': notes
        }
    
    def extract_pr_references(self, text: str) -> List[int]:
        """
        Extract PR numbers from text.
        
        Args:
            text: Text to search
            
        Returns:
            List of PR numbers
        """
        if not text:
            return []
        
        matches = self.PR_PATTERN.findall(text)
        return [int(m) for m in matches]
    
    def detect_breaking_changes(self, text: str) -> bool:
        """
        Detect if text indicates breaking changes.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if breaking changes detected
        """
        if not text:
            return False
        
        for pattern in self.BREAKING_PATTERNS:
            if pattern.search(text):
                return True
        
        return False
    
    def parse_commit_message(self, message: str) -> Dict[str, Any]:
        """
        Parse a commit message to extract type and description.
        
        Args:
            message: Commit message
            
        Returns:
            Dict with type, scope, description
        """
        if not message:
            return {
                'type': 'other',
                'scope': None,
                'description': '',
                'full_message': ''
            }
        
        # Take first line
        first_line = message.split('\n')[0].strip()
        
        # Try conventional commit format
        match = self.COMMIT_PREFIX_PATTERN.match(first_line)
        if match:
            commit_type = match.group(1).lower()
            scope = match.group(2).strip('()') if match.group(2) else None
            description = match.group(3).strip()
            
            # Map commit types
            type_mapping = {
                'feat': 'feature',
                'fix': 'bugfix',
                'docs': 'documentation',
                'perf': 'performance',
                'refactor': 'refactor',
                'test': 'test',
                'chore': 'maintenance',
                'build': 'build',
                'ci': 'ci',
                'style': 'style'
            }
            
            return {
                'type': type_mapping.get(commit_type, commit_type),
                'scope': scope,
                'description': description,
                'full_message': message
            }
        
        # If not conventional format, try to infer from keywords
        description = first_line
        commit_type = self._infer_type_from_description(description)
        
        return {
            'type': commit_type,
            'scope': None,
            'description': description,
            'full_message': message
        }
    
    def _extract_summary(self, lines: List[str]) -> str:
        """Extract summary from release notes lines."""
        # Usually the first non-empty line
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                return line
        return ''
    
    def _extract_features(self, lines: List[str]) -> List[str]:
        """Extract feature descriptions from lines."""
        features = []
        in_features_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check for features section header
            if re.match(r'#+\s*(new\s+)?features?', line, re.IGNORECASE):
                in_features_section = True
                continue
            
            # Check if we've moved to a different section
            if line.startswith('#'):
                in_features_section = False
                continue
            
            # Extract feature items
            if in_features_section and line.startswith(('- ', '* ', '+ ')):
                features.append(line[2:].strip())
        
        return features
    
    def _extract_fixes(self, lines: List[str]) -> List[str]:
        """Extract bug fix descriptions from lines."""
        fixes = []
        in_fixes_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check for fixes section header
            if re.match(r'#+\s*(bug\s+)?fix(es)?', line, re.IGNORECASE):
                in_fixes_section = True
                continue
            
            # Check if we've moved to a different section
            if line.startswith('#'):
                in_fixes_section = False
                continue
            
            # Extract fix items
            if in_fixes_section and line.startswith(('- ', '* ', '+ ')):
                fixes.append(line[2:].strip())
        
        return fixes
    
    def _extract_breaking_changes(self, lines: List[str]) -> List[str]:
        """Extract breaking change descriptions from lines."""
        breaking = []
        in_breaking_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check for breaking changes section header
            if re.match(r'#+\s*breaking\s+change', line, re.IGNORECASE):
                in_breaking_section = True
                continue
            
            # Check if we've moved to a different section
            if line.startswith('#'):
                in_breaking_section = False
                continue
            
            # Extract breaking change items
            if in_breaking_section and line.startswith(('- ', '* ', '+ ')):
                breaking.append(line[2:].strip())
        
        return breaking
    
    def _infer_type_from_description(self, description: str) -> str:
        """Infer change type from description text."""
        description_lower = description.lower()
        
        # Check for keywords
        if any(kw in description_lower for kw in ['add', 'new', 'implement', 'support']):
            return 'feature'
        elif any(kw in description_lower for kw in ['fix', 'bug', 'issue', 'crash', 'error']):
            return 'bugfix'
        elif any(kw in description_lower for kw in ['optimize', 'performance', 'faster', 'speed']):
            return 'performance'
        elif any(kw in description_lower for kw in ['doc', 'docs', 'documentation', 'readme']):
            return 'documentation'
        elif any(kw in description_lower for kw in ['refactor', 'restructure', 'reorganize']):
            return 'refactor'
        elif any(kw in description_lower for kw in ['test', 'testing']):
            return 'test'
        elif any(kw in description_lower for kw in ['example', 'demo', 'sample']):
            return 'example'
        
        return 'other'
    
    def extract_title_and_pr(self, text: str) -> Dict[str, Any]:
        """
        Extract title and PR number from a combined string like "Title (#1234)".
        
        Args:
            text: Text containing title and PR reference
            
        Returns:
            Dict with title and pr_number
        """
        if not text:
            return {'title': '', 'pr_number': None}
        
        # Pattern for "Title (#1234)" or "Title (PR #1234)"
        match = re.match(r'(.+?)\s*\((?:PR\s*)?#(\d+)\)', text.strip())
        if match:
            return {
                'title': match.group(1).strip(),
                'pr_number': int(match.group(2))
            }
        
        # No PR reference found
        return {
            'title': text.strip(),
            'pr_number': None
        }
