import os

class Config:
    def __init__(self):
        self.github_api_url = "https://api.github.com"
        self.github_token = os.getenv("GITHUB_TOKEN")

        # DEPRECATED: Use repo_url instead. Kept for backward compatibility only.
        # This will be removed in a future version.
        self.github_repository_path = os.getenv("GITHUB_REPOSITORY_PATH")

        self.repo_provider = os.getenv("REPO_PROVIDER")

        # New URL-based config (for defaults/fallback only)
        self.repo_url = os.getenv("REPO_URL")
        self.gitlab_token = os.getenv("GITLAB_TOKEN")
        self.bitbucket_token = os.getenv("BITBUCKET_TOKEN")
        self.bitbucket_username = os.getenv("BITBUCKET_USERNAME")

    def set_repo_provider(self, provider):
        self.repo_provider = provider

    def set_github_token(self, token):
        self.github_token = token

    def set_github_repository_path(self, path):
        self.github_repository_path = path

    def get_github_api_url(self):
        """
        Get the GitHub API URL (e.g. https://api.github.com)
        """
        return self.github_api_url

    def get_github_token(self):
        """
        Get the GitHub token
        """
        return self.github_token

    def get_github_repository_path(self):
        """
        Get the Github repository path (e.g. BlocksOrg/client-monorepo)
        """
        return self.github_repository_path
    
    def get_github_repository_owner(self, raise_error_if_not_found = False):
        """
        Get the GitHub repository owner (e.g. BlocksOrg)
        """
        # Try parsing from repository_path (DEPRECATED but backward compatible)
        repository_path = self.get_github_repository_path()
        if repository_path:
            slug_parts = repository_path.split("/")
            if len(slug_parts) >= 2:
                return slug_parts[0]

        # Try parsing from generic repo_url
        if self.repo_url:
            owner, _ = self.parse_owner_repo_from_url(self.repo_url)
            if owner:
                return owner

        if raise_error_if_not_found:
            raise ValueError("Repo class: 'owner' argument is required")
        return None

    def get_github_repository_name(self, raise_error_if_not_found = False):
        """
        Get the Github repository name (e.g. client-monorepo)
        """
        # Try parsing from repository_path (DEPRECATED but backward compatible)
        repository_path = self.get_github_repository_path()
        if repository_path:
            slug_parts = repository_path.split("/")
            if len(slug_parts) >= 2:
                return '/'.join(slug_parts[1:])  # Support nested paths

        # Try parsing from generic repo_url
        if self.repo_url:
            _, repo = self.parse_owner_repo_from_url(self.repo_url)
            if repo:
                return repo

        if raise_error_if_not_found:
            raise ValueError("Repo class: 'repo' argument is required")
        return None

    def get_repo_provider(self):
        """
        Get the repo provider (GITHUB, GITLAB, etc)
        """
        return self.repo_provider

    # Provider tokens (for defaults/fallback)
    def get_gitlab_token(self):
        """Get the GitLab token"""
        return self.gitlab_token

    def set_gitlab_token(self, token):
        """Set the GitLab token"""
        self.gitlab_token = token

    def get_bitbucket_token(self):
        """Get the Bitbucket token"""
        return self.bitbucket_token

    def set_bitbucket_token(self, token):
        """Set the Bitbucket token"""
        self.bitbucket_token = token

    def get_bitbucket_username(self):
        """Get the Bitbucket username"""
        return self.bitbucket_username

    def set_bitbucket_username(self, username):
        """Set the Bitbucket username"""
        self.bitbucket_username = username

    # URL-based config
    def get_repo_url(self):
        """Get the repository URL (any provider)."""
        return self.repo_url

    def set_repo_url(self, url):
        """Set the repository URL (any provider)."""
        self.repo_url = url

    # Helper to parse owner/repo from URL
    def parse_owner_repo_from_url(self, url):
        """
        Parse owner and repo from a git URL.

        Examples:
            https://github.com/owner/repo.git -> ('owner', 'repo')
            https://github.com/owner/repo -> ('owner', 'repo')
            git@gitlab.com:owner/repo.git -> ('owner', 'repo')
            git@gitlab.com:owner/subowner/repo.git -> ('owner', 'subowner/repo')

        Returns:
            tuple: (owner, repo) or (None, None) if parsing fails
        """
        import re
        from urllib.parse import urlparse

        if not url:
            return None, None

        # Handle SSH URLs (git@github.com:owner/repo.git)
        ssh_match = re.match(r'git@[^:]+:(.+)', url)
        if ssh_match:
            path = ssh_match.group(1)
        else:
            # Handle HTTPS URLs
            parsed = urlparse(url)
            path = parsed.path

        # Remove leading slash, .git suffix
        path = path.lstrip('/').removesuffix('.git')
        parts = path.split('/')

        if len(parts) >= 2:
            return parts[0], '/'.join(parts[1:])  # Support nested: owner, subowner/repo

        return None, None
