# Quick Start: Publishing srvdb to PyPI with uv

## ✅ Setup Complete

You now have:
- ✅ Virtual environment (`.venv`)
- ✅ Maturin 1.10.2 installed
- ✅ Built wheel: `srvdb-0.1.0-cp312-cp312-manylinux_2_34_x86_64.whl`

## 🚀 Publishing Steps

### 1. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 2. Test Locally (Recommended)
```bash
# Install the wheel locally
uv pip install target/wheels/srvdb-0.1.0-cp312-cp312-manylinux_2_34_x86_64.whl

# Test it works
python3 -c "import srvdb; print(f'srvdb v{srvdb.__version__}')"

# Run the example
python3 examples/python_demo.py
```

### 3. Get PyPI Credentials

**Create PyPI Account:**
1. Go to https://pypi.org/account/register/
2. Verify your email

**Generate API Token:**
1. Go to https://pypi.org/manage/account/token/
2. Create token with name "srvdb-upload"
3. **Save the token** - you'll only see it once!

### 4. Publish to PyPI

```bash
# Activate venv (if not already)
source .venv/bin/activate

# Set your PyPI token as environment variable
export MATURIN_PYPI_TOKEN=pypi-AgEIcGljcmkub3JnLyotGx... # Your actual token

# Publish!
maturin publish
```

**OR** use interactive mode:
```bash
maturin publish
# Enter username: __token__
# Enter password: <paste your PyPI token>
```

### 5. Verify Publication

After successful upload:
```bash
# Anyone can now install:
pip install srvdb

# Or with uv:
uv pip install srvdb
```

## 🔄 Updating the Package

For future releases:

```bash
# 1. Update version in both files
#    - Cargo.toml: version = "0.2.0"
#    - pyproject.toml: version = "0.2.0"

# 2. Make your code changes

# 3. Build new wheel
source .venv/bin/activate
maturin build --release

# 4. Publish
maturin publish
```

## 📋 Pre-Flight Checklist

Before publishing:
- [ ] PyPI account created
- [ ] API token generated
- [ ] Package name `srvdb` is available (check https://pypi.org/project/srvdb)
- [ ] README.md is up-to-date
- [ ] Version number is correct (0.1.0)
- [ ] Local test passed

## 🐛 Troubleshooting

**"Package name already taken"**
- Choose different name or contact PyPI if you own it

**"Invalid credentials"**
- Regenerate API token
- Use `__token__` as username, token as password

**Build failed**
- Run `cargo build --release` first
- Check Rust toolchain is working

## 📦 Current Build Output

Wheel location: `target/wheels/srvdb-0.1.0-cp312-cp312-manylinux_2_34_x86_64.whl`
- Platform: Linux x86_64
- Python: 3.12
- Size: ~1.3MB

## 📚 Resources

- Maturin Guide: https://www.maturin.rs/tutorial
- PyPI Upload: https://pypi.org/help/#publishing
- srvdb Repo: https://github.com/Srinivas26k/svdb
