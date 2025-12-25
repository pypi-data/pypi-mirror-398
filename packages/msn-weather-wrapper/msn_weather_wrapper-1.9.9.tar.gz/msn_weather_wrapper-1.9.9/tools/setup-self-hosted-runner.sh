#!/usr/bin/env bash
set -euo pipefail

# Installs required tooling for the self-hosted runner on Ubuntu 24.04.
# Includes: git, Python 3.12 + pip/venv, Node.js 20, Docker (with Buildx/Compose),
# GitHub CLI (gh), Trivy, Syft, Grype, and common helpers.

if [[ $(id -u) -ne 0 ]]; then
  echo "This script must be run as root (or with sudo)." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y \
  ca-certificates curl wget gnupg lsb-release software-properties-common \
  git build-essential unzip jq \
  python3.12 python3.12-venv python3.12-dev python3-pip

# Node.js 20 (via Nodesource)
if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

# Docker Engine + Buildx + Compose plugin
install_docker() {
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
}

if ! command -v docker >/dev/null 2>&1; then
  install_docker
fi

# GitHub CLI (gh)
if ! command -v gh >/dev/null 2>&1; then
  type -p curl >/dev/null || apt-get install -y curl
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
  chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list
  apt-get update
  apt-get install -y gh
fi

# Trivy
if ! command -v trivy >/dev/null 2>&1; then
  curl -fsSL https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor -o /usr/share/keyrings/trivy.gpg
  echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" > /etc/apt/sources.list.d/trivy.list
  apt-get update
  apt-get install -y trivy
fi

# Syft & Grype
if ! command -v syft >/dev/null 2>&1; then
  curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
fi

if ! command -v grype >/dev/null 2>&1; then
  curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
fi

# Optional: add runner user to docker group (uncomment if needed)
# usermod -aG docker runner

# Optional: Playwright deps (commented out; enable if you run frontend E2E here)
# apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

# Versions summary
cat <<"SUMMARY"
Installed/checked:
- git
- Python 3.12 + venv + pip
- Node.js 20
- Docker Engine + Buildx + Compose plugin
- GitHub CLI (gh)
- Trivy
- Syft
- Grype
- jq, curl, wget, unzip, build-essential

Next steps:
- Ensure the runner user has docker group membership if jobs need Docker without sudo.
- Configure runner service and register with your repo/org.
SUMMARY
