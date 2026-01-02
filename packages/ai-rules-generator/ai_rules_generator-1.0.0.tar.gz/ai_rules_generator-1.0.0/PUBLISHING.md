# Publishing Guide - Package Manager Instructions

This guide provides step-by-step instructions for publishing ai-rules-generator to all supported package managers.

## Table of Contents

- [Pre-Publishing Checklist](#pre-publishing-checklist)
- [1. PyPI (pip)](#1-pypi-pip)
- [2. Homebrew (brew) - macOS/Linux](#2-homebrew-brew---macoslinux)
- [3. AUR (yay/paru) - Arch Linux](#3-aur-yayparu---arch-linux)
- [4. APT (Debian/Ubuntu)](#4-apt-debianubuntu)
- [5. Chocolatey (Windows)](#5-chocolatey-windows)
- [6. winget (Windows)](#6-winget-windows)
- [7. Flatpak (Linux Universal)](#7-flatpak-linux-universal)
- [Quick Release Checklist](#quick-release-checklist)
- [Package Manager Summary](#package-manager-summary)
- [Troubleshooting](#troubleshooting)

---

## Pre-Publishing Checklist

Before publishing to any package manager:

1. **Update Version Numbers** in:

   - `pyproject.toml`
   - `setup.py`
   - `PKGBUILD` (pkgver)
   - `Formula/ai-rules-generator.rb` (url version)
   - `chocolatey/ai-rules-generator.nuspec`
   - `debian/changelog`
   - `flatpak/com.github.ai_rules_generator.AIRulesGenerator.yaml`

2. **Create Git Tag and Release**

   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   gh release create v1.0.0 --notes "Release v1.0.0"
   ```

3. **Calculate Checksums**
   ```bash
   curl -L -o ai-rules-generator-1.0.0.tar.gz \
     https://github.com/rpupo63/ai-rules-generator/archive/v1.0.0.tar.gz
   sha256sum ai-rules-generator-1.0.0.tar.gz
   ```

---

## 1. PyPI (pip)

### Setup (First Time)

1. Create accounts (they are **separate**):

   - https://pypi.org/account/register/
   - https://test.pypi.org/account/register/ (for testing - **requires separate account**)

2. Generate API tokens (one for each):

   - **TestPyPI**: Go to https://test.pypi.org/manage/account/token/ and create a token
   - **PyPI**: Go to https://pypi.org/manage/account/token/ and create a token
   - Tokens should start with `pypi-`
   - **Important**: TestPyPI tokens are different from PyPI tokens - you cannot use a PyPI token on TestPyPI!

   **Token Scope Recommendation**:

   - **Recommended**: Create a **project-scoped token** (select the specific project: `ai-rules-generator`)
   - **Why**: Better security - if compromised, only this project is affected
   - **Alternative**: Account-wide token works, but has broader permissions

3. Install build tools: `pip install build twine`

4. Configure authentication (choose one method):

   **Option A: Using .pypirc file (Recommended)**

   Create `~/.pypirc`:

   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-YOUR_PYPI_TOKEN_HERE

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-YOUR_TESTPYPI_TOKEN_HERE
   ```

   Make it secure: `chmod 600 ~/.pypirc`

   **Option B: Using environment variables**

   ```bash
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-YOUR_TESTPYPI_TOKEN_HERE
   ```

   **Option C: Using keyring (most secure)**

   ```bash
   keyring set https://test.pypi.org/legacy/ __token__ YOUR_TESTPYPI_TOKEN
   ```

### Publishing

```bash
# Build package
python -m build

# Test upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*
```

### Verification

```bash
pip install ai-rules-generator==1.0.0
ai-rules-generator --help
```

### Troubleshooting Authentication Errors

If you get a `403 Forbidden` error:

1. **Verify you have a TestPyPI account** (separate from PyPI)
2. **Use a TestPyPI token** (not a PyPI token) - generate at https://test.pypi.org/manage/account/token/
3. **Token format**: Username = `__token__`, Password = full token including `pypi-` prefix
4. **Check token permissions** - ensure upload scope is enabled

---

## 2. Homebrew (brew) - macOS/Linux

### Setup (First Time)

1. Create GitHub repository: `rpupo63/homebrew-tap`
2. Clone locally: `git clone https://github.com/rpupo63/homebrew-tap.git ~/homebrew-tap`

### Publishing

1. Update checksum in `Formula/ai-rules-generator.rb`:

   ```bash
   # Download release
   curl -L -o /tmp/ai-rules-generator-1.0.0.tar.gz \
     https://github.com/rpupo63/ai-rules-generator/archive/v1.0.0.tar.gz

   # Calculate checksum (macOS)
   shasum -a 256 /tmp/ai-rules-generator-1.0.0.tar.gz
   # Or (Linux)
   sha256sum /tmp/ai-rules-generator-1.0.0.tar.gz
   ```

2. Copy and update formula:
   ```bash
   cp Formula/ai-rules-generator.rb ~/homebrew-tap/Formula/
   cd ~/homebrew-tap
   git add Formula/ai-rules-generator.rb
   git commit -m "Update ai-rules-generator to 1.0.0"
   git push origin main
   ```

### User Installation

```bash
brew tap rpupo63/tap
brew install ai-rules-generator
```

---

## 3. AUR (yay/paru) - Arch Linux

### Setup (First Time)

1. Create AUR account: https://aur.archlinux.org/register
2. Add SSH key to AUR account
3. Test: `ssh -T aur@aur.archlinux.org`

### Publishing

1. Generate .SRCINFO:

   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```

2. Clone AUR repository:

   ```bash
   git clone ssh://aur@aur.archlinux.org/ai-rules-generator.git /tmp/aur-ai-rules-generator
   ```

3. Update files:

   ```bash
   cp PKGBUILD .SRCINFO /tmp/aur-ai-rules-generator/
   cd /tmp/aur-ai-rules-generator
   ```

4. Commit and push:
   ```bash
   git add PKGBUILD .SRCINFO
   git commit -m "Update to version 1.0.0"
   git push origin master
   ```

### User Installation

```bash
yay -S ai-rules-generator
# or
paru -S ai-rules-generator
```

---

## 4. APT (Debian/Ubuntu)

### Setup (First Time)

1. Install build tools: `sudo apt install debhelper dh-python python3-all python3-setuptools devscripts`
2. Optional: Create Launchpad PPA account for automatic builds

### Publishing Method 1: Direct .deb Distribution

```bash
# Build .deb package
dpkg-buildpackage -us -uc -b

# Upload to GitHub releases
gh release upload v1.0.0 ../ai-rules-generator_1.0.0-1_all.deb
```

### Publishing Method 2: Launchpad PPA

```bash
# Build source package (requires GPG key setup)
debuild -S -sa

# Upload to PPA
dput ppa:rpupo63/ai-rules-generator ../ai-rules-generator_1.0.0-1_source.changes
```

### User Installation

```bash
# From .deb file
wget https://github.com/rpupo63/ai-rules-generator/releases/download/v1.0.0/ai-rules-generator_1.0.0-1_all.deb
sudo dpkg -i ai-rules-generator_1.0.0-1_all.deb

# From PPA
sudo add-apt-repository ppa:rpupo63/ai-rules-generator
sudo apt update
sudo apt install ai-rules-generator
```

---

## 5. Chocolatey (Windows)

### Setup (First Time)

1. Create account: https://community.chocolatey.org/account/register
2. Get API key from: https://community.chocolatey.org/account
3. Install Chocolatey CLI (if needed)

### Publishing

1. Update checksum in `chocolatey/tools/chocolateyinstall.ps1`:

   ```powershell
   # Download release
   $url = "https://github.com/rpupo63/ai-rules-generator/archive/v1.0.0.zip"
   Invoke-WebRequest -Uri $url -OutFile ai-rules-generator.zip

   # Calculate checksum
   Get-FileHash .\ai-rules-generator.zip -Algorithm SHA256
   ```

2. Build package:

   ```powershell
   cd chocolatey
   choco pack ai-rules-generator.nuspec
   ```

3. Push to Chocolatey:

   ```powershell
   choco push ai-rules-generator.1.0.0.nupkg --source https://push.chocolatey.org/ --api-key YOUR_API_KEY
   ```

4. Wait for moderation (24-48 hours for updates, 3-7 days for first package)

### User Installation

```powershell
choco install ai-rules-generator
```

---

## 6. winget (Windows)

### Setup (First Time)

1. Fork: https://github.com/microsoft/winget-pkgs
2. Install wingetcreate: `winget install Microsoft.WingetCreate`

### Publishing

1. Update SHA256 hashes in manifest files (if using installers)

2. Copy manifest files to your fork:

   ```bash
   # Copy .winget/manifests/ structure to your fork
   cp -r .winget/manifests/a/AIRulesGenerator ../winget-pkgs/manifests/a/
   ```

3. Validate manifests:

   ```powershell
   winget validate --manifest .winget/manifests/a/AIRulesGenerator/AIRulesGenerator/1.0.0/
   ```

4. Create pull request to microsoft/winget-pkgs

5. Wait for automated tests and maintainer approval

### User Installation

```powershell
winget install AIRulesGenerator.AIRulesGenerator
```

---

## 7. Flatpak (Linux Universal)

### Setup (First Time)

1. Install flatpak-builder: `sudo apt install flatpak flatpak-builder`
2. Add Flathub: `flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo`

### Publishing Method 1: Direct Bundle Distribution

1. Update SHA256 hashes in `flatpak/com.github.ai_rules_generator.AIRulesGenerator.yaml`

2. Build bundle:

   ```bash
   cd flatpak
   flatpak-builder --repo=repo --force-clean build-dir com.github.ai_rules_generator.AIRulesGenerator.yaml
   flatpak build-bundle repo ai-rules-generator-1.0.0.flatpak com.github.ai_rules_generator.AIRulesGenerator
   ```

3. Upload to GitHub releases:
   ```bash
   gh release upload v1.0.0 ai-rules-generator-1.0.0.flatpak
   ```

### Publishing Method 2: Flathub (Official Distribution)

1. Fork: https://github.com/flathub/flathub

2. Create directory: `com.github.rpupo63.AIRulesGenerator`

3. Copy files from `flatpak/` directory

4. Update app ID from `ai_rules_generator` to `rpupo63` in manifest files

5. Create PR to Flathub with title: "Add com.github.rpupo63.AIRulesGenerator"

6. Wait for review and approval

### User Installation

```bash
# From Flathub (after approval)
flatpak install flathub com.github.ai_rules_generator.AIRulesGenerator

# From .flatpak bundle
flatpak install --user ai-rules-generator-1.0.0.flatpak
```

---

## Quick Release Checklist

- [ ] Update version in all config files
- [ ] Update `debian/changelog`: `dch -v 1.0.0-1 "Release version 1.0.0"`
- [ ] Update `flatpak/*.metainfo.xml` release date
- [ ] Create Git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Create GitHub release with notes
- [ ] Calculate and update checksums
- [ ] Publish to PyPI
- [ ] Update and push Homebrew formula
- [ ] Update and push AUR PKGBUILD
- [ ] Build and upload .deb to GitHub releases
- [ ] Push Chocolatey package
- [ ] Create PR to winget-pkgs
- [ ] Build and upload Flatpak bundle (optional: submit to Flathub)

---

## Package Manager Summary

| Package Manager | Platform      | Setup Time | Publish Time | Auto-Update |
| --------------- | ------------- | ---------- | ------------ | ----------- |
| PyPI            | All           | Quick      | Instant      | Manual      |
| Homebrew        | macOS/Linux   | Medium     | Instant      | Yes         |
| AUR (yay)       | Arch          | Medium     | Instant      | Yes         |
| APT             | Debian/Ubuntu | Medium     | Instant      | Yes         |
| Chocolatey      | Windows       | Medium     | 24-48 hours  | Yes         |
| winget          | Windows       | Medium     | Days         | Yes         |
| Flatpak         | Linux         | Medium     | Days-Weeks   | Yes         |

---

## Troubleshooting

**Version mismatch errors:** Ensure all version numbers match across all config files.

**Checksum errors:** Recalculate checksums after creating release tag:

```bash
curl -L -o release.tar.gz https://github.com/rpupo63/ai-rules-generator/archive/v1.0.0.tar.gz
sha256sum release.tar.gz
```

**AUR SSH issues:** Test connection: `ssh -T aur@aur.archlinux.org`

**Chocolatey moderation:** First package takes 3-7 days; updates typically 24-48 hours.

**winget validation:** Use `winget validate` command to check manifests before PR.
