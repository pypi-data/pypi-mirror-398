# dayhoff-tools

A set of small, sharp tools for everyone at Dayhoff. Hosted on PyPi, so you can Poetry or pip install like everything else.

## Installation

The base package includes minimal dependencies required for core CLI functionality (like job running):

```bash
pip install dayhoff-tools
# or
uv add dayhoff-tools
# or, for the special case of installing it in the DHT repo itself,
uv pip install -e .[full]
```

### Optional Dependencies

You can install extra sets of dependencies using brackets. Available groups are:

* `core`: Includes common data science and bioinformatics tools (`biopython`, `boto3`, `docker`, `fair-esm`, `h5py`, `questionary`).
* `dev`: Includes development and testing tools (`black`, `pytest`, `pandas`, `numpy`, `torch`, etc.).
* `all`: Includes all dependencies from both `core` and `dev`.

**Examples:**

```bash
# Install with core dependencies
pip install 'dayhoff-tools[core]'
poetry add 'dayhoff-tools[core]'

# Install with all dependencies
pip install 'dayhoff-tools[all]'
poetry add 'dayhoff-tools[all]'
```