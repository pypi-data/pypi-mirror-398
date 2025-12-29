![KaggleEase Banner](https://github.com/Dinesh-raya/kaagleease/raw/main/kaggleease_banner_1766798647754.png)

# KaggleEase 🚀
### The Universal Kaggle Gateway for Data Scientists

KaggleEase is a minimalist, high-performance Python library designed to bridge the gap between Kaggle's vast data ecosystem and your local or Colab development environment. It replaces the heavy official Kaggle package with a smart, self-healing REST client that "just works."

---

## 📘 The Masterclass Notebook
Before you dive into the code, check out our **KaggleEase_Masterclass.ipynb** located in the root directory. 

It is the **definitive guide** for everything from authentication to advanced universal format loading. 
> [!TIP]
> **[Open the Masterclass Notebook](https://github.com/Dinesh-raya/kaagleease/blob/main/KaggleEase_Masterclass.ipynb)** to see every feature in action with zero-boilerplate code.

---

## 🌟 Top Features

| Feature | Description |
| :--- | :--- |
| **🚀 Universal Load** | Handles CSV, Parquet, JSON, Excel, and SQLite automatically. |
| **🏆 Native Competitions** | Official competition slugs (like `titanic`) work out of the box. |
| **🛡️ No-Crash Fallback** | Returns local path strings for non-tabular data (Images/Models). |
| **🧠 Deep Intelligence** | Fuzzy handle matching, implicit resolution, and self-healing APIs. |
| **✨ IPython Magics** | Use `%kaggle_load` for zero-boilerplate loading in notebooks. |

---

## ⚡ Quick Start

### 1. Installation
```python
!pip install kaggleease --upgrade
```

### 2. Authentication (Foolproof)
You can set environment variables (safest) or use `kaggle.json`.
```python
import os
os.environ['KAGGLE_USERNAME'] = "your_username"
os.environ['KAGGLE_KEY'] = "your_api_key"
```

### 3. Load Anything
```python
from kaggleease import load

# Loaded as a Pandas DataFrame automatically
df = load("titanic") 

# Images? Returns the local path string
path = load("resnet50")
```

---

## 🛠️ Advanced Usage

### Universal Formats
```python
# Load JSON
df = load("rtatman/iris-dataset-json-version")

# Load SQLite (Auto-detects the first table!)
df = load("world-bank/world-development-indicators")
```

### Deep-Scan Intelligence
If a dataset has an obscured API (like `heptapod/titanic`), KaggleEase bypassed the error, downloads the data, and scans every subdirectory to find your CSV for you.

---

## 🤝 Contributing & Support
Built by Data Scientists, for Data Scientists.
- **GitHub**: [Dinesh-raya/kaagleease](https://github.com/Dinesh-raya/kaagleease)
- **PyPI**: [kaggleease](https://pypi.org/project/kaggleease/)

---
*KaggleEase v1.3.9 - The "Universal Resilience" Release.*
