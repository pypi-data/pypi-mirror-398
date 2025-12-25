"""Share commands - Manage session sharing and collaboration."""

import os
import webbrowser
import getpass
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from ..tracker.git_tracker import ReAlignGitTracker
from ..logging_config import setup_logger

logger = setup_logger('realign.commands.share', 'share.log')


def share_configure_command(
    remote: str,
    token: Optional[str] = None,
    repo_root: Optional[Path] = None
) -> int:
    """
    Manually configure remote repository for sharing.

    Args:
        remote: Remote repository (e.g., user/repo or full URL)
        token: GitHub access token (optional)
        repo_root: Path to repository root (uses cwd if not provided)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Get project root
    if repo_root is None:
        repo_root = Path(os.getcwd()).resolve()

    # Initialize tracker
    tracker = ReAlignGitTracker(repo_root)

    # Check if repository is initialized
    if not tracker.is_initialized():
        print("❌ Repository not initialized")
        print("Run 'aline init' first")
        return 1

    # Parse remote URL
    remote_url = _parse_remote_url(remote)

    if not remote_url:
        print("❌ Invalid remote format")
        print("\nExpected formats:")
        print("  user/repo")
        print("  https://github.com/user/repo.git")
        return 1

    # Store token in git credentials if provided
    if token:
        _store_git_credentials(remote_url, token)

    # Configure remote
    print(f"Configuring remote: {remote_url}")

    success = tracker.setup_remote(remote_url)

    if not success:
        print("❌ Failed to configure remote")
        return 1

    print("✓ Remote configured successfully")

    # Try initial push
    print("\nAttempting initial push...")

    push_success = tracker.safe_push()

    if push_success:
        print("✓ Successfully pushed to remote")
    else:
        print("⚠️  Initial push failed")
        print("\nPossible issues:")
        print("  - Repository doesn't exist (create it on GitHub first)")
        print("  - No access permissions (check GitHub access token)")
        print("  - Network issues")
        print("\nYou can try pushing later with: aline push")

    print(f"\nRemote: {remote_url}")

    # Update config
    _update_sharing_config(repo_root, remote_url, enabled=True)

    print("\nNext steps:")
    print("  - Push sessions: aline push")
    print("  - Invite teammates: aline share invite <email>")

    return 0


def share_status_command(repo_root: Optional[Path] = None) -> int:
    """
    Show current sharing configuration.

    Args:
        repo_root: Path to repository root (uses cwd if not provided)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Get project root
    if repo_root is None:
        repo_root = Path(os.getcwd()).resolve()

    # Initialize tracker
    tracker = ReAlignGitTracker(repo_root)

    if not tracker.is_initialized():
        print("Repository not initialized")
        return 1

    # Check if remote is configured
    remote_url = tracker.get_remote_url()

    if not remote_url:
        print("Sharing: Disabled")
        print("\nTo enable sharing:")
        print("  aline init --share          (browser-based setup)")
        print("  aline share configure       (manual configuration)")
        return 0

    print("Sharing: Enabled ✓")
    print(f"Remote: {remote_url}")

    # Get unpushed commits
    unpushed = tracker.get_unpushed_commits()
    print(f"Unpushed commits: {len(unpushed)}")

    # Load config to show additional details
    config = tracker.config.get('sharing', {})

    if config.get('owner'):
        print(f"Owner: {config['owner']}")

    if config.get('created_at'):
        print(f"Created: {config['created_at']}")

    return 0


def share_invite_command(
    email: Optional[str] = None,
    repo_root: Optional[Path] = None
) -> int:
    """
    Invite collaborator to shared repository.

    Opens GitHub collaboration settings page in browser.

    Args:
        email: Email address to invite (optional, for display only)
        repo_root: Path to repository root (uses cwd if not provided)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Get project root
    if repo_root is None:
        repo_root = Path(os.getcwd()).resolve()

    # Initialize tracker
    tracker = ReAlignGitTracker(repo_root)

    if not tracker.has_remote():
        print("❌ No remote configured")
        print("Run 'aline share configure' first")
        return 1

    # Get remote URL
    remote_url = tracker.get_remote_url()

    # Parse GitHub repo from URL
    repo_path = _extract_github_repo(remote_url)

    if not repo_path:
        print("❌ Not a GitHub repository")
        print(f"Remote: {remote_url}")
        return 1

    # Construct GitHub collaborators URL
    github_url = f"https://github.com/{repo_path}/settings/access"

    print("Opening GitHub collaboration page...")
    print(f"Repository: {repo_path}")

    if email:
        print(f"Inviting: {email}")

    # Open browser
    webbrowser.open(github_url)

    print("\nOnce invited, they can join with:")
    print(f"  aline init --join {repo_path}")

    return 0


def share_link_command(repo_root: Optional[Path] = None) -> int:
    """
    Get shareable link for teammates to join.

    Args:
        repo_root: Path to repository root (uses cwd if not provided)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Get project root
    if repo_root is None:
        repo_root = Path(os.getcwd()).resolve()

    # Initialize tracker
    tracker = ReAlignGitTracker(repo_root)

    if not tracker.has_remote():
        print("❌ No remote configured")
        print("Run 'aline share configure' first")
        return 1

    # Get remote URL
    remote_url = tracker.get_remote_url()

    # Parse GitHub repo from URL
    repo_path = _extract_github_repo(remote_url)

    if not repo_path:
        print(f"Remote URL: {remote_url}")
        print("\nShare this URL with teammates")
        return 0

    print("Share with teammates:")
    print()
    print(f"Repository: https://github.com/{repo_path}")
    print()
    print("Join command:")
    print(f"  aline init --join {repo_path}")

    return 0


def share_disable_command(repo_root: Optional[Path] = None) -> int:
    """
    Disable sharing (keeps history intact).

    Args:
        repo_root: Path to repository root (uses cwd if not provided)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Get project root
    if repo_root is None:
        repo_root = Path(os.getcwd()).resolve()

    # Initialize tracker
    tracker = ReAlignGitTracker(repo_root)

    if not tracker.has_remote():
        print("Sharing is already disabled")
        return 0

    remote_url = tracker.get_remote_url()

    confirm = input(f"Remove remote: {remote_url}? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        return 0

    # Remove remote
    try:
        tracker._run_git(
            ["remote", "remove", "origin"],
            cwd=tracker.realign_dir,
            check=True
        )

        print("✓ Remote removed")
        print("Local history preserved")

        # Update config
        _update_sharing_config(repo_root, None, enabled=False)

        return 0

    except Exception as e:
        logger.error(f"Failed to remove remote: {e}")
        print("❌ Failed to remove remote")
        return 1


# Helper functions

def _parse_remote_url(remote: str) -> Optional[str]:
    """
    Parse remote URL from various formats.

    Supports:
    - user/repo -> https://github.com/user/repo.git
    - https://github.com/user/repo.git (unchanged)
    - git@github.com:user/repo.git (unchanged)
    """
    remote = remote.strip()

    # Already a full URL
    if remote.startswith('http://') or remote.startswith('https://') or remote.startswith('git@'):
        return remote

    # Short format: user/repo
    if '/' in remote and not remote.startswith('/'):
        parts = remote.split('/')
        if len(parts) == 2:
            user, repo = parts
            # Remove .git suffix if present
            repo = repo.replace('.git', '')
            return f"https://github.com/{user}/{repo}.git"

    return None


def _extract_github_repo(url: str) -> Optional[str]:
    """
    Extract GitHub repo path (user/repo) from URL.

    Examples:
        https://github.com/alice/myproject.git -> alice/myproject
        git@github.com:alice/myproject.git -> alice/myproject
    """
    url = url.strip()

    # HTTPS URL
    if 'github.com/' in url:
        parts = url.split('github.com/')
        if len(parts) == 2:
            repo_path = parts[1]
            # Remove .git suffix
            repo_path = repo_path.replace('.git', '')
            return repo_path

    # SSH URL
    if 'github.com:' in url:
        parts = url.split('github.com:')
        if len(parts) == 2:
            repo_path = parts[1]
            # Remove .git suffix
            repo_path = repo_path.replace('.git', '')
            return repo_path

    return None


def _get_github_username(token: str) -> Optional[str]:
    """
    Get GitHub username from a personal access token using GitHub API.

    Args:
        token: GitHub personal access token

    Returns:
        GitHub username or None if failed
    """
    try:
        import urllib.request
        import json

        req = urllib.request.Request(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            username = data.get("login")
            if username:
                logger.info(f"Retrieved GitHub username: {username}")
                return username
    except Exception as e:
        logger.warning(f"Failed to get GitHub username: {e}")
        return None


def _store_git_credentials(url: str, token: str):
    """
    Store GitHub token in git credential helper.

    This allows git to authenticate without prompting.
    """
    try:
        import subprocess

        # Configure credential helper
        subprocess.run(
            ["git", "config", "--global", "credential.helper", "store"],
            check=False
        )

        # Extract hostname from URL
        if 'github.com' in url:
            hostname = 'github.com'
        else:
            # Extract from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.hostname or 'github.com'

        # Store credentials
        # Format: https://<token>@github.com
        cred_url = f"https://{token}@{hostname}"

        # Write to credential store
        cred_file = Path.home() / '.git-credentials'

        # Read existing credentials
        existing_creds = []
        if cred_file.exists():
            existing_creds = cred_file.read_text().strip().split('\n')

        # Remove existing credentials for this host
        existing_creds = [c for c in existing_creds if hostname not in c]

        # Add new credentials
        existing_creds.append(cred_url)

        # Write back
        cred_file.write_text('\n'.join(existing_creds) + '\n')
        cred_file.chmod(0o600)  # Secure permissions

        logger.info("Stored git credentials")

    except Exception as e:
        logger.warning(f"Failed to store credentials: {e}")
        # Non-fatal - user can authenticate manually


def _update_sharing_config(project_root: Path, remote_url: Optional[str], enabled: bool, member_name: Optional[str] = None):
    """
    Update config.yaml with sharing configuration.

    Args:
        project_root: Path to project root
        remote_url: GitHub remote URL
        enabled: Whether sharing is enabled
        member_name: GitHub username of the member (for joined repositories)
    """
    from realign import get_realign_dir
    realign_dir = get_realign_dir(project_root)
    config_path = realign_dir / "config.yaml"

    # Load existing config
    config = {}
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

    # Update sharing section
    if 'sharing' not in config:
        config['sharing'] = {}

    config['sharing']['enabled'] = enabled

    if remote_url:
        config['sharing']['remote_url'] = remote_url

        # Extract owner from URL
        repo_path = _extract_github_repo(remote_url)
        if repo_path:
            owner = repo_path.split('/')[0]
            config['sharing']['owner'] = owner

        # Set created_at if not already set
        if 'created_at' not in config['sharing']:
            config['sharing']['created_at'] = datetime.now().isoformat()

    # Store member name if provided (for joined repositories)
    if member_name:
        config['sharing']['member_name'] = member_name
        config['sharing']['member_branch'] = f"{member_name}/master"

    # Save config
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated sharing config: enabled={enabled}, member={member_name}")


def init_share_flow(repo_root: Optional[Path] = None) -> int:
    """
    Interactive flow for setting up a new shared repository.

    This is called by `aline init --share`.

    Args:
        repo_root: Path to repository root (uses cwd if not provided)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Get project root
    if repo_root is None:
        repo_root = Path(os.getcwd()).resolve()

    print("╭─────────────────────────────────────────╮")
    print("│  ReAlign Sharing Setup                  │")
    print("╰─────────────────────────────────────────╯")
    print()

    # Initialize ReAlign if not already done
    from .init import init_repository
    tracker = ReAlignGitTracker(repo_root)

    if not tracker.is_initialized():
        print("Initializing ReAlign...")
        result = init_repository(repo_path=str(repo_root))
        if not result["success"]:
            print("❌ Failed to initialize ReAlign")
            return 1
        print("✓ ReAlign initialized")
        print()

    # Check if remote already configured
    if tracker.has_remote():
        remote_url = tracker.get_remote_url()
        print(f"⚠️  Remote already configured: {remote_url}")
        print()
        confirm = input("Reconfigure? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Cancelled")
            return 0
        print()

    # Step 1: Get repository name
    print("[1/3] Repository Setup")
    print("─────────────────────")
    print()
    print("Choose a repository name for your team's sessions.")
    print("This will be created as a private repository on GitHub.")
    print()

    # Suggest default name
    suggested_name = repo_root.name + "-realign-sessions"
    repo_name = input(f"Repository name [{suggested_name}]: ").strip()
    if not repo_name:
        repo_name = suggested_name

    print()

    # Step 2: Get GitHub username
    print("[2/3] GitHub Account")
    print("────────────────────")
    print()
    github_user = input("GitHub username: ").strip()

    if not github_user:
        print("❌ GitHub username required")
        return 1

    print()

    # Step 3: Get GitHub token
    print("[3/3] Authentication")
    print("────────────────────")
    print()
    print("Create a GitHub Personal Access Token:")
    print("  1. Go to: https://github.com/settings/tokens/new")
    print("  2. Name: 'ReAlign Sharing'")
    print("  3. Scopes: Select 'repo' (full control of private repositories)")
    print("  4. Generate token and paste below")
    print()

    # Open browser to token creation page
    open_browser = input("Open token creation page in browser? [Y/n]: ").strip().lower()
    if open_browser != 'n':
        token_url = "https://github.com/settings/tokens/new?description=ReAlign%20Sharing&scopes=repo"
        webbrowser.open(token_url)
        print("✓ Opened in browser")
        print()

    # Get token securely
    token = getpass.getpass("GitHub Personal Access Token: ").strip()

    if not token:
        print("❌ Token required")
        return 1

    print()
    print("Setting up repository...")
    print()

    # Construct repository path and URL
    repo_path = f"{github_user}/{repo_name}"
    remote_url = f"https://github.com/{repo_path}.git"

    # Create repository using GitHub API
    try:
        import subprocess
        import json

        # Use gh CLI if available, otherwise use GitHub API directly
        gh_available = False
        try:
            gh_check = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=False
            )
            gh_available = (gh_check.returncode == 0)
        except FileNotFoundError:
            gh_available = False

        if gh_available:
            # Use gh CLI
            print("Creating repository using GitHub CLI...")
            result = subprocess.run(
                [
                    "gh", "repo", "create", repo_path,
                    "--private",
                    "--description", "ReAlign AI session history"
                ],
                env={**os.environ, "GH_TOKEN": token},
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                # Repository might already exist
                if "already exists" in result.stderr.lower():
                    print(f"Repository {repo_path} already exists, using it...")
                else:
                    print(f"❌ Failed to create repository: {result.stderr}")
                    return 1
            else:
                print(f"✓ Created private repository: {repo_path}")

        else:
            # Use GitHub API directly
            print("Creating repository using GitHub API...")
            import urllib.request

            api_url = "https://api.github.com/user/repos"
            data = json.dumps({
                "name": repo_name,
                "private": True,
                "description": "ReAlign AI session history",
                "auto_init": False
            }).encode('utf-8')

            req = urllib.request.Request(
                api_url,
                data=data,
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "Content-Type": "application/json"
                },
                method="POST"
            )

            try:
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    print(f"✓ Created private repository: {repo_path}")
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                if "already exists" in error_body.lower():
                    print(f"Repository {repo_path} already exists, using it...")
                else:
                    print(f"❌ Failed to create repository: {error_body}")
                    return 1

    except Exception as e:
        logger.error(f"Failed to create repository: {e}")
        print(f"❌ Failed to create repository: {e}")
        print()
        print("You can create the repository manually:")
        print(f"  1. Go to: https://github.com/new")
        print(f"  2. Name: {repo_name}")
        print(f"  3. Privacy: Private")
        print(f"  4. Then run: aline share configure {repo_path} --token <your-token>")
        return 1

    # Configure remote
    print()
    print("Configuring remote...")

    if not tracker.setup_remote(remote_url):
        print("❌ Failed to configure remote")
        return 1

    # Store credentials
    _store_git_credentials(remote_url, token)

    print("✓ Remote configured")
    print()

    # Update config
    _update_sharing_config(repo_root, remote_url, enabled=True)

    # Push initial commits
    print("Pushing initial commits...")
    push_success = tracker.safe_push()

    if push_success:
        print("✓ Initial push successful")
    else:
        print("⚠️  Initial push failed (you can try 'aline push' later)")

    # Show success message
    print()
    print("╭─────────────────────────────────────────╮")
    print("│  ✓ Setup Complete!                      │")
    print("╰─────────────────────────────────────────╯")
    print()
    print(f"Repository: https://github.com/{repo_path}")
    print()
    print("Next steps:")
    print("  • Push sessions: aline push")
    print("  • Pull updates: aline pull")
    print("  • Sync: aline sync")
    print()
    print("Share with teammates:")
    print(f"  aline init --join {repo_path}")
    print()

    return 0


def init_join_flow(repo: str, repo_root: Optional[Path] = None) -> int:
    """
    Interactive flow for joining an existing shared repository.

    This is called by `aline init --join <repo>`.

    Args:
        repo: Repository in format 'user/repo'
        repo_root: Path to repository root (uses cwd if not provided)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Get project root
    if repo_root is None:
        repo_root = Path(os.getcwd()).resolve()

    print("╭─────────────────────────────────────────╮")
    print("│  Join ReAlign Shared Repository        │")
    print("╰─────────────────────────────────────────╯")
    print()

    # Parse repository
    remote_url = _parse_remote_url(repo)
    if not remote_url:
        print("❌ Invalid repository format")
        print()
        print("Expected format: user/repo")
        print(f"Example: aline init --join alice/team-sessions")
        return 1

    repo_path = _extract_github_repo(remote_url)
    print(f"Repository: https://github.com/{repo_path}")
    print()

    # Initialize ReAlign if not already done
    from .init import init_repository
    tracker = ReAlignGitTracker(repo_root)

    if not tracker.is_initialized():
        print("Initializing ReAlign...")
        result = init_repository(repo_path=str(repo_root), for_join=True)
        if not result["success"]:
            print("❌ Failed to initialize ReAlign")
            return 1
        print("✓ ReAlign initialized")
        print()

    # Check if remote already configured
    if tracker.has_remote():
        existing_remote = tracker.get_remote_url()
        print(f"⚠️  Remote already configured: {existing_remote}")
        print()
        confirm = input("Reconfigure? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Cancelled")
            return 0
        print()

    # Verify repository exists
    print("Verifying repository access...")
    import subprocess

    # Try to check if repo exists using git ls-remote
    check_result = subprocess.run(
        ["git", "ls-remote", remote_url],
        capture_output=True,
        text=True,
        check=False
    )

    if check_result.returncode != 0:
        # Repository might be private, need authentication
        print("Repository requires authentication")
        print()
    else:
        print("✓ Repository found")
        print()

    # Get GitHub token
    print("Authentication Required")
    print("──────────────────────")
    print()
    print("You need a GitHub Personal Access Token to access this repository.")
    print()
    print("If you don't have a token:")
    print("  1. Go to: https://github.com/settings/tokens/new")
    print("  2. Name: 'ReAlign Sharing'")
    print("  3. Scopes: Select 'repo' (full control of private repositories)")
    print("  4. Generate token and paste below")
    print()

    # Open browser to token creation page
    open_browser = input("Open token creation page in browser? [Y/n]: ").strip().lower()
    if open_browser != 'n':
        token_url = "https://github.com/settings/tokens/new?description=ReAlign%20Sharing&scopes=repo"
        webbrowser.open(token_url)
        print("✓ Opened in browser")
        print()

    # Get token securely
    token = getpass.getpass("GitHub Personal Access Token: ").strip()

    if not token:
        print("❌ Token required")
        return 1

    print()

    # Verify access with token
    print("Verifying access...")
    verify_result = subprocess.run(
        ["git", "ls-remote", remote_url],
        env={**os.environ, "GIT_ASKPASS": "echo", "GIT_USERNAME": "x-access-token", "GIT_PASSWORD": token},
        capture_output=True,
        text=True,
        check=False
    )

    if verify_result.returncode != 0:
        print("❌ Failed to access repository")
        print()
        print("Possible issues:")
        print("  • Invalid token")
        print("  • No access to repository")
        print("  • Repository doesn't exist")
        print()
        print("Ask the repository owner to invite you:")
        print(f"  GitHub Settings → {repo_path} → Manage Access → Invite")
        return 1

    print("✓ Access verified")
    print()

    # Get GitHub username from token
    print("Getting GitHub username...")
    github_username = _get_github_username(token)
    if not github_username:
        print("⚠️  Could not retrieve GitHub username, using current git user")
        # Fallback: try to get from git config
        import subprocess
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=False
        )
        github_username = result.stdout.strip() if result.returncode == 0 else None

        if not github_username:
            print("❌ Could not determine username for branch")
            return 1

    member_branch = f"{github_username}/master"
    print(f"✓ Member branch: {member_branch}")
    print()

    # Configure remote
    print("Configuring remote...")

    if not tracker.setup_remote(remote_url):
        print("❌ Failed to configure remote")
        return 1

    # Store credentials
    _store_git_credentials(remote_url, token)

    print("✓ Remote configured")
    print()

    # Pull existing sessions FIRST (before updating config)
    # This ensures we get the remote's config.yaml and .gitignore
    print("Pulling existing sessions from owner's master branch...")
    pull_success = tracker.safe_pull()

    if pull_success:
        print("✓ Pulled from owner's master branch")
        print()

        # Create member-specific branch based on owner's master
        print(f"Creating member branch: {member_branch}...")
        if not tracker.create_branch(member_branch, start_point="master"):
            print("❌ Failed to create member branch")
            return 1
        print(f"✓ Created and checked out branch: {member_branch}")
        print()
    else:
        print("⚠️  Failed to pull from owner's master (repository might be empty)")
        print("Creating member branch on empty repository...")
        if not tracker.create_branch(member_branch, start_point="master"):
            # If master doesn't exist, try creating a branch directly
            print("⚠️  Could not create from master, attempting to create as initial branch...")
            # This might happen on a completely empty repo
            pass
        print()

    # Update config AFTER pull
    # This way we preserve any existing config from remote
    _update_sharing_config(repo_root, remote_url, enabled=True, member_name=github_username)

    if pull_success:
        # Get commit count
        import subprocess
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=tracker.realign_dir,
            capture_output=True,
            text=True,
            check=False
        )

        commit_count = result.stdout.strip() if result.returncode == 0 else "unknown"
        print(f"✓ Pulled {commit_count} commit(s)")
    else:
        print("⚠️  Pull failed (repository might be empty)")

    # Show success message
    print()
    print("╭─────────────────────────────────────────╮")
    print("│  ✓ Successfully Joined!                 │")
    print("╰─────────────────────────────────────────╯")
    print()
    print(f"Repository: https://github.com/{repo_path}")
    print()
    print("You can now:")
    print("  • Push sessions: aline push")
    print("  • Pull updates: aline pull")
    print("  • Sync: aline sync")
    print()

    return 0
