# LerpNet (Learnable Interpolation Network)

LerpNet is a **lightweight neural interpolation library** designed for **fast regression and function approximation**. It trains a compact MLP, learns smooth interpolation from data, and exports results in **Python-friendly `.pkl`** and **embedded-friendly `.json`** formats for deployment on systems like ESP32.  

No heavy deep learning frameworks are required—perfect for **edge AI applications**.

---

## Features

- Learnable interpolation using a **compact MLP**
- Extremely lightweight (**no PyTorch / TensorFlow required**)
- Outputs:
  - `.pkl` for Python inference
  - `.json` for C++ / ESP32 inference
- Built-in utilities:
  - Data normalization
  - Learning rate finder
  - Training metrics (RMSE, MAPE, R²)
- Designed for **edge & embedded deployment**
- Ideal for:
  - Sensor calibration
  - Curve fitting
  - Control systems
  - Real-time interpolation
  - Function approximation
  - Learnable lookup tables
  - Replacement for hard-coded formulas

---

## Generated files:

1) model.pkl — Python inference
2) norm_constants.json — Input/output normalization
3) model_weights.json — Embedded / C++ inference
4) Training plots & CSV (actual_vs_predicted.csv)

## Installation

```bash
pip install lerpnet
