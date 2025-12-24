"""Generator for creating formatted changelog entries."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChangelogGenerator:
    """Generates formatted changelog sections from categorized changes."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize generator.
        
        Args:
            config: Configuration dict with formatting options
        """
        self.config = config or self._default_config()
        self.formatting = self.config.get('formatting', {})
    
    def _default_config(self) -> Dict[str, Any]:
        """Get default formatting configuration."""
        return {
            'formatting': {
                'max_pr_title_length': 100,
                'include_pr_links': True,
                'include_commit_links': False,
                'group_minor_changes': True,
                'minor_change_threshold': 5,
                'show_full_version_list': False
            }
        }
    
    def generate_section(
        self,
        from_tag: str,
        to_tag: str,
        categorized_changes: Dict[str, List[Dict[str, Any]]],
        category_info: Dict[str, Dict[str, Any]],
        date: Optional[str] = None,
        commit_count: Optional[int] = None
    ) -> str:
        """
        Generate a complete changelog section.
        
        Args:
            from_tag: Starting version tag
            to_tag: Ending version tag
            categorized_changes: Dict mapping categories to change lists
            category_info: Dict with category metadata (name, icon, priority)
            date: Optional date string
            commit_count: Optional number of commits
            
        Returns:
            Formatted markdown section
        """
        date_str = date or datetime.now().strftime('%Y-%m-%d')
        
        # Build header
        lines = [
            f"## {date_str}: Update to llama.cpp {to_tag}",
            ""
        ]
        
        # Generate summary
        summary = self._generate_summary(from_tag, to_tag, categorized_changes, commit_count)
        if summary:
            lines.extend([
                "### Summary",
                summary,
                ""
            ])
        
        # Generate notable changes sections
        notable_changes = self._generate_notable_changes(categorized_changes, category_info)
        if notable_changes:
            lines.extend([
                "### Notable Changes",
                "",
                notable_changes,
                ""
            ])
        
        # Generate additional changes summary
        additional = self._generate_additional_changes(categorized_changes, category_info)
        if additional:
            lines.extend([
                "### Additional Changes",
                additional,
                ""
            ])
        
        # Generate version range info
        lines.extend([
            "### Full Commit Range",
            f"- {from_tag} to {to_tag}" + (f" ({commit_count} commits)" if commit_count else ""),
            f"- Upstream releases: https://github.com/ggml-org/llama.cpp/compare/{from_tag}...{to_tag}",
            "",
            "---",
            ""
        ])
        
        return '\n'.join(lines)
    
    def _generate_summary(
        self,
        from_tag: str,
        to_tag: str,
        categorized_changes: Dict[str, List[Dict[str, Any]]],
        commit_count: Optional[int] = None
    ) -> str:
        """Generate summary paragraph."""
        commit_info = f"{commit_count} upstream commits" if commit_count else "multiple commits"
        
        # Count notable changes
        notable_count = sum(
            len(changes) for cat, changes in categorized_changes.items()
            if cat in ['breaking', 'feature', 'performance']
        )
        
        highlights = []
        if categorized_changes.get('breaking'):
            highlights.append("breaking changes")
        if categorized_changes.get('feature'):
            highlights.append("new features")
        if categorized_changes.get('performance'):
            highlights.append("performance improvements")
        
        highlight_str = ""
        if highlights:
            if len(highlights) == 1:
                highlight_str = f" with {highlights[0]}"
            elif len(highlights) == 2:
                highlight_str = f" with {highlights[0]} and {highlights[1]}"
            else:
                highlight_str = f" with {', '.join(highlights[:-1])}, and {highlights[-1]}"
        
        summary = f"Updated llama.cpp from {from_tag} to {to_tag}, incorporating {commit_info}{highlight_str}."
        
        return summary
    
    def _generate_notable_changes(
        self,
        categorized_changes: Dict[str, List[Dict[str, Any]]],
        category_info: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate notable changes section with categorized items."""
        lines = []
        
        # Categories to include in notable changes
        notable_categories = ['breaking', 'feature', 'performance', 'bugfix']
        
        for category_key in notable_categories:
            changes = categorized_changes.get(category_key, [])
            if not changes:
                continue
            
            info = category_info.get(category_key, {})
            icon = info.get('icon', '')
            name = info.get('name', category_key.title())
            
            # Add category header
            lines.append(f"#### {icon} {name}")
            
            # Add changes
            for change in changes:
                change_line = self._format_change_item(change)
                lines.append(change_line)
            
            lines.append("")  # Blank line between categories
        
        return '\n'.join(lines)
    
    def _format_change_item(self, change: Dict[str, Any]) -> str:
        """Format a single change item."""
        title = change.get('title', 'Untitled change')
        tag = change.get('tag', '')
        pr_number = change.get('pr_number')
        description = change.get('description', '')
        url = change.get('url', '')
        
        # Truncate title if needed
        max_length = self.formatting.get('max_pr_title_length', 100)
        if len(title) > max_length:
            title = title[:max_length-3] + '...'
        
        # Build the line
        line_parts = []
        
        # Add tag if available
        if tag:
            line_parts.append(f"**{tag}**:")
        else:
            line_parts.append("-")
        
        # Add title
        line_parts.append(title)
        
        # Add PR link if available and enabled
        if pr_number and self.formatting.get('include_pr_links', True):
            pr_url = url or f"https://github.com/ggml-org/llama.cpp/pull/{pr_number}"
            line_parts.append(f"([#{pr_number}]({pr_url}))")
        
        main_line = " ".join(line_parts)
        
        # Add description as sub-items if available
        if description and isinstance(description, list):
            sub_items = '\n'.join(f"  - {item}" for item in description[:3])  # Max 3 sub-items
            return f"- {main_line}\n{sub_items}"
        elif description and isinstance(description, str) and len(description) < 200:
            return f"- {main_line}\n  - {description}"
        else:
            return f"- {main_line}"
    
    def _generate_additional_changes(
        self,
        categorized_changes: Dict[str, List[Dict[str, Any]]],
        category_info: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate summary of additional minor changes."""
        # Categories considered "additional"
        additional_categories = ['documentation', 'example', 'maintenance']
        
        total_count = sum(
            len(categorized_changes.get(cat, []))
            for cat in additional_categories
        )
        
        if total_count == 0:
            return ""
        
        # Build summary
        parts = []
        for category_key in additional_categories:
            changes = categorized_changes.get(category_key, [])
            count = len(changes)
            if count > 0:
                info = category_info.get(category_key, {})
                name = info.get('name', category_key.title()).lower()
                parts.append(f"{count} {name}")
        
        summary = f"{total_count} minor improvements: " + ", ".join(parts) + "."
        
        # If threshold not met, show individual items
        threshold = self.formatting.get('minor_change_threshold', 5)
        if total_count <= threshold:
            lines = [summary, ""]
            for category_key in additional_categories:
                changes = categorized_changes.get(category_key, [])
                if changes:
                    for change in changes:
                        lines.append(self._format_change_item(change))
            return '\n'.join(lines)
        
        return summary
    
    def update_changelog(self, changelog_path: str, new_section: str) -> bool:
        """
        Update CHANGELOG.md with a new section.
        
        Args:
            changelog_path: Path to CHANGELOG.md
            new_section: New section content to add
            
        Returns:
            True if successful
        """
        try:
            # Read existing changelog
            try:
                with open(changelog_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                # Create new changelog
                content = "# Changelog\n\n"
            
            # Find insertion point (after the # Changelog header)
            lines = content.split('\n')
            insert_index = 0
            
            for i, line in enumerate(lines):
                if line.strip().startswith('# Changelog'):
                    insert_index = i + 1
                    # Skip any blank lines after header
                    while insert_index < len(lines) and not lines[insert_index].strip():
                        insert_index += 1
                    break
            
            # Insert new section
            lines.insert(insert_index, new_section)
            
            # Write back
            with open(changelog_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            logger.info(f"Updated changelog at {changelog_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating changelog: {e}")
            return False
    
    def format_change_list(self, changes: List[Dict[str, Any]]) -> str:
        """
        Format a list of changes as markdown.
        
        Args:
            changes: List of change dicts
            
        Returns:
            Formatted markdown string
        """
        lines = []
        for change in changes:
            lines.append(self._format_change_item(change))
        return '\n'.join(lines)
