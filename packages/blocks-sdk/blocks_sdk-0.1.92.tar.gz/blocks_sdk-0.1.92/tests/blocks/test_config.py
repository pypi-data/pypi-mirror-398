import os
import pytest
from unittest.mock import patch

from blocks.config import Config


class TestConfig:
    """Tests for Config class."""

    def test_init_loads_env_vars(self):
        """Test that Config loads environment variables on initialization."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GITLAB_TOKEN': 'test_gitlab_token',
            'BITBUCKET_TOKEN': 'test_bitbucket_token',
            'BITBUCKET_USERNAME': 'test_username',
            'GITHUB_REPOSITORY_PATH': 'owner/repo',
            'REPO_URL': 'https://github.com/owner/repo',
            'REPO_PROVIDER': 'github'
        }):
            config = Config()
            assert config.github_token == 'test_github_token'
            assert config.gitlab_token == 'test_gitlab_token'
            assert config.bitbucket_token == 'test_bitbucket_token'
            assert config.bitbucket_username == 'test_username'
            assert config.github_repository_path == 'owner/repo'
            assert config.repo_url == 'https://github.com/owner/repo'
            assert config.repo_provider == 'github'

    def test_set_and_get_gitlab_token(self):
        """Test setting and getting GitLab token."""
        config = Config()
        config.set_gitlab_token('new_gitlab_token')
        assert config.get_gitlab_token() == 'new_gitlab_token'

    def test_set_and_get_bitbucket_token(self):
        """Test setting and getting Bitbucket token."""
        config = Config()
        config.set_bitbucket_token('new_bitbucket_token')
        assert config.get_bitbucket_token() == 'new_bitbucket_token'

    def test_set_and_get_bitbucket_username(self):
        """Test setting and getting Bitbucket username."""
        config = Config()
        config.set_bitbucket_username('new_username')
        assert config.get_bitbucket_username() == 'new_username'

    def test_set_and_get_repo_url(self):
        """Test setting and getting repository URL."""
        config = Config()
        config.set_repo_url('https://gitlab.com/owner/repo')
        assert config.get_repo_url() == 'https://gitlab.com/owner/repo'

    def test_parse_owner_repo_from_https_url(self):
        """Test parsing owner and repo from HTTPS URL."""
        config = Config()
        owner, repo = config.parse_owner_repo_from_url('https://github.com/owner/repo.git')
        assert owner == 'owner'
        assert repo == 'repo'

    def test_parse_owner_repo_from_https_url_without_git(self):
        """Test parsing owner and repo from HTTPS URL without .git suffix."""
        config = Config()
        owner, repo = config.parse_owner_repo_from_url('https://github.com/owner/repo')
        assert owner == 'owner'
        assert repo == 'repo'

    def test_parse_owner_repo_from_ssh_url(self):
        """Test parsing owner and repo from SSH URL."""
        config = Config()
        owner, repo = config.parse_owner_repo_from_url('git@github.com:owner/repo.git')
        assert owner == 'owner'
        assert repo == 'repo'

    def test_parse_owner_repo_nested_path(self):
        """Test parsing owner and repo with nested path."""
        config = Config()
        owner, repo = config.parse_owner_repo_from_url('https://gitlab.com/owner/subowner/repo.git')
        assert owner == 'owner'
        assert repo == 'subowner/repo'

    def test_parse_owner_repo_from_none(self):
        """Test parsing with None URL returns (None, None)."""
        config = Config()
        owner, repo = config.parse_owner_repo_from_url(None)
        assert owner is None
        assert repo is None

    def test_parse_owner_repo_from_invalid_url(self):
        """Test parsing with invalid URL returns (None, None)."""
        config = Config()
        owner, repo = config.parse_owner_repo_from_url('https://github.com/')
        assert owner is None
        assert repo is None

    def test_get_github_repository_owner_from_path(self):
        """Test getting owner from repository_path (deprecated but backward compatible)."""
        config = Config()
        config.github_repository_path = 'owner/repo'
        assert config.get_github_repository_owner() == 'owner'

    def test_get_github_repository_owner_from_url(self):
        """Test getting owner from repo_url."""
        config = Config()
        config.github_repository_path = None
        config.repo_url = 'https://github.com/owner/repo'
        assert config.get_github_repository_owner() == 'owner'

    def test_get_github_repository_owner_raises_error_if_not_found(self):
        """Test that get_github_repository_owner raises error when not found and flag is set."""
        config = Config()
        config.github_repository_path = None
        config.repo_url = None
        with pytest.raises(ValueError, match="'owner' argument is required"):
            config.get_github_repository_owner(raise_error_if_not_found=True)

    def test_get_github_repository_name_from_path(self):
        """Test getting repo name from repository_path (deprecated but backward compatible)."""
        config = Config()
        config.github_repository_path = 'owner/repo'
        assert config.get_github_repository_name() == 'repo'

    def test_get_github_repository_name_from_url(self):
        """Test getting repo name from repo_url."""
        config = Config()
        config.github_repository_path = None
        config.repo_url = 'https://github.com/owner/repo'
        assert config.get_github_repository_name() == 'repo'

    def test_get_github_repository_name_nested_path(self):
        """Test getting repo name with nested path."""
        config = Config()
        config.github_repository_path = None
        config.repo_url = 'https://gitlab.com/owner/subowner/repo'
        assert config.get_github_repository_name() == 'subowner/repo'

    def test_get_github_repository_name_raises_error_if_not_found(self):
        """Test that get_github_repository_name raises error when not found and flag is set."""
        config = Config()
        config.github_repository_path = None
        config.repo_url = None
        with pytest.raises(ValueError, match="'repo' argument is required"):
            config.get_github_repository_name(raise_error_if_not_found=True)

    def test_get_repo_provider(self):
        """Test getting repository provider."""
        config = Config()
        config.repo_provider = 'gitlab'
        assert config.get_repo_provider() == 'gitlab'

    def test_set_repo_provider(self):
        """Test setting repository provider."""
        config = Config()
        config.set_repo_provider('bitbucket')
        assert config.repo_provider == 'bitbucket'
