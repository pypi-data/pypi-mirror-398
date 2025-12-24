# PyThermoCalcDB

[![PyPI Downloads](https://static.pepy.tech/badge/pythermocalcdb/month)](https://pepy.tech/projects/pythermocalcdb)
![PyPI](https://img.shields.io/pypi/v/PyThermoCalcDB)
![Python Version](https://img.shields.io/pypi/pyversions/PyThermoCalcDB.svg)
![License](https://img.shields.io/pypi/l/PyThermoCalcDB)

**PyThermoCalcDB** — Python Thermodynamic Calculation Engine powered by PyThermoDB

PyThermoCalcDB is a companion package to PyThermoDB, designed to provide a robust set of thermodynamic calculations, utilities, and workflows — using thermodynamic properties, constants, and equations built with PyThermoDB.

## 🚀 Why PyThermoCalcDB?

- **Seamless integration** with PyThermoDB: use the database of thermodynamic data (pure component properties, correlations, etc.) as the foundation.
- **Reusable calculation tools**: functions for various calculations.
- **Consistent with your thermodynamic ecosystem**: fits with existing packages like PyThermoModels, PyPhaseEQ, PyThermoFlash — offering a central “calculation engine” layer.
- **Minimal dependencies**: lean design, using PyThermoDB as core data source; optionally depend on well-known numerical libraries (e.g. NumPy, SciPy) if needed for complex calculations.
- **Flexible use-cases**: from quick property lookups to advanced process calculations, or integration in larger workflows or multi-agent systems.

## 📦 Installation

```bash
pip install pyThermoCalcDB
```

## 🚀 Usage

PyThermoCalcDB provides high-level thermodynamic calculation routines built on top of PyThermoDB. It is optimized for scripts, notebooks, and pipeline integration — the examples in `examples/` show complete, runnable workflows.

- 🔧 What it does
  - 🧩 Build a `ModelSource` from ThermoDB files (via `pyThermoLinkDB`) and access data/equation sources.
  - ♨️ Formation properties
    - 🔥 Enthalpy of formation — `calc_enthalpy_of_formation_at_temperature`, `calc_enthalpy_of_formation_range`
    - ⚖️ Gibbs energy of formation — `calc_gibbs_energy_of_formation_at_temperature`, `calc_gibbs_energy_of_formation_range`
  - 🌡️ Vapor / phase properties
    - 💧 Vapor pressure at T — `calc_vapor_pressure_at_temperature`
    - 🔁 Enthalpy of vaporization — `calc_enthalpy_of_vaporization_at_temperature`
    - 🌡️↔️ Pressure → Saturation T — `calc_saturated_temperature_at_pressure`
    - 📈 Vapor pressure sensitivity dPvap/dT — `calc_vapor_pressure_sensitivity_at_temperature`
  - 🧮 Evaluate equation models (e.g., `VaPr`, `Cp_IG`) from the equation source (these may be `TableEquation` or other equation types).

- ⚙️ Quick notes
  - 📦 Most helper functions accept a `Component` object, a `model_source` (from `pyThermoLinkDB.load_and_build_model_source`), and typed `Temperature`/`Pressure` values.
  - 🔁 Modes like `'attach'`, `'log'`, and `'silent'` control return/log behavior — check the examples for usage patterns.

- 📘 Examples (runnable)
  - `examples/exp-2.py` — shows building a `ModelSource` and computing enthalpy and Gibbs formation properties (single temperature and ranges).
  - `examples/exp-3.py` — shows vapor/phase calculations: vapor pressure, enthalpy of vaporization, saturated temperature at pressure, sensitivity, and evaluating equation objects such as `VaPr` and `Cp_IG`.

Open the example files for complete, runnable workflows that demonstrate loading ThermoDB files, building the model source, and invoking the high-level calculation functions.

## 🤝 Contributing

Contributions are highly welcome — bug fixes, new calculation routines, mixture models, extended unit tests, documentation, etc.

## 📝 License

This project is distributed under the Apache License, Version 2.0, which grants you broad freedom to use, modify, and integrate the software into your own applications or projects, provided that you comply with the conditions outlined in the license. Although Apache 2.0 does not require users to retain explicit author credit beyond standard copyright and license notices, I kindly request that if you incorporate this work into your own software, you acknowledge Sina Gilassi as the original author. Referencing the original repository or documentation is appreciated, as it helps recognize the effort invested in developing and maintaining this project.

## ❓ FAQ

For any question, contact me on [LinkedIn](https://www.linkedin.com/in/sina-gilassi/)

## 👨‍💻 Authors

- [@sinagilassi](https://www.github.com/sinagilassi)
