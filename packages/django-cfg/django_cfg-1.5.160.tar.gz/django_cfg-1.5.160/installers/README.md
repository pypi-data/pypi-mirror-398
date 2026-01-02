# Django-CFG Installer

This directory contains the source code and scripts for the Django-CFG cross-platform installer.

## Directory Structure

*   **`go-installer/`**: The source code for the "thick" Go binary installer. This compiles into a standalone executable that contains all necessary logic.
*   **`install.sh`**: A "thin" bootstrap script for Linux and macOS. It downloads the correct Go binary from GitHub Releases and runs it.
*   **`install.ps1`**: A "thin" bootstrap script for Windows (PowerShell). It downloads the correct Go binary from GitHub Releases and runs it.
*   **`Makefile`**: Automation for building and releasing.

## How to Release

We use a manual release process via the `Makefile` to build binaries for all platforms and upload them to GitHub.

### Prerequisites

*   **Go** (1.21+)
*   **GitHub CLI (`gh`)** (authenticated with `gh auth login`)

### Steps

1.  **Auto-increment and Release** (Recommended):
    ```bash
    make publish
    ```
    This automatically increments the patch version and creates a new release.

2.  **Manual version release**:
    ```bash
    make release VERSION=v1.0.0
    ```

    This command will:
    1.  Compile the Go binary for **Windows** (`.exe`), **macOS** (Intel & Apple Silicon), and **Linux**.
    2.  Create a new Release on GitHub with the tag `v1.0.0`.
    3.  Upload the compiled binaries to the release assets.

## Release Management

### List Releases

View all GitHub releases:
```bash
make list-releases
```

### Cleanup Old Releases

Remove old releases to keep only the latest:

**Using Makefile** (with confirmation prompt):
```bash
# Keep only the latest release
make clean-old-releases

# Keep the last 3 releases
make clean-old-releases KEEP=3
```

**Using Shell Script** (more flexible):
```bash
# Dry run - see what would be deleted without making changes
./cleanup-releases.sh 1 --dry-run

# Keep only the latest release
./cleanup-releases.sh

# Keep the last 5 releases
./cleanup-releases.sh 5
```

The shell script provides:
- Confirmation prompts before deletion
- Dry-run mode to preview changes
- Detailed progress reporting
- Error handling and summary statistics

## How Users Install

Users don't need to download the binary manually. They can use the one-line install commands which use the bootstrap scripts:

**Linux / macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/markolofsen/django-cfg/main/installers/install.sh | bash
```

**Windows (PowerShell):**
```powershell
iwr -useb https://raw.githubusercontent.com/markolofsen/django-cfg/main/installers/install.ps1 | iex
```

These scripts automatically detect the user's OS and architecture, download the correct binary from the latest GitHub Release, and execute it.
