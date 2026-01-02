# Quick Start - pyperf-why

## One-Time Setup (5 minutes)

```bash
# 1. Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# 2. Create virtual environment
cd pyperf-why
python3 -m venv venv

# 3. Activate it
source venv/bin/activate

# 4. Install maturin
pip install maturin
```

## Build the Project

```bash
# Make sure venv is activated (you'll see (venv) in your prompt)
source venv/bin/activate

# Build
maturin develop

# Test it works
python -c "from pyperf_why import explain; print('✓ Works!')"
```

## Try It

```bash
# Create a test file
cat > test.py << 'EOF'
from pyperf_why import explain

@explain
def slow_code():
    result = []
    for i in range(100):
        result.append(i * 2)
    return result

slow_code()
EOF

# Run it
python test.py
```

## Daily Workflow

```bash
# Always activate venv first
source venv/bin/activate

# Make changes to Rust code
vim src/heuristics/list_growth.rs

# Rebuild
maturin develop

# Test
python test.py

# When done
deactivate
```

## Quick Commands

```bash
# Activate venv
source venv/bin/activate

# Build
./build.sh

# Deactivate
deactivate
```