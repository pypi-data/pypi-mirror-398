## Contributing

We welcome contributions!

**Setup**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

**Run Checks**

```bash
# Lint & Format
flake8 plugin
black --check plugin tests

# Tests
pytest -q
```

---

## Continuous Integration

* **GitHub Actions** runs:

  * `flake8`
  * `black --check`
  * `pytest` (with coverage)
* Python versions: **3.8–3.12**

---