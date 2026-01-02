# How to Release pyperf-why to PyPI

## Prerequisites

1. **PyPI Account**: Create account at https://pypi.org/account/register/
2. **API Token**: Generate at https://pypi.org/manage/account/token/
3. **Test your build locally first**

## Step-by-Step Release Process

### Option 1: Manual Release (Simplest)

```bash
# 1. Make sure everything is committed
git status

# 2. Update version in Cargo.toml and pyproject.toml if needed
# Current version: 0.1.0

# 3. Build release wheels for your platform
maturin build --release

# 4. Check the wheel was created
ls target/wheels/
# You should see: pyperf_why-0.1.0-*.whl

# 5. Upload to PyPI using maturin
maturin publish

# You'll be prompted for your PyPI credentials or API token
```

### Option 2: Test on TestPyPI First (Recommended)

```bash
# 1. Build the wheel
maturin build --release

# 2. Upload to TestPyPI first
maturin publish --repository testpypi

# 3. Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ pyperf-why

# 4. If everything works, upload to real PyPI
maturin publish
```

### Option 3: Using API Token (Most Secure)

```bash
# 1. Create API token at https://pypi.org/manage/account/token/
# Scope: "Entire account" or specific to "pyperf-why" project

# 2. Save token securely (it shows only once!)
# Token format: pypi-AgEIcHlwaS5vcmc...

# 3. Configure in ~/.pypirc
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TEST_TOKEN_HERE
EOF

chmod 600 ~/.pypirc

# 4. Now you can publish without entering credentials
maturin build --release
maturin publish
```

## What Maturin Does

When you run `maturin publish`, it:
1. Builds wheels for your current platform
2. Includes the Rust extension compiled as a binary
3. Uploads to PyPI
4. Makes it installable via `pip install pyperf-why`

## Cross-Platform Builds

**Important**: `maturin build` only builds for your current platform (macOS in your case).

For users on other platforms, you have options:

### Option A: Let Users Build from Source (Simple)

Users on other platforms can install via:
```bash
pip install pyperf-why
# pip will automatically compile from source using their Rust toolchain
```

They'll need Rust installed. This is automatic and works well.

### Option B: Use GitHub Actions for Multi-Platform (Advanced)

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12', '3.13']
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - uses: dtolnay/rust-toolchain@stable
    - name: Build wheels
      run: |
        pip install maturin
        maturin build --release
    - name: Upload to PyPI
      if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags')
      env:
        MATURIN_PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
      run: maturin publish
```

Then push a tag:
```bash
git tag v0.1.0
git push origin v0.1.0
```

## Post-Release Verification

```bash
# 1. Wait 2-3 minutes for PyPI to process

# 2. Check it's live
open https://pypi.org/project/pyperf-why/

# 3. Test installation in clean environment
python3 -m venv test_env
source test_env/bin/activate
pip install pyperf-why

# 4. Quick test
python -c "from pyperf_why import explain; print('Success!')"

deactivate
rm -rf test_env
```

## Troubleshooting

### "Invalid username/password"
- Use API token, not password
- Username should be `__token__`
- Make sure token starts with `pypi-`

### "Project name already taken"
- Someone else might have registered it
- Try a different name like `pyperf-why-analyzer`
- Update `name` in pyproject.toml

### "Wheel platform not supported"
- This is expected - you can only build for your platform
- Users on other platforms will build from source automatically
- Or use GitHub Actions for multi-platform builds

### Build fails
```bash
# Clean and rebuild
cargo clean
rm -rf target/
maturin build --release
```

## Quick Start (Fastest Way)

```bash
# For your first release, this is the simplest:

# 1. Create PyPI account at https://pypi.org/account/register/

# 2. Build and publish (you'll be prompted for credentials)
maturin build --release
maturin publish

# Done! Your package is live.
```

## Version Updates

To release a new version:

```bash
# 1. Update version in both files:
# - Cargo.toml: version = "0.1.1"
# - pyproject.toml: version = "0.1.1"

# 2. Commit changes
git add Cargo.toml pyproject.toml
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
git push && git push --tags

# 3. Build and publish
maturin build --release
maturin publish
```

## Checklist Before Publishing

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Version numbers match in Cargo.toml and pyproject.toml
- [ ] README.md is complete and accurate
- [ ] LICENSE file exists
- [ ] .gitignore excludes build artifacts
- [ ] Code is committed to git
- [ ] Personal info updated in pyproject.toml (author, email)

## After First Successful Release

Your package will be available at:
- PyPI: https://pypi.org/project/pyperf-why/
- Install: `pip install pyperf-why`
- Downloads tracked automatically on PyPI

Congratulations! 🎉