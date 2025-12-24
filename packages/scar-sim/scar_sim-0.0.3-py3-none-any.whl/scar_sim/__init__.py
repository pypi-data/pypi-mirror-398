"""
# SCAR SIM
[![PyPI version](https://badge.fury.io/py/scar_sim.svg)](https://badge.fury.io/py/scar_sim)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Supply Chain Adaptation and Resilience Simulator

# Setup

Make sure you have Python 3.11.x (or higher) installed on your system. You can download it [here](https://www.python.org/downloads/).

## Installation

```
pip install scar_sim
```

## Getting Started

- [Docs](https://connor-makowski.github.io/scar_sim/scar_sim.html)
- [Git](https://github.com/connor-makowski/scar_sim)

### Basic Example

```py
from scar_sim.entity import Arc, Node
from scar_sim.order import Order
from scar_sim.simulation import Simulation


simulation = Simulation()

# Create nodes
supplier_0 = simulation.add_object(
    Node(
        processing_min_time=0.8,
        processing_avg_time=1.0,
        processing_sd_time=0.02,
        processing_cashflow_per_unit=-50,
        metadata={
            "loc": "cn_ningbo",
            "otype": "node_supplier",
        },
    )
)
factory_1 = simulation.add_object(
    Node(
        processing_min_time=0.2,
        processing_avg_time=0.4,
        processing_sd_time=0.1,
        processing_cashflow_per_unit=-15,
        metadata={
            "loc": "us_ks_kc",
            "otype": "node_factory",
        },
    )
)

# Create arcs between nodes
arc_0_1 = simulation.add_object(
    Arc(
        origin_node=supplier_0,
        destination_node=factory_1,
        processing_min_time=2.0,
        processing_avg_time=2.0,
        processing_sd_time=0.05,
        processing_cashflow_per_unit=-10,
        metadata={
            "loc": "oc_pa",
            "otype": "arc_ocean",
        },
    )
)

order = simulation.add_object(
    Order(
        origin_node=supplier_0,
        destination_node=factory_1,
        units=1,
        planned_path=simulation.graph.get_optimal_path(
            supplier_0, factory_1, "cashflow"
        ),
    )
)

simulation.add_event(
    time_delta=0.0,
    func=order.start,
)

simulation.run(max_time=10.0)

print(simulation.orders[0].history[-1]) #=>
# {
#     'time': 2.9971,
#     'time_delta': 0.0,
#     'order_id': 3,
#     'current_obj_id': 1,
#     'meta': {
#         'loc': 'us_ks_kc',
#         'otype': 'node_factory',
#         'time': 2
#     },
#     'status': 'completed',
#     'cashflow': 0.0
# }

```

## Development

To avoid extra development overhead, we expect all developers to use a unix based environment (Linux or Mac). If you use Windows, please use WSL2.

For development, we test using Docker so we can lock system deps and swap out python versions easily. However, you can also use a virtual environment if you prefer. We provide a test script and a prettify script to help with development.

## Making Changes

1) Fork the repo and clone it locally.
2) Make your modifications.
3) Use Docker or a virtual environment to run tests and make sure they pass.
4) Prettify your code.
5) **DO NOT GENERATE DOCS**.
    - We will generate the docs and update the version number when we are ready to release a new version.
6) Only commit relevant changes and add clear commit messages.
    - Atomic commits are preferred.
7) Submit a pull request.

## Docker

Make sure Docker is installed and running.

- Create a docker container and drop into a shell
    - `./run.sh`
- Run all tests (see ./utils/test.sh)
    - `./run.sh test`
- Prettify the code (see ./utils/prettify.sh)
    - `./run.sh prettify`

- Note: You can and should modify the `Dockerfile` to test different python versions.

## Virtual Environment

- Create a virtual environment
    - `python3.XX -m venv venv`
        - Replace `3.XX` with your python version (3.11 or higher)
- Activate the virtual environment
    - `source venv/bin/activate`
- Install the development requirements
    - `pip install -r requirements/dev.txt`
- Run Tests
    - `./utils/test.sh`
- Prettify Code
    - `./utils/prettify.sh`"""

