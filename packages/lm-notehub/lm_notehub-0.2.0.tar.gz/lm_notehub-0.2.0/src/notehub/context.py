"""Store context resolution - determine host/org/repo from flags, config, and environment."""

from argparse import Namespace
from typing import Optional
import os
import subprocess


class StoreContext:
    """Resolved store context (host/org/repo)."""
    
    def __init__(self, host: str, org: str, repo: str):
        """
        Initialize store context.
        
        Args:
            host: GitHub host (e.g., 'github.com' or GHES hostname)
            org: Organization/owner name
            repo: Repository name
        """
        self.host = host
        self.org = org
        self.repo = repo
    
    @classmethod
    def resolve(cls, args: Namespace) -> 'StoreContext':
        """
        Resolve context from args, config, env, defaults.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            StoreContext: Resolved context
        """
        global_only = getattr(args, 'global_scope', False)
        
        # Resolve host
        host = cls._resolve_host(args, global_only)
        
        # Resolve org
        org = cls._resolve_org(args, global_only)
        
        # Resolve repo
        repo = cls._resolve_repo(args, global_only)
        
        return cls(host, org, repo)
    
    @classmethod
    def _resolve_host(cls, args: Namespace, global_only: bool) -> str:
        """Resolve host from args, git remote, config, or default."""
        # 1. --host flag
        if hasattr(args, 'host') and args.host:
            return args.host
        
        # 2. GH_HOST environment variable
        env_host = os.environ.get('GH_HOST')
        if env_host:
            return env_host
        
        # 3. Auto-detect from git remote (unless --global)
        if not global_only:
            remote_host = cls._get_git_remote_host()
            if remote_host:
                return remote_host
        
        # 4. git config --global notehub.host
        git_host = cls._get_git_config('notehub.host', global_only=True)
        if git_host:
            return git_host
        
        # 5. Default to github.com
        return 'github.com'
    
    @classmethod
    def _resolve_org(cls, args: Namespace, global_only: bool) -> str:
        """Resolve org from args, git remote, env, config, or $USER."""
        # 1. --org flag
        if hasattr(args, 'org') and args.org:
            return args.org
        
        # 2. Auto-detect from git remote (unless --global)
        if not global_only:
            remote_org = cls._get_git_remote_org()
            if remote_org:
                return remote_org
        
        # 3. Environment variable NotehubOrg
        env_org = os.environ.get('NotehubOrg')
        if env_org:
            return env_org
        
        # 4. git config --global notehub.org
        git_org = cls._get_git_config('notehub.org', global_only=True)
        if git_org:
            return git_org
        
        # 5. Default to $USER
        return os.environ.get('USER', 'unknown-user')
    
    @classmethod
    def _resolve_repo(cls, args: Namespace, global_only: bool) -> str:
        """Resolve repo from args, config, env, or default."""
        # 1. --repo flag (special handling for '.' = auto-detect)
        if hasattr(args, 'repo') and args.repo:
            if args.repo == '.':
                # Try to auto-detect from git remote
                remote_repo = cls._get_git_remote_repo()
                if remote_repo:
                    return remote_repo
                # If auto-detect fails, fall through to other methods
            else:
                # Explicit repo name provided
                return args.repo
        
        # 2. Auto-detect from git remote (unless --global)
        if not global_only:
            remote_repo = cls._get_git_remote_repo()
            if remote_repo:
                return remote_repo
        
        # 3. Environment variable NotehubRepo
        env_repo = os.environ.get('NotehubRepo')
        if env_repo:
            return env_repo
        
        # 4. git config notehub.repo (local unless --global)
        if not global_only:
            local_repo = cls._get_git_config('notehub.repo', global_only=False)
            if local_repo:
                return local_repo
        
        # 5. git config --global notehub.repo
        global_repo = cls._get_git_config('notehub.repo', global_only=True)
        if global_repo:
            return global_repo
        
        # 6. Default to 'notehub.default'
        return 'notehub.default'
    
    @staticmethod
    def _get_git_config(key: str, global_only: bool = False) -> Optional[str]:
        """
        Get git config value.
        
        Args:
            key: Config key (e.g., 'notehub.host')
            global_only: If True, only check global config
            
        Returns:
            Config value or None if not set
        """
        cmd = ['git', 'config']
        if global_only:
            cmd.append('--global')
        cmd.append(key)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            # git not installed
            pass
        
        return None
    
    @staticmethod
    def _expand_ssh_host(alias: str) -> Optional[str]:
        """
        Resolve SSH host alias to actual hostname using SSH config.
        
        Args:
            alias: SSH host alias (e.g., 'bbgithub')
            
        Returns:
            Actual hostname or None if not resolvable
        """
        try:
            result = subprocess.run(
                ['ssh', '-G', alias],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                # Parse output for "hostname" line
                for line in result.stdout.split('\n'):
                    if line.startswith('hostname '):
                        return line.split(maxsplit=1)[1]
        except FileNotFoundError:
            pass
        
        return None
    
    @staticmethod
    def _expand_git_url(url: str) -> str:
        """
        Expand git URL using insteadOf rules and SSH config.
        
        Args:
            url: Raw URL from git remote (may contain alias)
            
        Returns:
            Expanded URL with full hostname
        """
        # First try git config insteadOf rules
        try:
            result = subprocess.run(
                ['git', 'config', '--get-regexp', r'^url\..*\.insteadof$'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        config_key = parts[0]
                        alias = parts[1]
                        
                        if config_key.startswith('url.') and config_key.endswith('.insteadof'):
                            base_url = config_key[4:-10]
                            
                            if url.startswith(alias):
                                return url.replace(alias, base_url, 1)
        except FileNotFoundError:
            pass
        
        # If URL uses SSH short form (alias:org/repo), resolve via SSH config
        if ':' in url and '@' not in url and not url.startswith('https://'):
            # Short form: bbgithub:org/repo
            alias = url.split(':', 1)[0]
            path = url.split(':', 1)[1]
            
            # Try to resolve alias via SSH config
            actual_host = StoreContext._expand_ssh_host(alias)
            if actual_host:
                # Reconstruct as git@actualhost:org/repo
                return f"git@{actual_host}:{path}"
        
        return url
    
    @staticmethod
    def _get_git_remote_host() -> Optional[str]:
        """
        Extract host from git remote origin URL.
        
        Returns:
            Host (e.g., 'github.com') or None if not detectable
        """
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Expand URL using insteadOf rules
                url = StoreContext._expand_git_url(url)
                
                # Parse URL - handle both HTTPS and SSH formats
                # HTTPS: https://github.com/org/repo.git
                # SSH: git@github.com:org/repo.git
                if url.startswith('https://'):
                    # Extract host from https://host/...
                    parts = url.split('//')
                    if len(parts) > 1:
                        host_part = parts[1].split('/')[0]
                        return host_part
                elif '@' in url:
                    # Extract host from git@host:...
                    host_part = url.split('@')[1].split(':')[0]
                    return host_part
        except FileNotFoundError:
            pass
        
        return None
    
    @staticmethod
    def _get_git_remote_org() -> Optional[str]:
        """
        Extract org from git remote origin URL.
        
        Returns:
            Organization name or None if not detectable
        """
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Expand URL using insteadOf rules
                url = StoreContext._expand_git_url(url)
                
                # Parse URL
                # HTTPS: https://github.com/org/repo.git -> org
                # SSH: git@github.com:org/repo.git -> org
                # SCP-like: bbgithub:org/repo.git -> org
                if url.startswith('https://'):
                    parts = url.split('//')
                    if len(parts) > 1:
                        path_parts = parts[1].split('/')[1:]  # Skip host
                        if path_parts:
                            return path_parts[0]
                elif ':' in url:
                    # Handle both SSH (git@host:org/repo) and SCP-like (host:org/repo)
                    if '@' in url:
                        # SSH format: git@github.com:org/repo.git
                        path = url.split(':')[1]
                    else:
                        # SCP-like format: bbgithub:org/repo.git
                        path = url.split(':', 1)[1]
                    
                    org = path.split('/')[0]
                    return org
        except FileNotFoundError:
            pass
        
        return None
    
    @staticmethod
    def _get_git_remote_repo() -> Optional[str]:
        """
        Extract repo name from git remote origin URL.
        
        Returns:
            Repository name or None if not detectable
        """
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Expand URL using insteadOf rules
                url = StoreContext._expand_git_url(url)
                
                # Parse URL - handle both HTTPS and SSH formats
                # HTTPS: https://github.com/org/repo.git -> repo
                # SSH: git@github.com:org/repo.git -> repo
                # SCP-like: bbgithub:org/repo.git -> repo
                if url.startswith('https://'):
                    parts = url.split('//')
                    if len(parts) > 1:
                        path_parts = parts[1].split('/')[2:]  # Skip host and org
                        if path_parts:
                            repo = path_parts[0].removesuffix('.git')
                            return repo
                elif ':' in url:
                    # Handle both SSH (git@host:org/repo) and SCP-like (host:org/repo)
                    if '@' in url:
                        # SSH format: git@github.com:org/repo.git
                        path = url.split(':')[1]
                    else:
                        # SCP-like format: bbgithub:org/repo.git
                        path = url.split(':', 1)[1]
                    
                    # Extract repo from org/repo.git
                    if '/' in path:
                        repo = path.split('/')[1].removesuffix('.git')
                        return repo
        except FileNotFoundError:
            pass
        
        return None
    
    def repo_identifier(self) -> str:
        """
        Return 'org/repo' string.
        
        Returns:
            str: Organization and repository name
        """
        return f"{self.org}/{self.repo}"
    
    def full_identifier(self) -> str:
        """
        Return 'host:org/repo' string (or just 'org/repo' for github.com).
        
        Returns:
            str: Full identifier with host
        """
        if self.host == "github.com":
            return self.repo_identifier()
        return f"{self.host}:{self.repo_identifier()}"
    
    def build_issue_url(self, issue_number: int) -> str:
        """
        Build full GitHub issue URL.
        
        Args:
            issue_number: Issue number
            
        Returns:
            str: Full URL like https://github.com/org/repo/issues/123
        """
        return f"https://{self.host}/{self.org}/{self.repo}/issues/{issue_number}"

