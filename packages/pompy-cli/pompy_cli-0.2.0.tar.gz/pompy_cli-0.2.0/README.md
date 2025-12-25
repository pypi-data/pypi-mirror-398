# pompy-cli
A barebones CLI utility package for Python, for making interactive programs on the terminal.

## Installation

```bash
pip install pompy-cli
```

## Usage

More detailed documentation later.  
For now, you can check the `demo_basic.py` and `demo_context.py` to see what you can do with pompy_cli.


## Requirements

- Python >= 3.8

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/pompyproductions/pompy-cli.git
cd pompy-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e . 

# Install dev dependencies (optional)
pip install -r requirements-dev.txt
```

### Building

```bash
python -m build
```

### Publishing

```bash
twine upload dist/*
```

## License

GNU GPLv3.0

## Links

- PyPI: https://pypi.org/project/pompy-cli/
- GitHub: https://github.com/pompyproductions/pompy-cli
- Issues: https://github.com/pompyproductions/pompy-cli/issues
```