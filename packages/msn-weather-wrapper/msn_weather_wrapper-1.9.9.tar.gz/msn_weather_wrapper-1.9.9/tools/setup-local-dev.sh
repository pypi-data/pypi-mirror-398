#!/usr/bin/env bash
set -euo pipefail

# Bootstrap local dev environment for Ubuntu 24.04.
# Installs system deps (via apt), Python 3.12 toolchain, Node.js 20, and project deps
# (backend + frontend). Optional flag: --with-playwright-deps to install browser libs.

WITH_PLAYWRIGHT_DEPS=false
for arg in "$@"; do
  case "$arg" in
    --with-playwright-deps) WITH_PLAYWRIGHT_DEPS=true ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

# Resolve repo root (script is in tools/)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ $(id -u) -ne 0 ]]; then
  echo "This script must be run as root (or with sudo)." >&2
  exit 1
fi

DEV_USER=${SUDO_USER:-$USER}

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  ca-certificates curl wget gnupg lsb-release software-properties-common \
  build-essential git unzip jq \
  python3.12 python3.12-venv python3.12-dev python3-pip \
  pkg-config libffi-dev libssl-dev

# Node.js 20 (Nodesource)
if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

# Optional Playwright system deps
if [[ "$WITH_PLAYWRIGHT_DEPS" == "true" ]]; then
  apt-get install -y \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
fi

# Create Python venv in repo root as the dev user
run_as_dev() { sudo -u "$DEV_USER" HOME="$(getent passwd "$DEV_USER" | cut -d: -f6)" "$@"; }

if [[ ! -d "$REPO_ROOT/.venv" ]]; then
  run_as_dev python3.12 -m venv "$REPO_ROOT/.venv"
fi

run_as_dev "$REPO_ROOT/.venv/bin/pip" install --upgrade pip wheel
run_as_dev "$REPO_ROOT/.venv/bin/pip" install -e "$REPO_ROOT"[dev]

# Frontend deps
run_as_dev bash -c "cd '$REPO_ROOT/frontend' && npm install"

cat <<"SUMMARY"
Local dev setup complete.
What was done:
- System deps installed (build-essential, git, Python 3.12 toolchain, Node.js 20, jq, etc.).
- Optional Playwright libs installed: $WITH_PLAYWRIGHT_DEPS
- Python venv created at .venv and project installed with [dev] extras.
- Frontend npm dependencies installed in frontend/.

How to use:
- Activate venv: source .venv/bin/activate
- Run backend tests: pytest
- Run lint: ruff check .
- Run type check: mypy .
- Start API (example): python api.py
- Frontend dev: cd frontend && npm run dev
SUMMARY
