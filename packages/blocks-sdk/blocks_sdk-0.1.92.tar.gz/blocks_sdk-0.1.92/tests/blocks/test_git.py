import os
import subprocess
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from blocks.git import Git
from blocks.config import Config


@pytest.fixture
def mock_config():
    """Create a mocked Config object for testing."""
    config = MagicMock(spec=Config)
    config.get_github_token.return_value = "test_token"
    config.get_github_repository_path.return_value = "test_owner/test_repo"
    config.get_repo_url.return_value = None  # For backward compatibility tests
    config.get_gitlab_token.return_value = None
    config.get_bitbucket_token.return_value = None
    config.get_bitbucket_username.return_value = None
    config.get_repo_provider.return_value = None
    return config


@pytest.fixture
def git_instance(mock_config):
    """Create a Git instance with a mocked Config for testing."""
    return Git(mock_config)


class TestGit:
    def test_init(self, mock_config):
        """Test that Git instance is initialized correctly with config."""
        git = Git(mock_config)
        assert git.config == mock_config

    def test_get_repo_https_url_with_token(self, git_instance):
        """Test that get_repo_https_url returns correct URL with token."""
        # Updated to use new oauth2 authentication format
        expected_url = "https://oauth2:test_token@github.com/test_owner/test_repo.git"
        assert git_instance.get_repo_https_url() == expected_url

    def test_get_repo_https_url_without_token(self, mock_config, git_instance):
        """Test that get_repo_https_url returns correct URL without token."""
        # Set token to None
        mock_config.get_github_token.return_value = None
        expected_url = "https://github.com/test_owner/test_repo.git"
        assert git_instance.get_repo_https_url() == expected_url

    def test_get_repo_url_returns_https_url(self, git_instance):
        """Test that get_repo_url calls get_repo_https_url."""
        with patch.object(git_instance, 'get_repo_https_url') as mock_get_https:
            mock_get_https.return_value = "test_url"
            result = git_instance.get_repo_url()
            assert result == "test_url"
            mock_get_https.assert_called_once()

    def test_set_repo_path(self, git_instance):
        """Test that set_repo_path calls config.set_github_repository_path."""
        git_instance.set_repo_path("new_owner/new_repo")
        git_instance.config.set_github_repository_path.assert_called_once_with("new_owner/new_repo")

    def test_set_token(self, git_instance):
        """Test that set_token calls config.set_github_token."""
        git_instance.set_token("new_token")
        git_instance.config.set_github_token.assert_called_once_with("new_token")

    @patch('blocks.git.bash')
    def test_configure(self, mock_bash, git_instance):
        """Test that configure sets up git config correctly."""
        git_instance.configure()
        assert mock_bash.call_count == 2
        mock_bash.assert_any_call("git config --local user.email 'bot@blocksorg.com'")
        mock_bash.assert_any_call("git config --local user.name 'BlocksOrg'")

    @patch('blocks.git.bash')
    def test_checkout_basic(self, mock_bash, git_instance):
        """Test that checkout calls git checkout with correct parameters."""
        git_instance.checkout("main")
        mock_bash.assert_called_once_with("git checkout  main")

    @patch('blocks.git.bash')
    def test_checkout_with_options(self, mock_bash, git_instance):
        """Test that checkout handles all options correctly."""
        git_instance.checkout("feature-branch", new_branch=True, track=True, force=True)
        mock_bash.assert_called_once_with("git checkout -b --track --force feature-branch")

    @patch('blocks.git.bash')
    def test_checkout_orphan(self, mock_bash, git_instance):
        """Test that checkout handles orphan option correctly."""
        git_instance.checkout("orphan-branch", orphan=True)
        mock_bash.assert_called_once_with("git checkout --orphan orphan-branch")

    @patch('blocks.git.bash')
    def test_clone_basic(self, mock_bash, git_instance):
        """Test basic clone functionality."""
        with patch.object(git_instance, 'get_repo_url', return_value="https://github.com/test/repo.git"):
            with patch.object(Path, 'exists', return_value=False):
                with patch.object(Path, 'iterdir', return_value=[]):
                    with patch.object(os, 'chdir'):
                        with patch.object(git_instance, 'configure'):
                            git_instance.clone()
                            # Verify the clone command is called with authenticated URL
                            call_args = mock_bash.call_args[0][0]
                            assert "git clone" in call_args
                            assert "oauth2:test_token@github.com" in call_args

    @patch('blocks.git.bash')
    def test_clone_with_options(self, mock_bash, git_instance):
        """Test clone with all options."""
        with patch.object(git_instance, 'get_repo_url', return_value="https://github.com/test/repo.git"):
            with patch.object(Path, 'exists', return_value=False):
                with patch.object(Path, 'iterdir', return_value=[]):
                    with patch.object(os, 'chdir'):
                        with patch.object(git_instance, 'configure'):
                            git_instance.clone(
                                ref="main",
                                target_dir="/target",
                                depth=1,
                                single_branch=True,
                                recursive=True,
                                shallow_submodules=True
                            )
                            # Verify the clone command is called with the correct parameters
                            call_args = mock_bash.call_args[0][0]
                            assert "git clone" in call_args
                            assert "--branch main" in call_args
                            assert "--depth 1" in call_args
                            assert "--single-branch" in call_args
                            assert "--recursive" in call_args
                            assert "--shallow-submodules" in call_args
                            assert "oauth2:test_token@github.com" in call_args
                            assert "/target" in call_args

    def test_clone_non_empty_dir(self, git_instance):
        """Test that clone raises ValueError when target directory is not empty."""
        with patch.object(git_instance, 'get_repo_url', return_value="https://github.com/test/repo.git"):
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'iterdir', return_value=[MagicMock()]):
                    with pytest.raises(ValueError, match="Target directory .* already exists and is not empty"):
                        git_instance.clone(target_dir="/non-empty-dir")

    @patch('blocks.git.bash')
    def test_clone_creates_parent_dirs(self, mock_bash, git_instance):
        """Test that clone creates parent directories if they don't exist."""
        with patch.object(git_instance, 'get_repo_url', return_value="https://test_url"):
            with patch.object(Path, 'exists') as mock_exists:
                # First call for target_dir check, second for target_dir.parent check
                mock_exists.side_effect = [False, False]
                with patch.object(Path, 'mkdir') as mock_mkdir:
                    with patch.object(os, 'chdir'):
                        git_instance.clone(target_dir="/new/path")
                        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch('blocks.git.bash')
    @patch('blocks.git.os.chdir')
    def test_clone_configures_git(self, mock_chdir, mock_bash, git_instance):
        """Test that clone configures git after cloning."""
        with patch.object(git_instance, 'get_repo_url', return_value="https://test_url"):
            with patch.object(Path, 'exists', return_value=False):
                with patch.object(Path, 'iterdir', return_value=[]):
                    with patch.object(Path, 'absolute', return_value="/absolute/path"):
                        with patch.object(git_instance, 'configure') as mock_configure:
                            current_dir = os.getcwd()
                            git_instance.clone(target_dir="/target")
                            
                            # Verify current directory is restored
                            assert mock_chdir.call_count == 2
                            mock_chdir.assert_any_call("/absolute/path")
                            mock_chdir.assert_any_call(current_dir)
                            
                            # Verify configure is called
                            mock_configure.assert_called_once()

    @patch('blocks.git.bash')
    def test_init_repo(self, mock_bash, git_instance):
        """Test that init calls git init."""
        git_instance.init()
        mock_bash.assert_called_once_with("git init")

    @patch('blocks.git.bash')
    def test_pull_basic(self, mock_bash, git_instance):
        """Test basic pull functionality."""
        git_instance.pull()
        mock_bash.assert_called_once_with("git pull  origin HEAD")

    @patch('blocks.git.bash')
    def test_pull_with_options(self, mock_bash, git_instance):
        """Test pull with all options."""
        git_instance.pull(remote="upstream", branch="develop", rebase=True, ff_only=True)
        mock_bash.assert_called_once_with("git pull --rebase --ff-only upstream develop")

    @patch('blocks.git.bash')
    def test_push_basic(self, mock_bash, git_instance):
        """Test basic push functionality."""
        git_instance.push()
        mock_bash.assert_called_once_with("git push  origin HEAD")

    @patch('blocks.git.bash')
    def test_push_with_options(self, mock_bash, git_instance):
        """Test push with all options."""
        git_instance.push(remote="upstream", branch="feature", publish=True, force=True, tags=True)
        mock_bash.assert_called_once_with("git push -u --force --tags upstream feature")

    @patch('blocks.git.bash')
    def test_push_with_force_with_lease(self, mock_bash, git_instance):
        """Test push with force-with-lease option."""
        git_instance.push(force_with_lease=True)
        mock_bash.assert_called_once_with("git push --force-with-lease origin HEAD")

    @patch('blocks.git.bash')
    def test_commit_basic(self, mock_bash, git_instance):
        """Test basic commit functionality."""
        git_instance.commit("Test commit message")
        mock_bash.assert_called_once_with("git commit -m 'Test commit message'")

    @patch('blocks.git.bash')
    def test_commit_with_options(self, mock_bash, git_instance):
        """Test commit with all options."""
        git_instance.commit(
            "Test commit message",
            amend=True,
            all=True,
            allow_empty=True,
            signoff=True
        )
        mock_bash.assert_called_once_with(
            "git commit -m 'Test commit message' --amend --all --allow-empty --signoff"
        )

    @patch('blocks.git.bash')
    def test_commit_with_amend_no_edit(self, mock_bash, git_instance):
        """Test commit with amend and no_edit options."""
        git_instance.commit("", amend=True, no_edit=True)
        mock_bash.assert_called_once_with("git commit --amend --no-edit")

    @patch('blocks.git.bash')
    def test_commit_with_single_quotes_in_message(self, mock_bash, git_instance):
        """Test commit with single quotes in message that need escaping."""
        git_instance.commit("Test 'quoted' message")
        # Just check that the bash command was called once
        assert mock_bash.call_count == 1
        # and that the commit command contains the message
        assert "git commit" in mock_bash.call_args[0][0]
        assert "Test" in mock_bash.call_args[0][0]
        assert "quoted" in mock_bash.call_args[0][0]
        assert "message" in mock_bash.call_args[0][0]

    @patch('blocks.git.bash')
    def test_add_file(self, mock_bash, git_instance):
        """Test adding a specific file."""
        git_instance.add("test_file.py")
        mock_bash.assert_called_once_with("git add test_file.py")
    
    @patch('blocks.git.bash')
    def test_add_file_with_string_argument(self, mock_bash, git_instance):
        """Test adding a specific file using string argument (git.add("filename") syntax)."""
        git_instance.add("another_file.py")
        mock_bash.assert_called_once_with("git add another_file.py")

    @patch('blocks.git.bash')
    def test_add_all_files(self, mock_bash, git_instance):
        """Test adding all files."""
        git_instance.add(all=True)
        mock_bash.assert_called_once_with("git add .")
        
    def test_add_without_parameters(self, git_instance):
        """Test that add raises ValueError when neither file nor all are provided."""
        with pytest.raises(ValueError, match="Either 'file' or 'all' keyword argument must be provided"):
            git_instance.add()
            
    def test_add_with_empty_file_string(self, git_instance):
        """Test that add raises ValueError when file is an empty string and all is False."""
        with pytest.raises(ValueError, match="Either 'file' or 'all' keyword argument must be provided"):
            git_instance.add(file="", all=False)

    @patch('blocks.git.bash')
    def test_branch_create(self, mock_bash, git_instance):
        """Test creating a branch without checking it out."""
        git_instance.branch("new-branch")
        mock_bash.assert_called_once_with("git branch new-branch")

    def test_branch_create_and_checkout(self, git_instance):
        """Test creating a branch and checking it out."""
        with patch.object(git_instance, 'checkout') as mock_checkout:
            git_instance.branch("new-branch", checkout=True)
            mock_checkout.assert_called_once_with("new-branch", new_branch=True)


class TestGitMultiProvider:
    """Tests for multi-provider Git support (GitHub, GitLab, Bitbucket)."""

    @pytest.fixture
    def multi_config(self):
        """Create a mocked Config with multi-provider support."""
        config = MagicMock(spec=Config)
        config.get_github_token.return_value = "github_token"
        config.get_gitlab_token.return_value = "gitlab_token"
        config.get_bitbucket_token.return_value = "bitbucket_token"
        config.get_bitbucket_username.return_value = "bitbucket_user"
        config.get_repo_url.return_value = None
        config.get_github_repository_path.return_value = None
        config.get_repo_provider.return_value = None
        return config

    @pytest.fixture
    def git_multi(self, multi_config):
        """Create a Git instance for multi-provider testing."""
        return Git(multi_config)

    def test_normalize_url_adds_git_suffix(self, git_multi):
        """Test that _normalize_url adds .git suffix if missing."""
        url = "https://github.com/owner/repo"
        normalized = git_multi._normalize_url(url)
        assert normalized == "https://github.com/owner/repo.git"

    def test_normalize_url_preserves_git_suffix(self, git_multi):
        """Test that _normalize_url preserves existing .git suffix."""
        url = "https://github.com/owner/repo.git"
        normalized = git_multi._normalize_url(url)
        assert normalized == "https://github.com/owner/repo.git"

    def test_normalize_url_skips_query_params(self, git_multi):
        """Test that _normalize_url doesn't add .git if URL has query params."""
        url = "https://github.com/owner/repo?ref=main"
        normalized = git_multi._normalize_url(url)
        assert normalized == "https://github.com/owner/repo?ref=main"

    def test_normalize_url_handles_none(self, git_multi):
        """Test that _normalize_url handles None gracefully."""
        assert git_multi._normalize_url(None) is None

    def test_detect_provider_github(self, git_multi):
        """Test provider detection for GitHub."""
        url = "https://github.com/owner/repo"
        provider = git_multi._detect_provider_from_url(url)
        assert provider == "github"

    def test_detect_provider_github_enterprise(self, git_multi):
        """Test provider detection for GitHub Enterprise."""
        url = "https://github.company.com/owner/repo"
        provider = git_multi._detect_provider_from_url(url)
        assert provider == "github"

    def test_detect_provider_gitlab(self, git_multi):
        """Test provider detection for GitLab."""
        url = "https://gitlab.com/owner/repo"
        provider = git_multi._detect_provider_from_url(url)
        assert provider == "gitlab"

    def test_detect_provider_gitlab_enterprise(self, git_multi):
        """Test provider detection for GitLab Enterprise."""
        url = "https://gitlab.company.com/owner/repo"
        provider = git_multi._detect_provider_from_url(url)
        assert provider == "gitlab"

    def test_detect_provider_bitbucket(self, git_multi):
        """Test provider detection for Bitbucket."""
        url = "https://bitbucket.org/owner/repo"
        provider = git_multi._detect_provider_from_url(url)
        assert provider == "bitbucket"

    def test_detect_provider_defaults_to_github(self, git_multi):
        """Test that provider detection defaults to GitHub for unknown domains."""
        url = "https://unknown.com/owner/repo"
        provider = git_multi._detect_provider_from_url(url)
        assert provider == "github"

    def test_get_token_explicit_takes_priority(self, git_multi):
        """Test that explicit token takes priority over config."""
        token = git_multi._get_token_for_provider("github", explicit_token="explicit_token")
        assert token == "explicit_token"

    def test_get_token_github_from_config(self, git_multi):
        """Test getting GitHub token from config."""
        token = git_multi._get_token_for_provider("github")
        assert token == "github_token"

    def test_get_token_gitlab_from_config(self, git_multi):
        """Test getting GitLab token from config."""
        token = git_multi._get_token_for_provider("gitlab")
        assert token == "gitlab_token"

    def test_get_token_bitbucket_from_config(self, git_multi):
        """Test getting Bitbucket token from config."""
        token = git_multi._get_token_for_provider("bitbucket")
        assert token == "bitbucket_token"

    def test_get_username_explicit_takes_priority(self, git_multi):
        """Test that explicit username takes priority over config."""
        username = git_multi._get_username_for_provider("bitbucket", explicit_username="explicit_user")
        assert username == "explicit_user"

    def test_get_username_bitbucket_from_config(self, git_multi):
        """Test getting Bitbucket username from config."""
        username = git_multi._get_username_for_provider("bitbucket")
        assert username == "bitbucket_user"

    def test_get_username_returns_none_for_github(self, git_multi):
        """Test that username returns None for GitHub."""
        username = git_multi._get_username_for_provider("github")
        assert username is None

    def test_build_authenticated_url_github(self, git_multi):
        """Test building authenticated URL for GitHub."""
        url = "https://github.com/owner/repo.git"
        auth_url = git_multi._build_authenticated_url(url, "github", "token123")
        assert auth_url == "https://oauth2:token123@github.com/owner/repo.git"

    def test_build_authenticated_url_gitlab(self, git_multi):
        """Test building authenticated URL for GitLab."""
        url = "https://gitlab.com/owner/repo.git"
        auth_url = git_multi._build_authenticated_url(url, "gitlab", "token456")
        assert auth_url == "https://oauth2:token456@gitlab.com/owner/repo.git"

    def test_build_authenticated_url_bitbucket(self, git_multi):
        """Test building authenticated URL for Bitbucket."""
        url = "https://bitbucket.org/owner/repo.git"
        auth_url = git_multi._build_authenticated_url(url, "bitbucket", "token789", username="user123")
        assert auth_url == "https://user123:token789@bitbucket.org/owner/repo.git"

    def test_build_authenticated_url_bitbucket_requires_username(self, git_multi):
        """Test that Bitbucket requires username for authentication."""
        url = "https://bitbucket.org/owner/repo.git"
        with pytest.raises(ValueError, match="Bitbucket requires a username"):
            git_multi._build_authenticated_url(url, "bitbucket", "token789")

    def test_build_authenticated_url_no_token_returns_original(self, git_multi):
        """Test that no token returns original URL (for public repos)."""
        url = "https://github.com/owner/repo.git"
        auth_url = git_multi._build_authenticated_url(url, "github", None)
        assert auth_url == url

    def test_construct_url_from_parts(self, git_multi):
        """Test constructing URL from base_url and repo_path."""
        url = git_multi._construct_url_from_parts("https://github.com", "owner/repo")
        assert url == "https://github.com/owner/repo.git"

    def test_construct_url_from_parts_nested(self, git_multi):
        """Test constructing URL with nested repo path."""
        url = git_multi._construct_url_from_parts("https://gitlab.com", "owner/subowner/repo")
        assert url == "https://gitlab.com/owner/subowner/repo.git"

    def test_construct_url_handles_trailing_slash(self, git_multi):
        """Test that URL construction handles trailing slashes."""
        url = git_multi._construct_url_from_parts("https://github.com/", "/owner/repo")
        assert url == "https://github.com/owner/repo.git"

    @patch('blocks.git.bash')
    def test_clone_with_full_url(self, mock_bash, git_multi):
        """Test cloning with full URL and explicit token."""
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'iterdir', return_value=[]):
                with patch.object(os, 'chdir'):
                    with patch.object(git_multi, 'configure'):
                        git_multi.clone(url="https://github.com/owner/repo", token="token123")

                        # Verify the clone command was called with authenticated URL
                        call_args = mock_bash.call_args[0][0]
                        assert "git clone" in call_args
                        assert "oauth2:token123@github.com" in call_args

    @patch('blocks.git.bash')
    def test_clone_with_base_url_and_repo_path(self, mock_bash, git_multi):
        """Test cloning with base_url and repo_path."""
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'iterdir', return_value=[]):
                with patch.object(os, 'chdir'):
                    with patch.object(git_multi, 'configure'):
                        git_multi.clone(
                            base_url="https://gitlab.company.com",
                            repo_path="team/project",
                            provider="gitlab",
                            token="token456"
                        )

                        # Verify the clone command was called with constructed authenticated URL
                        call_args = mock_bash.call_args[0][0]
                        assert "git clone" in call_args
                        assert "oauth2:token456@gitlab.company.com" in call_args
                        assert "team/project.git" in call_args

    @patch('blocks.git.bash')
    def test_clone_bitbucket_with_username(self, mock_bash, git_multi):
        """Test cloning from Bitbucket with username."""
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'iterdir', return_value=[]):
                with patch.object(os, 'chdir'):
                    with patch.object(git_multi, 'configure'):
                        git_multi.clone(
                            url="https://bitbucket.org/owner/repo",
                            provider="bitbucket",
                            token="app_password",
                            username="bitbucket_user"
                        )

                        # Verify Bitbucket authentication format
                        call_args = mock_bash.call_args[0][0]
                        assert "git clone" in call_args
                        assert "bitbucket_user:app_password@bitbucket.org" in call_args

    @patch('blocks.git.bash')
    def test_clone_auto_detects_provider(self, mock_bash, git_multi):
        """Test that clone auto-detects provider from URL."""
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'iterdir', return_value=[]):
                with patch.object(os, 'chdir'):
                    with patch.object(git_multi, 'configure'):
                        git_multi.clone(url="https://gitlab.com/owner/repo", token="token123")

                        # Verify it uses oauth2 format (GitLab)
                        call_args = mock_bash.call_args[0][0]
                        assert "oauth2:token123@gitlab.com" in call_args

    def test_clone_requires_url_or_base_url(self, git_multi):
        """Test that clone raises ValueError when no URL is provided."""
        with pytest.raises(ValueError, match="No URL provided"):
            git_multi.clone()

    @patch('blocks.git.bash')
    def test_get_repo_https_url_with_new_config(self, mock_bash, git_multi):
        """Test get_repo_https_url with new URL-based config."""
        git_multi.config.get_repo_url.return_value = "https://gitlab.com/owner/repo"

        url = git_multi.get_repo_https_url()

        assert "oauth2:gitlab_token@gitlab.com" in url
        assert url.endswith("owner/repo.git")

    @patch('blocks.git.bash')
    def test_get_repo_https_url_backward_compatibility(self, mock_bash, git_multi):
        """Test get_repo_https_url falls back to repository_path (backward compatible)."""
        git_multi.config.get_repo_url.return_value = None
        git_multi.config.get_github_repository_path.return_value = "owner/repo"

        url = git_multi.get_repo_https_url()

        assert "oauth2:github_token@github.com" in url
        assert url.endswith("owner/repo.git")