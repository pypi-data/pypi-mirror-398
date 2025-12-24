"""GitHub API client for fetching llama.cpp release information."""

import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from github import Github, GithubException
import logging

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API to fetch llama.cpp information."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token. If None, uses GITHUB_TOKEN env var.
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.github = Github(self.token) if self.token else Github()
        self.repo_name = "ggml-org/llama.cpp"
        self.repo = None
        self.session = requests.Session()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds between requests
        
    def _get_repo(self):
        """Get repository object, cached."""
        if self.repo is None:
            self.repo = self.github.get_repo(self.repo_name)
        return self.repo
    
    def _rate_limit_wait(self):
        """Wait if necessary to avoid rate limiting."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def fetch_release_notes(self, tag: str) -> Optional[Dict[str, Any]]:
        """
        Fetch release notes for a specific tag.
        
        Args:
            tag: Git tag (e.g., 'b6499')
            
        Returns:
            Dict with release information or None if not found
        """
        try:
            self._rate_limit_wait()
            repo = self._get_repo()
            release = repo.get_release(tag)
            
            return {
                'tag': tag,
                'name': release.title,
                'body': release.body,
                'published_at': release.published_at,
                'url': release.html_url,
                'author': release.author.login if release.author else None
            }
        except GithubException as e:
            if e.status == 404:
                logger.warning(f"Release not found for tag {tag}")
            else:
                logger.error(f"Error fetching release {tag}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching release {tag}: {e}")
            return None
    
    def fetch_pr_info(self, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Fetch pull request information.
        
        Args:
            pr_number: PR number
            
        Returns:
            Dict with PR information or None if not found
        """
        try:
            self._rate_limit_wait()
            repo = self._get_repo()
            pr = repo.get_pull(pr_number)
            
            return {
                'number': pr_number,
                'title': pr.title,
                'body': pr.body,
                'state': pr.state,
                'merged': pr.merged,
                'url': pr.html_url,
                'labels': [label.name for label in pr.labels],
                'author': pr.user.login if pr.user else None,
                'created_at': pr.created_at,
                'merged_at': pr.merged_at
            }
        except GithubException as e:
            if e.status == 404:
                logger.warning(f"PR #{pr_number} not found")
            else:
                logger.error(f"Error fetching PR #{pr_number}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching PR #{pr_number}: {e}")
            return None
    
    def fetch_commit_range(self, from_tag: str, to_tag: str) -> List[Dict[str, Any]]:
        """
        Fetch all commits between two tags.
        
        Args:
            from_tag: Starting tag
            to_tag: Ending tag
            
        Returns:
            List of commit information dicts
        """
        try:
            self._rate_limit_wait()
            repo = self._get_repo()
            comparison = repo.compare(from_tag, to_tag)
            
            commits = []
            for commit in comparison.commits:
                commits.append({
                    'sha': commit.sha,
                    'message': commit.commit.message,
                    'author': commit.commit.author.name,
                    'date': commit.commit.author.date,
                    'url': commit.html_url
                })
            
            return commits
        except GithubException as e:
            logger.error(f"Error fetching commits {from_tag}..{to_tag}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching commits: {e}")
            return []
    
    def fetch_releases_in_range(self, from_tag: str, to_tag: str) -> List[Dict[str, Any]]:
        """
        Fetch all releases between two tags (inclusive).
        
        Args:
            from_tag: Starting tag (e.g., 'b6666')
            to_tag: Ending tag (e.g., 'b6792')
            
        Returns:
            List of release information dicts
        """
        try:
            # Extract build numbers
            from_num = int(from_tag.replace('b', ''))
            to_num = int(to_tag.replace('b', ''))
            
            releases = []
            repo = self._get_repo()
            
            # Fetch all releases
            all_releases = repo.get_releases()
            
            for release in all_releases:
                tag = release.tag_name
                if tag.startswith('b'):
                    try:
                        num = int(tag.replace('b', ''))
                        if from_num <= num <= to_num:
                            self._rate_limit_wait()
                            releases.append({
                                'tag': tag,
                                'name': release.title,
                                'body': release.body,
                                'published_at': release.published_at,
                                'url': release.html_url,
                                'author': release.author.login if release.author else None
                            })
                    except ValueError:
                        continue
            
            # Sort by tag number
            releases.sort(key=lambda x: int(x['tag'].replace('b', '')))
            return releases
            
        except Exception as e:
            logger.error(f"Error fetching releases in range: {e}")
            return []
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get current rate limit information.
        
        Returns:
            Dict with rate limit details
        """
        try:
            rate_limit = self.github.get_rate_limit()
            return {
                'core': {
                    'limit': rate_limit.core.limit,
                    'remaining': rate_limit.core.remaining,
                    'reset': rate_limit.core.reset
                },
                'search': {
                    'limit': rate_limit.search.limit,
                    'remaining': rate_limit.search.remaining,
                    'reset': rate_limit.search.reset
                }
            }
        except Exception as e:
            logger.error(f"Error fetching rate limit: {e}")
            return {}
    
    def fetch_tags_in_range(self, from_tag: str, to_tag: str) -> List[str]:
        """
        Get list of all tags between two versions.
        
        Args:
            from_tag: Starting tag (e.g., 'b6666')
            to_tag: Ending tag (e.g., 'b6792')
            
        Returns:
            List of tag names
        """
        try:
            from_num = int(from_tag.replace('b', ''))
            to_num = int(to_tag.replace('b', ''))
            
            # Generate all possible tags in range
            tags = []
            for num in range(from_num, to_num + 1):
                tags.append(f'b{num}')
            
            return tags
        except ValueError as e:
            logger.error(f"Invalid tag format: {e}")
            return []
