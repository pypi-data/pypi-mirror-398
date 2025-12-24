"""Categorizer for classifying changes into different types."""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChangeCategorizer:
    """Categorizes changes based on content, labels, and patterns."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize categorizer with rules.
        
        Args:
            config: Configuration dict with categorization rules
        """
        self.config = config or self._default_config()
        self.categories = self.config.get('categories', {})
    
    def _default_config(self) -> Dict[str, Any]:
        """Get default categorization configuration."""
        return {
            'categories': {
                'breaking': {
                    'name': 'Breaking Changes',
                    'icon': '⚠️',
                    'priority': 1,
                    'keywords': ['breaking', 'break', 'remove', 'deprecate', 'incompatible'],
                    'labels': ['breaking-change', 'breaking'],
                    'prefixes': ['breaking:', 'BREAKING:'],
                    'markers': ['BREAKING CHANGE:', 'BREAKING:']
                },
                'feature': {
                    'name': 'New Features',
                    'icon': '🆕',
                    'priority': 2,
                    'keywords': ['add', 'new', 'implement', 'support', 'introduce'],
                    'labels': ['enhancement', 'feature', 'new-feature'],
                    'prefixes': ['feat:', 'feature:'],
                    'paths': []
                },
                'performance': {
                    'name': 'Performance Improvements',
                    'icon': '🚀',
                    'priority': 3,
                    'keywords': ['optimize', 'performance', 'faster', 'speed', 'improve', 'acceleration'],
                    'labels': ['performance', 'optimization', 'perf'],
                    'prefixes': ['perf:', 'opt:', 'optimize:'],
                    'paths': []
                },
                'bugfix': {
                    'name': 'Bug Fixes',
                    'icon': '🐛',
                    'priority': 4,
                    'keywords': ['fix', 'bug', 'issue', 'crash', 'error', 'problem', 'resolve'],
                    'labels': ['bug', 'bugfix', 'fix'],
                    'prefixes': ['fix:', 'bugfix:'],
                    'paths': []
                },
                'documentation': {
                    'name': 'Documentation',
                    'icon': '📚',
                    'priority': 5,
                    'keywords': ['doc', 'docs', 'documentation', 'readme', 'comment', 'guide'],
                    'labels': ['documentation', 'docs'],
                    'prefixes': ['docs:', 'doc:'],
                    'paths': ['docs/', 'README']
                },
                'example': {
                    'name': 'Examples',
                    'icon': '🎨',
                    'priority': 6,
                    'keywords': ['example', 'demo', 'sample', 'tutorial'],
                    'labels': ['examples', 'example'],
                    'prefixes': ['example:', 'examples:'],
                    'paths': ['examples/']
                },
                'maintenance': {
                    'name': 'Maintenance',
                    'icon': '🔧',
                    'priority': 7,
                    'keywords': ['chore', 'refactor', 'cleanup', 'update', 'maintenance'],
                    'labels': ['maintenance', 'refactor', 'chore'],
                    'prefixes': ['chore:', 'refactor:', 'maint:'],
                    'paths': []
                }
            }
        }
    
    def categorize_change(
        self,
        title: str,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None,
        commit_type: Optional[str] = None
    ) -> str:
        """
        Categorize a change based on available information.
        
        Args:
            title: Change title or commit message
            description: Optional detailed description
            labels: Optional list of labels (from PR)
            file_paths: Optional list of file paths changed
            commit_type: Optional commit type (from conventional commits)
            
        Returns:
            Category name (key from categories dict)
        """
        # Combine text for analysis
        text = title.lower()
        if description:
            text += ' ' + description.lower()
        
        labels = labels or []
        file_paths = file_paths or []
        
        # Score each category
        scores = {}
        for category_key, category in self.categories.items():
            score = 0
            
            # Check commit type first (highest priority)
            if commit_type:
                if commit_type == category_key:
                    score += 100
            
            # Check labels (high priority)
            category_labels = category.get('labels', [])
            for label in labels:
                if label.lower() in [l.lower() for l in category_labels]:
                    score += 50
            
            # Check markers (high priority for breaking changes)
            markers = category.get('markers', [])
            for marker in markers:
                if marker.lower() in text:
                    score += 75
            
            # Check prefixes
            prefixes = category.get('prefixes', [])
            for prefix in prefixes:
                if title.lower().startswith(prefix.lower()):
                    score += 40
            
            # Check keywords
            keywords = category.get('keywords', [])
            for keyword in keywords:
                if keyword in text:
                    score += 10
            
            # Check file paths
            paths = category.get('paths', [])
            for path in paths:
                for file_path in file_paths:
                    if path.lower() in file_path.lower():
                        score += 20
            
            scores[category_key] = score
        
        # Find highest scoring category
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]
        
        # Default to maintenance
        return 'maintenance'
    
    def categorize_release(self, release_info: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize all changes in a release.
        
        Args:
            release_info: Dict with release information and changes
            
        Returns:
            Dict mapping category names to lists of changes
        """
        categorized = {key: [] for key in self.categories.keys()}
        
        changes = release_info.get('changes', [])
        for change in changes:
            category = self.categorize_change(
                title=change.get('title', ''),
                description=change.get('description', ''),
                labels=change.get('labels', []),
                file_paths=change.get('files', []),
                commit_type=change.get('type', None)
            )
            categorized[category].append(change)
        
        return categorized
    
    def get_category_info(self, category_key: str) -> Dict[str, Any]:
        """
        Get category information.
        
        Args:
            category_key: Category key
            
        Returns:
            Dict with category name, icon, priority
        """
        return self.categories.get(category_key, {
            'name': 'Other',
            'icon': '📦',
            'priority': 99
        })
    
    def get_sorted_categories(self) -> List[str]:
        """
        Get categories sorted by priority.
        
        Returns:
            List of category keys sorted by priority
        """
        items = [(k, v.get('priority', 99)) for k, v in self.categories.items()]
        items.sort(key=lambda x: x[1])
        return [k for k, _ in items]
