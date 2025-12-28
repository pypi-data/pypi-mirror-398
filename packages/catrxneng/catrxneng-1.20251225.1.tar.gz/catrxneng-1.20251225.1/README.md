# cat-rxn-eng

A Python library for modeling catalysts, simulating reactors, and optimizing catalytic processes.

## Overview

`cat-rxn-eng` is a comprehensive toolkit for modeling, simulating, and analyzing catalytic reaction systems. It provides utilities for thermodynamic calculations, kinetic modeling, reactor simulations, and data analysis across a range of catalytic processes including CO₂ conversion, methanol synthesis, reverse water-gas shift reactions, and multi-phase transformations.

## Features

- **Kinetic Modeling**: Tools for power-law, Langmuir-Hinshelwood, and dual-site kinetic models
- **Reactor Simulation**: Support for plug flow reactors (PFR) and other reactor types
- **Thermodynamic Calculations**: Equilibrium and property calculations for chemical species
- **Material Properties**: Catalyst and support material characterization
- **Data Analysis**: Plotting and analysis utilities for experimental and simulated data
- **Configuration Management**: Organized configuration system for reaction parameters

## Installation

### From Git

```bash
git clone https://github.com/gpbrez/cat-rxn-eng.git
cd cat-rxn-eng
pip install -e .
```

### Dependencies

- `numpy` - Numerical computations
- `scipy` - Scientific computing
- `pandas` - Data manipulation and analysis
- `matplotlib` - Plotting and visualization
- `plotly` - Interactive visualizations
- `influxdb-client` - Time-series data logging (optional)
- `requests` - HTTP library

## Project Structure

```
cat-rxn-eng/
├── kinetic_models/     # Kinetic rate law models and fitting
├── reactors/          # Reactor types and simulations (PFR, etc.)
├── species/           # Chemical species properties and thermodynamics
├── quantities/        # Unit-aware quantities and conversions
├── reactions/         # Reaction definitions and stoichiometry
├── simulate/          # High-level simulation interfaces
├── material/          # Catalyst and material properties
├── plots/             # Plotting utilities
├── utils/             # General utilities
└── conf/              # Configuration management
```

## Usage Examples

### Basic Kinetic Modeling

```python
from cat_rxn_eng import kinetic_models

# Define and fit power-law kinetic models
model = kinetic_models.PowerLawModel(...)
fitted_params = model.fit(experimental_data)
```

### Reactor Simulation

```python
from cat_rxn_eng import simulate, reactors

# Simulate a plug flow reactor
pfr = reactors.PlugFlowReactor(...)
results = simulate.run_pfr_simulation(pfr, feed_conditions)
```

### Thermodynamic Calculations

```python
from cat_rxn_eng import species

# Get thermodynamic properties
co2 = species.Species('CO2')
h2 = species.Species('H2')
equilibrium = species.calculate_equilibrium([co2, h2])
```

## Applications

This toolkit has been used for research on:

- **CO₂ to Methanol Synthesis**: Kinetic modeling and process optimization
- **Reverse Water-Gas Shift (RWGS)**: Reaction characterization and conversion studies
- **Tandem Catalytic Reactions**: Combined CO₂ conversion and transformations
- **Methanol-to-Olefins (MTO)**: Kinetic analysis and process simulation
- **Catalytic Validation**: Validation of literature kinetic models against experimental data

## Documentation

Documentation is provided through:

- Jupyter notebooks in `nb-*` directories for application examples
- Inline docstrings throughout the package
- Example scripts in the `scripts/` directory

## License

MIT License - see LICENSE file for details

## Author

Gordon Brezicki
