# PhoneTracer ⚡️  
OSINT Phone Number Metadata Toolkit

PhoneTracer is a modular Python toolkit for extracting **public,
non-invasive metadata** from phone numbers using Google’s
`libphonenumber` (via the `phonenumbers` library).

> ❗ PhoneTracer does NOT track phones, reveal owners, or provide live locations.


# [![PyPI version](https://img.shields.io/pypi/v/phonetrcer.svg)](https://pypi.org/project/phonetracer/)
# [![Python versions](https://img.shields.io/pypi/pyversions/phonetrcer.svg)](https://pypi.org/project/phonetracer/)

---

## ✨ Features

- 📞 Phone number parsing & validation
- 🌍 Country / region identification
- 🏷 Carrier lookup (when available)
- 🕒 Timezone detection
- 🧠 Spam-style heuristic scoring
- 📄 Scan numbers from text files
- 📊 JSON export
- 🖥 Argument-based CLI
- 📟 Interactive command-line menu
- 🪟 Desktop GUI (Tkinter)
- 🧪 Built-in tests
- 🤖 GitHub Actions CI

---

## 🧱 Project Architecture

```

phone_tracer/
│
├── main.py        # Mode selector (entry point)
├── core.py        # Shared logic (analysis, logging, export)
├── cli_args.py    # Argument-based CLI mode
├── cli_menu.py    # Interactive command-line menu
├── gui_app.py     # GUI (Tkinter)
│
├── tracer.log     # Runtime logs
└── .github/
    └── workflows/
        └── python-ci.yml

````

---

## 🚀 Getting Started

### Requirements
- Python **3.7+**

### Install dependency
```bash
pip install phonenumbers
````

---

## ▶️ Usage

### Start PhoneTracer

```bash
python main.py
```

You will be prompted to choose:

```
1. Argument mode
2. Command-line menu
3. GUI
```

---

### 🔹 Argument Mode

```bash
python main.py
# choose option 1
```

Then use:

```bash
python cli_args.py -n "+91 9513717169"
python cli_args.py -f numbers.txt
```

---

### 🔹 Command-line Menu

```bash
python main.py
# choose option 2
```

Interactive menu-driven interface.

---

### 🔹 GUI Mode

```bash
python main.py
# choose option 3
```

Simple desktop UI built with Tkinter.

---

## 📂 Output

All scan results are exported as JSON files:

```
YYYYMMDD_HHMMSS_<PHONE>.json
```

---

## 🧠 Spam Heuristics

PhoneTracer assigns a **spam score** based on simple patterns:

* Repeated digits
* Excessive zeros
* Abnormal formatting

This is only an indicator, **not a classification**.

---

## 🤖 Continuous Integration

GitHub Actions automatically:

* Installs dependencies
* Runs core sanity tests
* Ensures CLI paths load correctly

Workflow file:

```
.github/workflows/python-ci.yml
```

---

## 🔐 Privacy & Ethics

* ❌ No phone tracking
* ❌ No subscriber identification
* ❌ No surveillance techniques
* ✅ Metadata-only analysis

Use responsibly and legally.

---

## 📜 License

MIT License
Educational & research use is encouraged.

---

⭐ If you find this project useful, consider starring the repository!

