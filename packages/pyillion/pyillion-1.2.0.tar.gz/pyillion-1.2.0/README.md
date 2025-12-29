# pyillion

<!-- BADGES -->
![PyPI](https://img.shields.io/pypi/v/pyillion)
![Python](https://img.shields.io/pypi/pyversions/pyillion)
![License](https://img.shields.io/pypi/l/pyillion)
![Wheel](https://img.shields.io/pypi/wheel/pyillion)
![Status](https://img.shields.io/badge/status-stable-brightgreen)

> Convert integers into long-form and short form **-illion notation**  
> (million, billion, trillion, …) with high precision and simplicity.

---

## ✨ Features

- 🔢 Convert large integers to human-readable **illion format**
- ⚡ Lightweight, zero dependencies
- 🧮 Custom decimal precision
- 🧠 Simple and explicit API
- 📦 Clean **src-layout**, PyPI-ready

---

## 📦 Installation

```bash
pip install pyillion
```

---

## 🚀 Quick Start

```python
from pyillion import illionify

print(illionify(1234567890))
# 1.234 billion
```

With custom precision:

```python
print(illionify(1234567890, r=4))
# 1.2345 billion
```
With short form:

```python
print(illionify(1234567890, short=True))
# 1.234B
```
---

## 🧩 API Reference

### `illionify(n: int, r: int = 3, short = False) -> str`

Turn a number into long-form or short-form *-illion* notation.

```python
illionify(9876543210)
# '9.876 billion'
```

---

### `il(n: int, bl: bool = False)`

Return the *-illion* name corresponding to `n`.

```python
il(7)
# 'sextillion'

il(7, bl=True)
# 1000 ** 7
```
### `il_short(n: int, bl: bool = False)`

Return the short form *-illion* name corresponding to `n`.

```python
il_short(7)
# 'Sx'

il(7, bl=True)
# 1000 ** 7
```
---

### `e(n: int)`

Return `1000 ** n`.

```python
e(4)
# 1000000000000
```

---

### `d(a, b, r: int = 3)`

Safe division with fixed decimal precision.

```python
d(215, 11, 4)
# 19.5454
```

---

## 📁 Project Structure

```text
pyillion/
├─ src/
│  └─ pyillion/
│     ├─ __init__.py
│     └─ illionifyer.py
├─ pyproject.toml
├─ README.md
└─ LICENSE
```

---

## 🧪 Supported Python Versions

- Python **3.8+**
- Tested on **3.13 / 3.14**

---

## 📜 License

This project is licensed under the **MIT License**.  
See [LICENSE](LICENSE) for details.

---

## 🌐 Links

- 🧾 PyPI: https://pypi.org/project/pyillion/
- 🧑‍💻 GitHub: https://github.com/phannoiershit/pyillion
- 🐞 Issues: https://github.com/phannoiershit/pyillion/issues

---

## ⭐ Why pyillion?

If you need:
- deterministic formatting
- full control over *-illion logic*
- **no hidden heuristics** like `humanize`

→ **pyillion is for you.**

