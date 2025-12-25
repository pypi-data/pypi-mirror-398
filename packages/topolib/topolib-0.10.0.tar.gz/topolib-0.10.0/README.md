# Topolib 🚀

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)
[![Issues](https://img.shields.io/badge/issues-on%20GitLab-blue.svg)](https://gitlab.com/DaniloBorquez/topolib/-/issues)
[![Develop coverage](https://gitlab.com/DaniloBorquez/topolib/badges/develop/coverage.svg)](https://gitlab.com/DaniloBorquez/topolib/-/pipelines?ref=develop)
[![Documentation Status](https://readthedocs.org/projects/topolib/badge/?version=latest)](https://topolib.readthedocs.io/en/latest/?badge=latest)

> **Topolib** is a compact, modular Python library for modeling, analyzing, and visualizing optical network topologies.  
> **Goal:** Provide researchers and engineers with a simple, extensible toolkit for working with nodes, links, metrics, and map-based visualizations.  
>   
> 🌐 **Model** | 📊 **Analyze** | 🗺️ **Visualize** | 🧩 **Extend**

---

## 📂 Examples


Explore ready-to-run usage examples in the [`examples/`](examples/) folder!

- [Show topology on a map](examples/show_topology_in_map.py) 🗺️
- [Show default topology in map](examples/show_default_topology_in_map.py) 🗺️
- [Export topology as PNG](examples/export_topology_png.py) 🖼️
- [Export topology to CSV and JSON](examples/export_csv_json.py) 📄
- [Export topology and k-shortest paths for FlexNetSim](examples/export_flexnetsim.py) 🔀
- [Generate traffic demand matrices](examples/traffic_matrices.py) 📊
- [Generate multi-period traffic matrices with growth](examples/multiperiod_traffic_matrices.py) 📈

---

## 🧭 Overview

Topolib is organized into four main modules:

- 🧱 **Elements:** `Node`, `Link` — basic building blocks
- 🕸️ **Topology:** `Topology`, `Path` — manage nodes, links, paths, and adjacency
- 📈 **Analysis:** `Metrics`, `TrafficMatrix` — compute node degree, link stats, connection matrices, and traffic demand matrices
- 🖼️ **Visualization:** `MapView` — interactive maps with Folium and PyQt6, clean PNG exports

---

## ✨ Features

- Modular, extensible design
- Easy-to-use classes for nodes, links, and paths
- Built-in metrics and analysis helpers
- Traffic demand matrix generation with three models (gravitational, DC/IXP, distribution probability)
- Returns NumPy arrays for efficient mathematical operations
- Interactive map visualization with Folium and PyQt6
- Clean PNG export without external dependencies (no Selenium required)
- Resource caching for faster map rendering
- JSON import/export and interoperability
- Ready for Sphinx, Read the Docs, and PyPI

---

## ⚡ Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install topolib
```

---

## 📚 Documentation

Full documentation: [https://topolib.readthedocs.io/](https://topolib.readthedocs.io/)

---

## 📝 Basic usage

### Creating a topology

```python
from topolib.elements.node import Node
from topolib.topology.topology import Topology

n1 = Node(1, 'A', 10.0, 20.0)
n2 = Node(2, 'B', 11.0, 21.0)
topo = Topology(nodes=[n1, n2])
# Add links, compute metrics, visualize, etc.
```

### Generating traffic matrices

```python
from topolib.topology import Topology
from topolib.analysis import TrafficMatrix

# Load a topology
topo = Topology.load_default_topology("Germany-14nodes")

# Generate traffic matrix using gravitational model
matrix = TrafficMatrix.gravitational(topo, rate=0.015)
# Returns NumPy array: matrix[i, j] = traffic from node i to j (Gbps)

# Export to CSV
TrafficMatrix.to_csv(matrix, topo, "traffic_matrix.csv")

# Export to JSON (list of demands with src, dst, required fields)
TrafficMatrix.to_json(matrix, topo, "traffic_matrix.json")
```

---

## 🛠️ Development

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development guidelines, commit message rules, and pre-commit setup.

---

## 📄 License

MIT — see [`LICENSE`](LICENSE) for details.
