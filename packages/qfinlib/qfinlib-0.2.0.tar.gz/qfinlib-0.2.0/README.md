# qfinlib

A comprehensive quantitative finance library for Python.

## Disclaimer

This repository contains personal, educational research only. It is not related to any professional role, employer, or investment activity. All material is based on public information.

## Overview

qfinlib provides a complete toolkit for quantitative finance, including:

- **Date handling**: Serial dates, tenors, schedules, holiday calendars, day count fractions
- **Mathematical utilities**: Interpolation, solvers, statistics, auto-differentiation
- **Market data**: Curves, FX, rates, volatility, credit, inflation, bonds
- **Financial instruments**: Swaps, bonds, FRA, futures, options, CDS, FX forwards, deposits, ZCIS
- **Valuation**: Pricing engines for all instrument types
- **Risk analytics**: PV, DV01, gamma, theta, carry/roll, scenario analysis
- **Calibration**: Curve and volatility model calibration
- **Models**: Interest rate models (LGM, Hull-White)

## Installation

```bash
pip install qfinlib
```

## Quick Start

```python
import qfinlib as qf

# Example usage coming soon
```

## Documentation

See the `docs/` directory for detailed documentation and tutorials.

## Development

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for development guidelines.

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:
- Tests run automatically on pull requests
- Package is automatically published to PyPI when merged to `main`

See [.github/CI_SETUP.md](.github/CI_SETUP.md) for CI/CD setup instructions.

## License

MIT License

