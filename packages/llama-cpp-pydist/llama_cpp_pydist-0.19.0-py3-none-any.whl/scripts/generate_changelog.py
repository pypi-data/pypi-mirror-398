#!/usr/bin/env python3
"""
Generate enhanced changelog entries for llama_cpp_pydist.

This tool fetches release information from llama.cpp GitHub repository
and generates formatted changelog entries with PR details, categorization,
and summaries.
"""

import os
import re
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import click
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from changelog.github_client import GitHubClient
from changelog.parser import ChangeParser
from changelog.categorizer import ChangeCategorizer
from changelog.generator import ChangelogGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DOWNLOAD_LINK_PATTERN = re.compile(r'https://github\.com/ggml-org/llama\.cpp/releases/download/')


class ChangelogManager:
    """Manages the changelog generation process."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the changelog manager.
        
        Args:
            config_path: Optional path to config YAML file
        """
        self.config = self._load_config(config_path)
        self.github_client = GitHubClient(token=os.getenv('GITHUB_TOKEN'))
        self.parser = ChangeParser()
        self.categorizer = ChangeCategorizer(config=self.config)
        self.generator = ChangelogGenerator(config=self.config)
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Error loading config from {config_path}: {e}")
        
        # Try default location
        default_path = Path(__file__).parent / 'config.yaml'
        if default_path.exists():
            try:
                with open(default_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Error loading default config: {e}")
        
        return {}
    
    def fetch_changes(self, from_tag: str, to_tag: str) -> List[Dict[str, Any]]:
        """
        Fetch all changes between two tags.
        
        Args:
            from_tag: Starting tag
            to_tag: Ending tag
            
        Returns:
            List of change dicts
        """
        logger.info(f"Fetching changes from {from_tag} to {to_tag}")
        
        changes = []
        
        # Get all tags in range
        tags = self.github_client.fetch_tags_in_range(from_tag, to_tag)
        logger.info(f"Found {len(tags)} tags in range")
        
        # Fetch release info for each tag
        for tag in tags:
            logger.info(f"Fetching release info for {tag}")
            release = self.github_client.fetch_release_notes(tag)
            
            if release and release.get('body'):
                # Parse release notes
                parsed = self.parser.parse_release_notes(release['body'])
                
                # Extract PR references
                pr_refs = parsed.get('pr_references', [])
                
                # If we have PR references, fetch detailed info
                if pr_refs:
                    for pr_num in pr_refs[:5]:  # Limit to first 5 PRs per release
                        pr_info = self.github_client.fetch_pr_info(pr_num)
                        if pr_info:
                            changes.append({
                                'tag': tag,
                                'title': pr_info['title'],
                                'pr_number': pr_num,
                                'url': pr_info['url'],
                                'labels': pr_info['labels'],
                                'description': self._extract_description(pr_info['body']),
                                'type': None
                            })
                else:
                    # No PR references, use release title
                    title_pr = self.parser.extract_title_and_pr(release['name'])
                    changes.append({
                        'tag': tag,
                        'title': title_pr['title'] or release['name'],
                        'pr_number': title_pr['pr_number'],
                        'url': release['url'],
                        'labels': [],
                        'description': parsed.get('summary', ''),
                        'type': None
                    })
        
        logger.info(f"Collected {len(changes)} changes")
        return changes
    
    def _extract_description(self, pr_body: Optional[str]) -> Any:
        """Extract description from PR body."""
        if not pr_body:
            return None
        
        lines = pr_body.strip().split('\n')
        description_lines = []
        
        for line in lines[:10]:  # First 10 lines only
            line = line.strip()
            if self._is_download_link(line):
                continue
            if line and not line.startswith('#'):
                if line.startswith(('- ', '* ', '+ ')):
                    description_lines.append(line[2:])
                elif len(description_lines) < 3:
                    description_lines.append(line)
        
        return description_lines if description_lines else None

    @staticmethod
    def _is_download_link(line: str) -> bool:
        """Skip lines that look like release download entries."""
        return bool(DOWNLOAD_LINK_PATTERN.search(line))
    
    def categorize_changes(self, changes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize list of changes.
        
        Args:
            changes: List of change dicts
            
        Returns:
            Dict mapping categories to change lists
        """
        categorized = {}
        
        for change in changes:
            category = self.categorizer.categorize_change(
                title=change['title'],
                description=change.get('description'),
                labels=change.get('labels', []),
                commit_type=change.get('type')
            )
            
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(change)
        
        return categorized
    
    def generate_changelog_section(
        self,
        from_tag: str,
        to_tag: str,
        date: Optional[str] = None
    ) -> str:
        """
        Generate a complete changelog section.
        
        Args:
            from_tag: Starting tag
            to_tag: Ending tag
            date: Optional date string
            
        Returns:
            Formatted markdown section
        """
        # Fetch changes
        changes = self.fetch_changes(from_tag, to_tag)
        
        # Categorize
        categorized = self.categorize_changes(changes)
        
        # Get category info
        category_info = {}
        for cat_key in categorized.keys():
            category_info[cat_key] = self.categorizer.get_category_info(cat_key)
        
        # Generate section
        section = self.generator.generate_section(
            from_tag=from_tag,
            to_tag=to_tag,
            categorized_changes=categorized,
            category_info=category_info,
            date=date,
            commit_count=len(changes)
        )
        
        return section


@click.group()
def cli():
    """Generate enhanced changelog entries for llama_cpp_pydist."""
    pass


@cli.command()
@click.option('--from-tag', '-f', required=True, help='Starting tag (e.g., b6666)')
@click.option('--to-tag', '-t', required=True, help='Ending tag (e.g., b6792)')
@click.option('--date', '-d', help='Date for the entry (YYYY-MM-DD)')
@click.option('--config', '-c', help='Path to config YAML file')
@click.option('--preview', is_flag=True, help='Preview without updating file')
@click.option('--output', '-o', help='Output file (default: CHANGELOG.md)')
def generate(from_tag: str, to_tag: str, date: Optional[str], config: Optional[str], 
             preview: bool, output: Optional[str]):
    """Generate changelog section for a version range."""
    try:
        # Initialize manager
        manager = ChangelogManager(config_path=config)
        
        # Check rate limit
        rate_info = manager.github_client.get_rate_limit_info()
        if rate_info:
            core = rate_info.get('core', {})
            remaining = core.get('remaining', 0)
            logger.info(f"GitHub API rate limit: {remaining} requests remaining")
            if remaining < 10:
                logger.warning("Low API rate limit! Consider using a GitHub token.")
        
        # Generate section
        logger.info(f"Generating changelog for {from_tag} to {to_tag}")
        section = manager.generate_changelog_section(from_tag, to_tag, date)
        
        if preview:
            # Print to stdout
            click.echo("\n" + "="*80)
            click.echo("PREVIEW")
            click.echo("="*80 + "\n")
            click.echo(section)
        else:
            # Update changelog file
            changelog_path = output or 'CHANGELOG.md'
            if manager.generator.update_changelog(changelog_path, section):
                click.echo(f"✓ Updated {changelog_path}")
            else:
                click.echo(f"✗ Failed to update {changelog_path}", err=True)
                sys.exit(1)
    
    except KeyboardInterrupt:
        click.echo("\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--tag', '-t', required=True, help='Tag to fetch info for')
def info(tag: str):
    """Show information about a specific tag."""
    try:
        client = GitHubClient()
        
        release = client.fetch_release_notes(tag)
        if release:
            click.echo(f"\nTag: {release['tag']}")
            click.echo(f"Name: {release['name']}")
            click.echo(f"URL: {release['url']}")
            click.echo(f"Published: {release['published_at']}")
            click.echo(f"\nBody:\n{release['body']}")
        else:
            click.echo(f"No release found for tag {tag}", err=True)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def rate_limit():
    """Check GitHub API rate limit status."""
    try:
        client = GitHubClient()
        info = client.get_rate_limit_info()
        
        if info:
            click.echo("\nGitHub API Rate Limit Status:")
            click.echo("="*40)
            
            core = info.get('core', {})
            click.echo(f"\nCore API:")
            click.echo(f"  Limit: {core.get('limit', 'N/A')}")
            click.echo(f"  Remaining: {core.get('remaining', 'N/A')}")
            click.echo(f"  Resets at: {core.get('reset', 'N/A')}")
            
            search = info.get('search', {})
            click.echo(f"\nSearch API:")
            click.echo(f"  Limit: {search.get('limit', 'N/A')}")
            click.echo(f"  Remaining: {search.get('remaining', 'N/A')}")
            click.echo(f"  Resets at: {search.get('reset', 'N/A')}")
        else:
            click.echo("Unable to fetch rate limit info", err=True)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
