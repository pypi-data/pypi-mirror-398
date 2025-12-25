# wp21_train

A modular, extensible Python framework designed for managing data parsing, serialization, and metadata tracking in machine learning workflows — especially for hardware-aware applications such as HLS and AIE profiling. Built with physicists and hardware engineers in mind, `wp21_train` integrates support for CERN ROOT I/O, common formats like JSON and Pickle, and parsing of Xilinx toolchain outputs.

---

## 🚀 Features

- ✅ **Unified interface** for reading/writing training data and metadata  
- ✅ Supports **JSON**, **Pickle**, **YAML** and **ROOT** formats  
- ✅ Parsers for:
  - **HLS reports** (Vivado HLS)
  - **AIE profiling reports** (Vitis AI Engine)
  - **ATHENA configuration**
- ✅ A **training callback interface** to log key events and outputs  
- ✅ Lightweight **type-to-symbol conversion utility**  
- ✅ Versioned with easy integration (`__version__`)

---

## 📦 Included Modules

```
+-----------------------------------------------+--------------------------------------------------------------+-----------------------------------------+
| Module                                        | Description                                                  | Notes / Deps                            |
+-----------------------------------------------+--------------------------------------------------------------+-----------------------------------------+
| wp21_train/savers/json_adapter.py             | JSON-based serialization                                     | stdlib json                             |
| wp21_train/savers/pickle_adapter.py           | Pickle-based serialization                                   | stdlib pickle                           |
| wp21_train/savers/root_adapter.py             | ROOT I/O serialization                                       | uproot, awkward (no ROOT needed)        |
| wp21_train/savers/yml_adapter.py              | YAML I/O serialization                                       | PyYAML (yaml)                           |
| wp21_train/parser/hls_parser.py               | XML parsing of HLS synthesis reports                         |                                         |
| wp21_train/parser/aie_parser.py               | XML parsing of AIE runtime profiling                         |                                         |
| wp21_train/parser/athena_parser.py            | Parsing of ATHENA configuration                              |                                         |
| wp21_train/callbacks/base_callback.py         | Base callback for training pipelines                         |                                         |
| wp21_train/training/searchers/base_search.py  | Base class for search strategies                             |                                         |
| wp21_train/training/searchers/grid_search.py  | Grid search implementation                                   |                                         |
| wp21_train/training/searchers/random_search.py| Random search implementation                                 |                                         |
| wp21_train/training/trainers/base.py          | Common trainer utilities                                     |                                         |
| wp21_train/training/trainers/keras_base.py    | Keras trainer base                                           | tensorflow / keras                      |
| wp21_train/training/trainers/keras_trainer.py | Concrete Keras trainer                                       | tensorflow / keras                      |
| wp21_train/training/trainers/torch_base.py    | PyTorch trainer base                                         | torch                                   |
| wp21_train/training/trainers/torch_trainer.py | Concrete PyTorch trainer                                     | torch                                   |
| wp21_train/training/evaluator.py              | Generic evaluation helpers                                   |                                         |
| wp21_train/training/tuner.py                  | High-level tuning orchestration                              |                                         |
| wp21_train/utils/utility.py                   | Type-shortening / helpers for metadata tagging               |                                         |
| wp21_train/utils/logger.py                    | Simple logging of info/warn/error                            | (renamed from logging.py)               |
| wp21_train/utils/version.py                   | Package versioning (__version__)                             |                                         |
| wp21_train/__init__.py                        | Package exports                                              |                                         |
+-----------------------------------------------+--------------------------------------------------------------+-----------------------------------------+
```

## 🔧 Installation

### From PyPI

```bash
pip install wp21_train
```

---

## 📁 Example Usage

### 🔄 JSON / Pickle / YAML / ROOT Adapters

```python
from wp21_train.savers import json_adapter, pickle_adapter, yml_adapter, root_adapter

adapter = json_adapter("results", dump_data=my_data, dump_meta=my_metadata)
adapter.write_data()

meta, data = adapter.read_data()
```

### 🧠 HLS Parser

```python
from wp21_train.parsers import hls_parser

parser = hls_parser("hls_report.xml")
print(parser._data)        # extracted info
print(parser._meta_data)   # associated metadata
```

### ⚙️ AIE Parser

```python
from wp21_train.parsers import aie_parser

parser = aie_parser("aie_profile.xml")
print(parser._data)
```

### ⚙️ ATHENA Parser

```python
from wp21_train.parsers import athena_parser

parser = athena_parser(data=data_from_adapter, metadata=meta_from_adapter, nevents=10000)
print(parser.config)
print(parser.environment)
```

### 📋 Training Callback

```python
from wp21_train.callbacks import base_callback

cb = base_callback(project_name="FastML4Jets")
cb.on_train_begin()
# training loop here
cb.on_train_end()
```

### 🧬 Type Utility

```python
from wp21_train.utils.utility import get_short_type

print(get_short_type(42))     # 'd'
print(get_short_type("abc"))  # 's'
```

### 🧬 Logging Utility

```python
from wp21_train.utils.logging import log_message

log_message("error", f"Provided number of events ({nevents}) is not an integer.")
```

---

## 🧪 Testing

```bash
pytest tests/
```

---

## 📜 Requirements

- Python ≥ 3.7  
- `uproot` (for reading ROOT files)  
- `xml.etree.ElementTree` (standard lib, for HLS/AIE parsing)  
- **CERN ROOT** (installed and configured) if you use `.root` I/O
- PyYAML ≥ 6.0.0, < 7.0.0 (for reading yaml files)
- awkward (data is represented as awkward arrays)
- pybind11 and openmp - used to implement slow bits in C++

---

## ⚠️ Note About ROOT

This package supports `.root` file serialization and reading **via CERN ROOT**. If you intend to use this feature, ensure that ROOT is installed and properly sourced in your environment. You can install ROOT via Conda:

```bash
conda install -c conda-forge root
```

Or follow the official installation guide:  
https://root.cern/install/

---

## 🧠 Versioning

The current package version is defined in:

```python
from wp21_train.utils.version import __version__
```

---

## 🔖 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Ioannis Xiotidis**  
Email: [ioannis.xiotidis@cern.ch](mailto:ioannis.xiotidis@cern.ch)

**Pawel Mucha**  
Email: [pawel.mucha@cern.ch](mailto:pawel.mucha@cern.ch)

**Vila Andela Petrovic**  
Email: [vila.andela.petrovic@cern.ch](mailto:vila.andela.petrovic@cern.ch)

**David Reikher**  
Email: [david.reikher@cern.ch](mailto:david.reikher@cern.ch)

---
