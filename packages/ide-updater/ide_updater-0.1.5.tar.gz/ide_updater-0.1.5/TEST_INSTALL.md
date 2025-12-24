# Testing Your Package Installation

## Option 1: Install pipx (Recommended for CLI tools)

```bash
# Install pipx
sudo apt install pipx
pipx ensurepath

# Then install your package
pipx install ide-updater

# Or test from local files
pipx install dist/ide_updater-0.1.0-py3-none-any.whl
```

## Option 2: Test in a Virtual Environment

```bash
# Create a test virtual environment
python3 -m venv test-venv
source test-venv/bin/activate

# Install from PyPI (after you upload)
pip install ide-updater

# Or install from local wheel
pip install dist/ide_updater-0.1.0-py3-none-any.whl

# Test it
ide-updater check

# Deactivate when done
deactivate
rm -rf test-venv
```

## Option 3: Test from Local Files (Quick Test)

```bash
# Install directly from the wheel file in a venv
python3 -m venv /tmp/test-install
source /tmp/test-install/bin/activate
pip install dist/ide_updater-0.1.0-py3-none-any.whl
ide-updater check
deactivate
```

## Option 4: Install pipx via pip (if apt not available)

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
# Restart terminal or: source ~/.bashrc
pipx install ide-updater
```

## After Uploading to PyPI

Once you've uploaded to PyPI, users can install with:

```bash
# Using pipx (recommended for CLI tools)
pipx install ide-updater

# Or in a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install ide-updater
```

