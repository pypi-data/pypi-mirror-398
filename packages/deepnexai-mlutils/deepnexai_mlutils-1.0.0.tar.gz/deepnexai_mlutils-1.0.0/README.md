# DeepNexAI_mlutils

Dark summary image & architecture visualizer for TensorFlow models.

A lightweight utility package to automatically generate:

- Model architecture graph (PNG)
- Parameters report (TXT)
- Dark themed summary image (PNG)

---

## 📦 Installation

### Online
```bash
pip install DeepNexAI_mlutils



















Dark summary image & architecture visualizer for TensorFlow models.

A lightweight utility package to automatically generate:

- Model architecture graph (PNG)
- Parameters report (TXT)
- Dark themed summary image (PNG)

---

## 📦 Installation

### Online
```bash
pip install DeepNexAI_mlutils


# Offline (Wheel)
pip install DeepNexAI_mlutils-1.0.0-py3-none-any.whl



# Usage
from DeepNexAI_mlutils.model_tools import save_model_visualizer

save_model_visualizer(model, "MyModel")



# This will generate:

MyModel_Architecture.png
MyModel_Parameters.txt
MyModel_Summary.png


# Build your own wheel (Offline install)
# Inside project root:
pip install wheel
python setup.py bdist_wheel


# The wheel file will be created inside:
dist/


# Requirements
Python 3.8+
TensorFlow
Pillow
pydot
graphviz