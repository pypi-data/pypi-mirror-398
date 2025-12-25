# Installation Guide

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- pipx (recommended for isolated installation)

### Install pipx (if not already installed)

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

### Install Plane Compose

#### Option 1: From GitHub (Latest)

```bash
pipx install git+https://github.com/YOUR_ORG/compose.git
```

#### Option 2: From PyPI (Stable)

```bash
pipx install plane-compose
```

#### Option 3: From Source (Development)

```bash
git clone https://github.com/YOUR_ORG/compose.git
cd compose
pipx install .
```

### Upgrade

```bash
pipx upgrade plane-compose
```

### Uninstall

```bash
pipx uninstall plane-compose
```

---

## Verify Installation

```bash
plane --version
```

You should see output like:
```
Plane Compose v0.1.0
```

---

## Post-Installation Setup

### 1. Authenticate with Plane

```bash
plane auth login
```

Enter your Plane API key when prompted. You can find your API key at:
`https://app.plane.so/<workspace-slug>/settings/account/api-tokens/`

Replace `<workspace-slug>` with your actual workspace slug.

### 2. Verify Authentication

```bash
plane auth whoami
```

---

## Shell Completion (Optional)

### Bash

Add to `~/.bashrc`:
```bash
eval "$(plane --show-completion bash)"
```

### Zsh

Add to `~/.zshrc`:
```bash
eval "$(plane --show-completion zsh)"
```

### Fish

```fish
plane --show-completion fish > ~/.config/fish/completions/plane.fish
```

---

## Troubleshooting

### Command not found after installation

If `plane` command is not found after installation, ensure pipx's bin directory is in your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Add this to your `~/.bashrc`, `~/.zshrc`, or `~/.profile` to make it permanent.

### Permission denied errors

If you encounter permission errors during installation:

1. Ensure you have write permissions to `~/.local/`
2. Use pipx instead of pip for global installations
3. Avoid using `sudo` with pip/pipx

### Python version issues

Check your Python version:
```bash
python3 --version
```

Plane Compose requires Python 3.10 or higher. Update Python if needed:

**macOS (Homebrew):**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

---

## Advanced Installation Options

### Install in a Virtual Environment

```bash
python3 -m venv plane-env
source plane-env/bin/activate  # On Windows: plane-env\Scripts\activate
pip install git+https://github.com/YOUR_ORG/compose.git
```

### Install Specific Version

```bash
pipx install plane-compose==0.1.0
```

### Install with Development Dependencies

```bash
git clone https://github.com/YOUR_ORG/compose.git
cd compose
pip install -e ".[dev]"
```

---

## Docker Installation

Run Plane Compose in Docker without installing anything locally:

```bash
docker run --rm -v $(pwd):/workspace ghcr.io/YOUR_ORG/plane-compose:latest plane --help
```

Create an alias for convenience:

```bash
alias plane='docker run --rm -v $(pwd):/workspace ghcr.io/YOUR_ORG/plane-compose:latest plane'
```

---

## CI/CD Installation

### GitHub Actions

```yaml
- name: Install Plane Compose
  run: |
    pipx install plane-compose
    plane auth login --api-key ${{ secrets.PLANE_API_KEY }}
```

### GitLab CI

```yaml
install_plane:
  script:
    - pip install pipx
    - pipx install plane-compose
    - plane auth login --api-key $PLANE_API_KEY
```

### Jenkins

```groovy
sh 'pipx install plane-compose'
sh 'plane auth login --api-key ${PLANE_API_KEY}'
```

---

## Support

- **Issues**: https://github.com/YOUR_ORG/compose/issues
- **Discussions**: https://github.com/YOUR_ORG/compose/discussions
- **Documentation**: https://github.com/YOUR_ORG/compose#readme
- **Plane Support**: https://plane.so/support

