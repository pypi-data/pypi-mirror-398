# Testing Ash SDK for Python

A simple demo SDK.

## 📦 Installation

```bash
pip install testing-ash-sdk
```

## 🚀 Usage

```python
from testing_ash_sdk import greet, greet_user

print(greet())
# Output: hurray have a nice day

print(greet_user('John'))
# Output: hurray John, have a nice day
```

## 📚 API

| Function | Description |
|----------|-------------|
| `greet()` | Returns "hurray have a nice day" |
| `greet_user(name)` | Returns "hurray {name}, have a nice day" |

---

## 🚀 Publishing Instructions

### Step 1: Install Build Tools

```bash
cd python-sdk
pip install build twine
```

### Step 2: Build

```bash
python -m build
```

### Step 3: Publish

```bash
twine upload dist/*
```

---

## 📄 License

MIT
