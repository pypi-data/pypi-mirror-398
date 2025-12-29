# LoggedExample

**LoggedExample** is a clean, minimal demonstration application built to showcase **[ChronicleLogger](https://pypi.org/project/ChronicleLogger/)** — a high-performance, POSIX-compliant, cross-version (Python 2.7 & 3.x) logging utility with daily rotation, automatic archiving (tar.gz >7 days), old log removal (>30 days), privilege-aware paths (`/var/log` for root, `~/.app` for users), and smart environment detection (venv, pyenv, pyenv-virtualenv, Miniconda/Anaconda).

**ChronicleLogger** is available on PyPI: https://pypi.org/project/ChronicleLogger/

**LoggedExample PyPI**: https://pypi.org/project/LoggedExample/

**Current version**: 1.2.5

## Features
- Uses **ChronicleLogger** for structured, timestamped logging: `[YYYY-MM-DD HH:MM:SS] pid:<PID> [<LEVEL>] @<COMPONENT> :] <MESSAGE>`
- Automatically adapts log/base directory based on:
  - Active Python environment (venv / pyenv / pyenv-virtualenv / miniconda)
  - User privileges (root vs non-root)
- Debug mode (`DEBUG=show`) displays complete logger + environment information
- Simple CLI interface (`LoggedExample info`)
- Zero external dependencies beyond ChronicleLogger
- Ready for development, containers, or system services

## Installation

### Quick install (global or current environment)

```bash
pip install LoggedExample
```

Run:

```bash
LoggedExample info
# With full debug output:
DEBUG=show LoggedExample info
```

### Recommended: Use an isolated environment

LoggedExample (powered by ChronicleLogger) detects the active Python environment and places logs inside it — usually under `<env>/.app/logged-example/log/` or `~/.app/logged-example/log/`.

---

## Environment Guide: Purpose, Installation & Usage (2025)

| Environment                  | Purpose                                                                 | Log Location (non-root)                                      | Log Location (root)                  | Best For                              |
|------------------------------|-------------------------------------------------------------------------|--------------------------------------------------------------|--------------------------------------|---------------------------------------|
| N/A                     | Built-in, lightweight, project-specific isolation                       | `<home>/.app/logged-example/log/`                            | `/var/log/logged-example/`        | Quick projects, CI/CD, simple teams   |
| **venv**                     | Built-in, lightweight, project-specific isolation                       | `<venv>/.app/logged-example/log/`                            | `<venv>/.app/logged-example/log/`           | Quick projects, CI/CD, simple teams   |
| **pyenv**                    | Manage multiple Python versions easily on one system                    | `~/.pyenv/versions/3.12/.app/logged-example/log/`            | `/root/.pyenv/versions/3.12/.app/logged-example/log/`           | Developers switching Python versions  |
| **pyenv + virtualenv**       | Best of both worlds: version + project isolation                        | `~/.pyenv/versions/<env-name>/.app/logged-example/log/`      | `/root/.pyenv/versions/<env-name>/.app/logged-example/log/`           | **Recommended** for most developers   |
| **Miniconda**                | Lightweight Conda distribution — fast, minimal, scientific-friendly    | `~/miniconda3/envs/<name>/.app/logged-example/log/`          | `/root/miniconda3/envs/<name>/.app/logged-example/log/`           | Data science, ML, reproducible envs   |
| **Anaconda**                 | Full-featured Conda with hundreds of preinstalled packages              | `~/anaconda3/envs/<name>/.app/logged-example/log/`           | `/root/anaconda3/envs/<name>/.app/logged-example/log/`           | Beginners in data/science, heavy deps |

### 1. venv (standard Python virtual environment)

```bash
python3 -m venv logged-env
source logged-env/bin/activate

pip install LoggedExample

DEBUG=show LoggedExample info
```

### 2. pyenv (multiple Python versions)

```bash
pyenv install 3.12
pyenv global 3.12               # or pyenv local 3.12

pip install LoggedExample

DEBUG=show LoggedExample info
```

### 3. pyenv + virtualenv plugin (recommended)

```bash
pyenv virtualenv 3.12 logged-example-env
pyenv activate logged-example-env

pip install LoggedExample

DEBUG=show LoggedExample info
```

### 4. Miniconda (lightweight Conda)

```bash
conda create -n logged-example python=3.12
conda activate logged-example

pip install LoggedExample

DEBUG=show LoggedExample info
```

### 5. Anaconda (full distribution)

```bash
conda create -n logged-example python=3.12
conda activate logged-example

pip install LoggedExample

DEBUG=show logged-example info
```

### Root / System-wide Usage

```bash
sudo -E DEBUG=show logged-example info          # via sudo → user home
sudo su -                                       # real root
DEBUG=show LoggedExample info                  # → /var/log/logged-example/
```

## Development / From Source

```bash
git clone https://github.com/yourusername/logged-example.git
cd logged-example

pyenv virtualenv 3.12 logged-example-dev
pyenv activate logged-example-dev

pip install -e .
```

## License

MIT

Made with ❤️ using **[ChronicleLogger](https://pypi.org/project/ChronicleLogger/)** — happy logging!
