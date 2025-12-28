# Notehub

Using Github issues as general notes.

## Requirements

- Python 3.8 or higher
- Git
- GitHub CLI (`gh`) - [Installation instructions](https://cli.github.com/)
- GitHub personal access token (for API access)

## User Setup

### 1. Install GitHub CLI

Install the GitHub CLI (`gh`) if you haven't already:

**Windows:**
Download the MSI installer from https://cli.github.com/ (avoid MS Store version - use the official installer)

**macOS:**
```bash
brew install gh
```

**Linux:**
See https://github.com/cli/cli/blob/trunk/docs/install_linux.md

### 2. Authenticate with GitHub CLI

**For public GitHub:**
```bash
gh auth login
```
Follow the prompts to authenticate.

**For GitHub Enterprise:**
```bash
gh auth login --hostname <your-enterprise-github-hostname>
```

**Note:** Notehub uses `gh` for all GitHub API authentication. Make sure this step completes successfully.

### 3. Install Notehub

```bash
pip install lm-notehub
```

### 4. Create Your Notehub Repository

Create a GitHub repository to store your notes as issues. The recommended name is `notehub.default`:

**For public GitHub:**
- Go to https://github.com/new
- Create a repository named `notehub.default`
- Make it private (recommended for personal notes)

**For GitHub Enterprise:**
- Go to your enterprise GitHub instance (e.g., https://github.enterprise.com/new)
- Create a repository named `notehub.default`

### 5. Configure Notehub Settings

Set your default configuration using git config:

**For public GitHub (using default repo name):**
```bash
git config --global notehub.host github.com
git config --global notehub.org <your-github-username>
git config --global notehub.repo notehub.default
```

**For GitHub Enterprise:**
```bash
git config --global notehub.host <your-enterprise-github-hostname>
git config --global notehub.org <your-org-or-username>
git config --global notehub.repo notehub.default
```

Example for enterprise:
```bash
git config --global notehub.host github.enterprise.com
git config --global notehub.org jsmith
git config --global notehub.repo notehub.default
```

**Configure editor (Windows):**

By default, `gh` (and thus `notehub add`) uses `vi` for editing. To use VS Code instead:

```powershell
[System.Environment]::SetEnvironmentVariable('GIT_EDITOR', 'code --wait', 'User')
```

Restart your terminal after setting this. The `--wait` flag ensures VS Code blocks until you close the editor tab.

**Optional: Token environment variables**

While `gh auth login` handles authentication, you can also set token environment variables for additional flexibility:

- `GH_ENTERPRISE_TOKEN_2` - Preferred for enterprise
- `GH_ENTERPRISE_TOKEN` - Alternative for enterprise
- `GITHUB_TOKEN` - For public GitHub

These are checked in order and used to populate the environment when calling `gh`.

### 6. Verify Setup

Test that notehub can access your repository:

```bash
notehub status
```

You should see your configured host/org/repo. You're ready to start using notehub!

## Development Setup

### 1. Install Python (Windows)

- Install the python.org edition of Python3.x, stay away from MS Store
- Installer should add to the PATH:
```
C:\Users\<username>\AppData\Local\Programs\Python\Python313\Scripts
C:\Users\<username>\AppData\Local\Programs\Python\Python313
C:\Users\<username>\AppData\Local\Programs\Python\Launcher
```

### 2. Install in Development Mode

Install notehub with development dependencies:
```bash
python -m pip install -e .[dev]
```

This installs:
- `pytest` - Testing framework
- `pytest-cov` - Code coverage
- `pytest-mock` - Mocking utilities
- `pre-commit` - Git hooks framework

**Note**: Don't use `--user` flag. On Windows, `--user` puts packages in AppData\Roaming instead of AppData\Local, but since you own the latter there's no reason to use `--user`.

### 3. Set Up Pre-commit Hooks

Install the git hooks:
```bash
pre-commit install
```

This will automatically run on every commit:
- Trailing whitespace removal
- End-of-file fixes
- YAML validation
- Large file checks
- Merge conflict detection
- Unit tests with 20% minimum coverage

### 4. Configure GitHub Token

**For public GitHub:**
Set `GITHUB_TOKEN` environment variable with a personal access token.

**Within the corp wall:**
Set `GH_ENTERPRISE_TOKEN_2` environment variable (add to Windows environment variables).

### 5. Running Tests

Run all tests:
```bash
pytest
```

Run only unit tests:
```bash
pytest tests/unit/
```

Run with coverage report:
```bash
pytest --cov=src/notehub --cov-report=term-missing
```

### 6. Publishing to PyPI (Maintainers Only)

To publish a new version to PyPI, you need a PyPI API token. Set it as an environment variable:

**Windows (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable('LM_NOTEHUB_PYPI_TOKEN', 'your_pypi_token_here', 'User')
```

Restart your terminal, then run the publish script:
```bash
bash build-and-publish.sh
```

This will build the distribution and upload it to PyPI.

## Usage

After installation, the `notehub` command will be available:
```bash
notehub --help
```

## Virtual Environments (Optional)

Many developers recommend using virtual environments (venv, conda, etc.) to isolate project dependencies. While this is a best practice for production and complex projects with conflicting dependencies, it adds complexity and can be skipped for simpler projects or solo development. If you want to use one:

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix/macOS
```

Then proceed with the installation steps above.
