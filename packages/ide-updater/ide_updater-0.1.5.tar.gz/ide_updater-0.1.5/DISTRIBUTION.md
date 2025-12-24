# Distribution Guide

This guide covers how to package and distribute the IDE Updater tool publicly.

## 🚀 Quick Start (PyPI)

### 1. Set up PyPI account
- Create account at [pypi.org](https://pypi.org)
- Generate API token in account settings
- Store token securely

### 2. Install build tools
```bash
pip install build twine
```

### 3. Build and upload
```bash
# Build the package
python -m build

# Upload to test PyPI first (recommended)
python -m twine upload --repository testpypi dist/*

# Upload to real PyPI
python -m twine upload dist/*
```

### 4. Users install with:
```bash
pip install ide-updater
```

## 📦 Distribution Options

### Option 1: PyPI (Recommended)
- **Pros**: Standard Python distribution, easy `pip install`
- **Cons**: Requires Python environment
- **Best for**: Python developers, general Linux users

### Option 2: GitHub Releases + Binary
```bash
# Create standalone binary with PyInstaller
pip install pyinstaller
pyinstaller --onefile src/ide_updater/main.py --name ide-updater
```
- **Pros**: No Python required, single file
- **Cons**: Larger file size, platform-specific
- **Best for**: End users who don't want Python

### Option 3: Snap Package
```bash
# Create snapcraft.yaml
snapcraft
```
- **Pros**: Easy Ubuntu/Linux installation
- **Cons**: Snap-specific, limited to Snap-enabled systems
- **Best for**: Ubuntu users

### Option 4: AppImage
```bash
# Package as AppImage
python-appimage --python-version 3.11 --name ide-updater
```
- **Pros**: Portable, no installation needed
- **Cons**: Linux-only, larger size
- **Best for**: Portable usage

### Option 5: Docker
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -e .
ENTRYPOINT ["ide-updater"]
```
- **Pros**: Consistent environment, easy deployment
- **Cons**: Requires Docker, overhead
- **Best for**: Server environments, CI/CD

## 🔧 GitHub Setup

### 1. Repository setup
```bash
git remote add origin https://github.com/cosmah/ide-updater.git
git push -u origin main
```

### 2. Add PyPI token to GitHub Secrets
- Go to repository Settings → Secrets and variables → Actions
- Add secret: `PYPI_API_TOKEN` with your PyPI token

### 3. Create release
- Push a git tag: `git tag v0.1.0 && git push origin v0.1.0`
- Create GitHub release from tag
- GitHub Actions will automatically publish to PyPI

## 📊 Marketing & Distribution

### Documentation
- ✅ README.md with clear installation instructions
- ✅ CHANGELOG.md for version history
- ✅ LICENSE file
- ✅ Examples and usage guide

### Community
- Post on Reddit: r/linux, r/programming, r/Python
- Share on Twitter/X with hashtags: #Linux #IDE #CLI #Python
- Submit to awesome lists: awesome-cli-apps, awesome-linux-software
- Write blog post about the tool

### Package Managers
- **Homebrew**: Create formula for macOS/Linux
- **AUR**: Create package for Arch Linux
- **Debian**: Create .deb package
- **RPM**: Create .rpm for Red Hat/SUSE

## 🎯 Recommended Approach

1. **Start with PyPI** - easiest and most standard
2. **Add GitHub Releases** with binary for non-Python users
3. **Consider Snap** if you want Ubuntu store presence
4. **Add to package managers** based on user feedback

## 📈 Success Metrics

Track these to measure adoption:
- PyPI download stats
- GitHub stars/forks
- Issue reports and feature requests
- Community feedback

## 🔄 Maintenance

- Set up automated testing with GitHub Actions
- Monitor for IDE API changes
- Regular dependency updates
- Respond to user issues promptly