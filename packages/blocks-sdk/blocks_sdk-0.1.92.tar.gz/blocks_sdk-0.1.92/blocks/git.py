import os
import contextlib
from blocks.config import Config
from .utils import bash
from pathlib import Path

class Git:
    def __init__(self, config: Config):
        self.config = config

    def get_repo_https_url(self):
        """
        Get the HTTPS URL for the repository with authentication token if available.

        Returns:
            str: The HTTPS URL for the repository, including authentication token if available.
        """
        # Try new URL-based config first
        url = self.config.get_repo_url()
        if not url:
            # Fallback to old repository_path pattern for backward compatibility (DEPRECATED)
            repo_path = self.config.get_github_repository_path()
            if repo_path:
                url = f"https://github.com/{repo_path}.git"
            else:
                return None

        # Normalize URL
        url = self._normalize_url(url)

        # Apply authentication
        provider = self._detect_provider_from_url(url)
        token = self._get_token_for_provider(provider)
        username = self._get_username_for_provider(provider)
        if token:
            url = self._build_authenticated_url(url, provider, token, username)

        return url
    
    def get_repo_url(self):
        """
        Get the URL for the GitHub repository.

        Returns:
            str: The URL for the GitHub repository.
        """
        return self.get_repo_https_url()

    def _normalize_url(self, url):
        """
        Normalize git URL by adding .git suffix if missing.

        Examples:
            https://github.com/owner/repo -> https://github.com/owner/repo.git
            https://github.com/owner/repo.git -> https://github.com/owner/repo.git (unchanged)
        """
        if not url:
            return url

        if url.endswith('.git'):
            return url

        # Don't add .git if URL has query params or fragment
        if '?' in url or '#' in url:
            return url

        return f"{url}.git"

    def _detect_provider_from_url(self, url):
        """Detect git provider from URL domain."""
        from urllib.parse import urlparse

        if not url:
            return "github"

        parsed = urlparse(url)
        domain = parsed.netloc.split('@')[-1].lower()
        domain = domain.split(':')[0]  # Remove port

        if 'github' in domain:
            return 'github'
        elif 'gitlab' in domain:
            return 'gitlab'
        elif 'bitbucket' in domain:
            return 'bitbucket'
        else:
            return 'github'  # Default

    def _get_token_for_provider(self, provider, explicit_token=None):
        """
        Get authentication token for the specified provider.

        Args:
            provider: 'github', 'gitlab', or 'bitbucket'
            explicit_token: Explicitly provided token (highest priority)

        Returns:
            Token string or None
        """
        # Explicit token takes priority
        if explicit_token:
            return explicit_token

        # Fall back to config tokens
        provider_lower = provider.lower()
        if provider_lower == 'github':
            return self.config.get_github_token()
        elif provider_lower == 'gitlab':
            return self.config.get_gitlab_token()
        elif provider_lower == 'bitbucket':
            return self.config.get_bitbucket_token()
        else:
            return self.config.get_github_token()  # Default

    def _get_username_for_provider(self, provider, explicit_username=None):
        """
        Get username for the specified provider (mainly for Bitbucket).

        Args:
            provider: 'github', 'gitlab', or 'bitbucket'
            explicit_username: Explicitly provided username (highest priority)

        Returns:
            Username string or None
        """
        # Explicit username takes priority
        if explicit_username:
            return explicit_username

        # Bitbucket requires username
        if provider.lower() == 'bitbucket':
            return self.config.get_bitbucket_username()

        return None

    def _build_authenticated_url(self, url, provider, token, username=None):
        """Build authenticated URL with provider-specific format."""
        from urllib.parse import urlparse, urlunparse

        if not token:
            return url  # No auth for public repos

        parsed = urlparse(url)
        netloc = parsed.netloc.split('@')[-1]  # Remove existing auth

        provider_lower = provider.lower()

        # Bitbucket requires username:token format
        if provider_lower == 'bitbucket':
            if not username:
                raise ValueError("Bitbucket requires a username for authentication. "
                               "Provide via 'username' parameter or BITBUCKET_USERNAME env var.")
            auth_netloc = f"{username}:{token}@{netloc}"
        # GitHub and GitLab use oauth2:token format
        else:
            auth_netloc = f"oauth2:{token}@{netloc}"

        return urlunparse((
            'https',
            auth_netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))

    def _construct_url_from_parts(self, base_url, repo_path):
        """
        Construct full git URL from base URL and repo path.

        Args:
            base_url: "https://github.com" or "https://gitlab.company.com"
            repo_path: "owner/repo" or "owner/subowner/repo"

        Returns:
            Full URL like "https://github.com/owner/repo.git"
        """
        base = base_url.rstrip('/')
        path = repo_path.lstrip('/')
        url = f"{base}/{path}"
        return self._normalize_url(url)

    def set_repo_path(self, repo_path):
        """
        DEPRECATED: Use set_repo_url() instead. This method will be removed in a future version.

        Set the GitHub repository path.

        Args:
            repo_path (str): The GitHub repository path in the format 'owner/repo'.
        """
        self.config.set_github_repository_path(repo_path)

    def set_token(self, token):
        """
        Set the GitHub authentication token.
        
        Args:
            token (str): The GitHub authentication token.
        """
        self.config.set_github_token(token)
        
    def configure(self):
        """
        Configure Git with default user information.
        
        Sets the local Git user email to 'bot@blocksorg.com' and user name to 'BlocksOrg'.
        """
        bash(f"git config --local user.email 'bot@blocksorg.com'")
        bash(f"git config --local user.name 'BlocksOrg'")

    def checkout(self, ref="", new_branch=False, track=False, orphan=False, force=False):
        """
        Checkout a branch, tag, or commit.
        
        Args:
            ref (str): The branch, tag, or commit to checkout. Default is "" (current branch).
            new_branch (bool): Whether to create a new branch. Default is False.
            track (bool): Whether to set up tracking for a new branch. Default is False.
            orphan (bool): Whether to create an orphan branch. Default is False.
            force (bool): Whether to force checkout. Default is False.
            
        Returns:
            int: The exit code of the git checkout command.
            
        Raises:
            subprocess.CalledProcessError: If the git checkout command fails.
        """
        options = []
        
        if new_branch:
            options.append("-b")
        elif orphan:
            options.append("--orphan")
            
        if track:
            options.append("--track")
            
        if force:
            options.append("--force")
            
        options_str = " ".join(options)
        return bash(f"git checkout {options_str} {ref}")

    def clone(self, url=None, provider=None, base_url=None, repo_path=None,
              token=None, username=None, ref="", target_dir=".", depth=None,
              single_branch=False, recursive=False, shallow_submodules=False):
        """
        Clone a repository with support for GitHub, GitLab, and Bitbucket.

        Supports two patterns:
        1. Full URL: clone(url="https://github.com/owner/repo")
        2. Base + Path: clone(base_url="https://github.com", repo_path="owner/repo")

        Args:
            url (str): Full repository URL (with or without .git suffix).
            provider (str): Git provider ('github', 'gitlab', 'bitbucket').
                           If None, auto-detects from URL/base_url domain.
            base_url (str): Base URL like "https://github.com" or "https://gitlab.company.com".
                           Alternative to 'url'. Requires 'repo_path'.
            repo_path (str): Repository path like "owner/repo" or "owner/subowner/repo".
                            Used with 'base_url'. Supports nested paths.
            token (str): Authentication token (PAT/OAuth/App Password). Takes priority over config/env.
                        Useful for handling expired tokens at runtime.
            username (str): Username for authentication. Required for Bitbucket.
                           Takes priority over config/env BITBUCKET_USERNAME.
            ref (str): Branch, tag, or commit to clone. Default is "" (default branch).
            target_dir (str): Directory to clone into. Default is "." (current directory).
            depth (int): Shallow clone with history truncated to specified commits.
            single_branch (bool): Clone only history leading to tip of single branch.
            recursive (bool): Initialize all submodules within cloned repository.
            shallow_submodules (bool): All submodules shallow with depth=1.

        Returns:
            int: Exit code of the git clone command.

        Raises:
            ValueError: If target directory exists and is not empty, no URL specified,
                       or Bitbucket authentication missing username.
            subprocess.CalledProcessError: If git clone command fails.

        Examples:
            # GitHub
            git.clone(url="https://github.com/owner/repo", token="ghp_xxx")

            # GitLab (enterprise)
            git.clone(base_url="https://gitlab.company.com",
                      repo_path="team/project",
                      provider="gitlab",
                      token="glpat-xxx")

            # Bitbucket
            git.clone(url="https://bitbucket.org/owner/repo",
                      token="app_password_here",
                      username="bitbucket_username")

            # Auto-detection
            git.clone(url="https://gitlab.com/owner/repo", token="glpat-xxx")  # Detects GitLab
        """
        # Determine final URL
        if url:
            # Pattern 1: Full URL provided
            final_url = self._normalize_url(url)
        elif base_url and repo_path:
            # Pattern 2: Construct from base + path
            final_url = self._construct_url_from_parts(base_url, repo_path)
        else:
            # Pattern 3: Fallback to config (DEPRECATED but backward compatible)
            final_url = self.get_repo_url()
            if not final_url:
                raise ValueError("No URL provided: specify 'url' or 'base_url'+'repo_path'")

        # Determine provider
        if not provider:
            if url or base_url:
                # Detect from provided URL/base_url
                provider = self._detect_provider_from_url(url or base_url)
            else:
                # Use config provider or detect from config URL
                provider = self.config.get_repo_provider()
                if not provider:
                    provider = self._detect_provider_from_url(final_url)

        # Apply authentication
        token_to_use = self._get_token_for_provider(provider, explicit_token=token)
        username_to_use = self._get_username_for_provider(provider, explicit_username=username)
        if token_to_use:
            final_url = self._build_authenticated_url(final_url, provider, token_to_use, username_to_use)

        # Continue with existing validation and clone logic
        target_path = Path(target_dir)

        if target_path.exists() and any(target_path.iterdir()):
            raise ValueError(f"Target directory '{target_dir}' already exists and is not empty. Cannot clone into a non-empty directory.")
        elif not target_path.parent.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)

        # Build git clone command options
        options = []
        if ref:
            options.append(f"--branch {ref}")
        if depth is not None:
            options.append(f"--depth {depth}")
        if single_branch:
            options.append("--single-branch")
        if recursive:
            options.append("--recursive")
        if shallow_submodules:
            options.append("--shallow-submodules")

        options_str = " ".join(options)
        return_value = bash(f"git clone {options_str} {final_url} {target_dir}")
        current_dir = os.getcwd()
        os.chdir(target_path.absolute())
        with contextlib.suppress(Exception):
            self.configure()
        os.chdir(current_dir)
        return return_value

    def init(self):
        """
        Initialize a new Git repository in the current directory.
        
        Equivalent to running 'git init'.
        """
        bash("git init")

    def pull(self, remote="origin", branch="HEAD", rebase=False, ff_only=False):
        """
        Pull changes from a remote repository.
        
        Args:
            remote (str): The remote to pull from. Default is "origin".
            branch (str): The branch to pull from. Default is "HEAD".
            rebase (bool): Whether to rebase instead of merge. Default is False.
            ff_only (bool): Whether to only allow fast-forward merges. Default is False.
            
        Returns:
            int: The exit code of the git pull command.
            
        Raises:
            subprocess.CalledProcessError: If the git pull command fails.
        """
        options = []
        if rebase:
            options.append("--rebase")
        if ff_only:
            options.append("--ff-only")
        
        options_str = " ".join(options)
        return bash(f"git pull {options_str} {remote} {branch}")
        
    def push(self, remote="origin", branch="HEAD", publish=False, force=False, force_with_lease=False, tags=False):
        """
        Push changes to a remote repository.
        
        Args:
            remote (str): The remote to push to. Default is "origin".
            branch (str): The branch to push. Default is "HEAD".
            publish (bool): Whether to set up tracking with -u. Default is False.
            force (bool): Whether to force push. Default is False.
            force_with_lease (bool): Whether to force push with lease. Default is False.
            tags (bool): Whether to push tags. Default is False.
            
        Returns:
            int: The exit code of the git push command.
            
        Raises:
            subprocess.CalledProcessError: If the git push command fails.
        """
        options = []
        
        if publish:
            options.append("-u")
        if force:
            options.append("--force")
        elif force_with_lease:
            options.append("--force-with-lease")
        if tags:
            options.append("--tags")
        
        options_str = " ".join(options)
        return bash(f"git push {options_str} {remote} {branch}")

    def commit(self, message, amend=False, no_edit=False, all=False, allow_empty=False, signoff=False):
        """
        Commit changes to the repository.
        
        Args:
            message (str): The commit message.
            amend (bool): Whether to amend the previous commit. Default is False.
            no_edit (bool): When amending, whether to reuse the previous commit message. Default is False.
            all (bool): Whether to automatically stage all modified and deleted files. Default is False.
            allow_empty (bool): Whether to allow creating empty commits. Default is False.
            signoff (bool): Whether to add a Signed-off-by line to the commit message. Default is False.
            
        Returns:
            int: The exit code of the git commit command.
            
        Raises:
            subprocess.CalledProcessError: If the git commit command fails.
        """
        options = []
        
        if message and not (amend and no_edit):
            # Escape single quotes in the message
            escaped_message = message.replace("'", "'\\''")
            options.append(f"-m '{escaped_message}'")
        
        if amend:
            options.append("--amend")
            
        if no_edit:
            options.append("--no-edit")
            
        if all:
            options.append("--all")
            
        if allow_empty:
            options.append("--allow-empty")
            
        if signoff:
            options.append("--signoff")
        
        options_str = " ".join(options)
        return bash(f"git commit {options_str}")

    def add(self, file=None, all=False):
        """
        Add file contents to the index.
        
        Args:
            file (str): The file to add. Ignored if all=True.
            all (bool): Whether to add all files (including untracked). Default is False.
            
        Raises:
            subprocess.CalledProcessError: If the git add command fails.
        """
        if all:
            bash("git add .")
        elif file:
            bash(f"git add {file}")
        else:
            raise ValueError("Either 'file' or 'all' keyword argument must be provided")

    def branch(self, branch_name, checkout=False):
        """
        Create a new branch.
        
        Args:
            branch_name (str): The name of the branch to create.
            checkout (bool): Whether to checkout the new branch after creating it. Default is False.
            
        Raises:
            subprocess.CalledProcessError: If the git branch command fails.
        """
        if checkout:
            self.checkout(branch_name, new_branch=True)
        else:
            bash(f"git branch {branch_name}")
