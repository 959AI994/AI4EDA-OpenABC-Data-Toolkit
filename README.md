# AI4EDA Data Toolkit

A comprehensive open-source toolkit for EDA (Electronic Design Automation) data processing and format conversion, specifically designed for AI4EDA applications.

## Features

- **Format Conversion**
  - AIG to BENCH conversion
  - BENCH to GraphML conversion
  - GraphML to PyTorch Geometric (.pt) conversion
  - Verilog to AIG conversion

- **Metrics Calculation**
  - Area and delay computation using Liberty libraries
  - Support for custom ABC optimization scripts

- **Synthesis Recipe Generation**
  - Automatic generation of synthesis optimization sequences
  - Customizable optimization strategies

- **PyTorch Geometric Compatibility**
  - Cross-version PyG data loading
  - Compatible with both old and new PyG formats

## Installation

### Prerequisites

- Python 3.7+
- NetworkX
- PyTorch
- PyTorch Geometric

### Install from source

```bash
git clone https://github.com/your-org/AI4EDA-OpenABC-Data-Toolkit.git
cd AI4EDA-OpenABC-Data-Toolkit
pip install -r requirements.txt
pip install -e .
```

## Project Structure

```
AI4EDA-OpenABC-Data-Toolkit/
├── ai4eda/                    # Main package
│   ├── converters/            # Format converters
│   │   ├── aig_to_bench.py
│   │   ├── bench_to_graphml.py
│   │   ├── graphml_to_pt.py
│   │   └── verilog_to_aig.py
│   ├── core/                  # Core functionality
│   │   ├── metrics.py         # Area/delay calculation
│   │   └── synthesis_recipe.py
│   ├── utils/                 # Utilities
│   │   └── pyg_loader.py      # PyG compatibility loader
│   └── cli.py                 # Command-line interface
├── bin/                       # Binary tools
│   ├── abc                    # ABC synthesis tool
│   └── yosys-abc              # Yosys-ABC tool
├── libs/                      # Liberty libraries
│   └── asap7.lib              # ASAP7 library
├── test_data/                 # Test data
│   ├── aig/                   # Sample AIG files
│   ├── verilog/               # Sample Verilog files
│   ├── bench/                 # Generated BENCH files
│   ├── graphml/               # Generated GraphML files
│   └── pt/                    # Generated PT files
└── ai4eda-toolkit             # Main executable script
```

## Usage

### Command-line Interface

The toolkit provides a unified command-line interface:

```bash
ai4eda <command> <subcommand> [options]
```

Or use the direct script:

```bash
./ai4eda-toolkit <command> <subcommand> [options]
```

### Format Conversion

#### AIG to BENCH

Convert a single file:
```bash
ai4eda convert aig2bench input.aig output.bench
```

Batch convert a directory:
```bash
ai4eda convert aig2bench input_dir/ output_dir/ --batch --recursive
```

#### BENCH to GraphML

Convert a single file:
```bash
ai4eda convert bench2graphml input.bench output.graphml
```

Batch convert:
```bash
ai4eda convert bench2graphml input_dir/ output_dir/ --batch --recursive
```

#### GraphML to PyTorch Geometric

Convert a single file:
```bash
ai4eda convert graphml2pt input.graphml output.pt
```

Batch convert:
```bash
ai4eda convert graphml2pt input_dir/ output_dir/ --batch --recursive
```

#### Verilog to AIG

Convert a single file:
```bash
ai4eda convert verilog2aig input.v output.aig
```

With top module specification:
```bash
ai4eda convert verilog2aig input.v output.aig --top-module my_module
```

### Metrics Calculation

Calculate area and delay for an AIG file:
```bash
ai4eda metrics input.aig --lib libs/asap7.lib
```

With custom optimization script:
```bash
ai4eda metrics input.aig --lib libs/asap7.lib --opt-script "balance; rewrite; refactor"
```

Batch process:
```bash
ai4eda metrics input_dir/ --lib libs/asap7.lib --batch
```

### Synthesis Recipe Generation

Generate synthesis recipes:
```bash
ai4eda recipe generate input.aig output_dir/ --num-recipes 100
```

With Liberty library:
```bash
ai4eda recipe generate input.aig output_dir/ --num-recipes 100 --lib libs/asap7.lib
```

## Python API

You can also use the toolkit as a Python library:

### Format Conversion

```python
from ai4eda.converters.aig_to_bench import convert_aig_to_bench
from ai4eda.converters.bench_to_graphml import convert_bench_to_graphml
from ai4eda.converters.graphml_to_pt import convert_graphml_to_pt

# Convert AIG to BENCH
success, msg = convert_aig_to_bench("input.aig", "output.bench")

# Convert BENCH to GraphML
success, msg = convert_bench_to_graphml("input.bench", "output.graphml")

# Convert GraphML to PT
success, msg = convert_graphml_to_pt("input.graphml", "output.pt")
```

### Metrics Calculation

```python
from ai4eda.core.metrics import calculate_metrics

# Calculate area and delay
area, delay, msg = calculate_metrics(
    "design.aig",
    lib_path="libs/asap7.lib",
    opt_script="balance; rewrite"
)
print(f"Area: {area}, Delay: {delay}")
```

### PyG Data Loading (Cross-version Compatible)

```python
from ai4eda.utils.pyg_loader import load_pyg_data_compatible, extract_pyg_attr

# Load PyG data (works with old and new PyG versions)
data = load_pyg_data_compatible("graph.pt")

# Extract specific attributes safely
edge_index = extract_pyg_attr(data, 'edge_index')
node_type = extract_pyg_attr(data, 'node_type')
```

## Testing

Run the example workflow:

```bash
# 1. Convert AIG to BENCH
./ai4eda-toolkit convert aig2bench test_data/aig/div.aig test_data/bench/div.bench

# 2. Convert BENCH to GraphML
./ai4eda-toolkit convert bench2graphml test_data/bench/div.bench test_data/graphml/div.graphml

# 3. Convert GraphML to PT
./ai4eda-toolkit convert graphml2pt test_data/graphml/div.graphml test_data/pt/div.pt

# 4. Calculate metrics
./ai4eda-toolkit metrics test_data/aig/div.aig --lib libs/asap7.lib

# 5. Generate synthesis recipes
./ai4eda-toolkit recipe generate test_data/aig/div.aig test_data/recipes --num-recipes 10
```

## Advanced Features

### PyTorch Geometric Version Compatibility

The toolkit automatically handles PyG version differences:

```python
from ai4eda.utils.pyg_loader import load_pyg_data_compatible

# This works regardless of PyG version
data = load_pyg_data_compatible("old_format.pt")
data_new = load_pyg_data_compatible("new_format.pt")
```

### Batch Processing

All conversion tools support batch processing:

```python
from ai4eda.converters.aig_to_bench import AigToBenchConverter

converter = AigToBenchConverter()
stats = converter.convert_batch(
    input_dir="designs/aig/",
    output_dir="designs/bench/",
    recursive=True
)
print(f"Converted {stats['success']}/{stats['total']} files")
```

## Tools Included

- **ABC**: Berkeley ABC synthesis tool (v1.0)
- **Yosys-ABC**: Yosys integrated ABC tool
- **ASAP7 Library**: 7nm ASAP library for technology mapping

## Directory Structure for Data

Recommended directory structure for your data:

```
your_project/
├── raw/
│   ├── verilog/          # Original Verilog files
│   └── aig/              # AIG files
├── processed/
│   ├── bench/            # BENCH format
│   ├── graphml/          # GraphML format
│   └── pt/               # PyTorch Geometric format
├── recipes/              # Synthesis recipes
└── metrics/              # Calculated metrics
```

## Performance Tips

1. **Batch Processing**: Use `--batch` flag for processing multiple files
2. **Recursive Search**: Use `--recursive` to process nested directories
3. **Timeout Settings**: Adjust timeout for large designs in Python API
4. **Parallel Processing**: The toolkit uses efficient parallel processing for batch operations

## Troubleshooting

### ABC Tool Not Found

Make sure the ABC binary is in the `bin/` directory or specify path:
```bash
ai4eda convert aig2bench input.aig output.bench --abc-path /path/to/abc
```

### PyTorch Geometric Import Error

Install PyG following official instructions:
```bash
pip install torch-geometric
```

### Liberty Library Issues

Ensure the liberty file exists:
```bash
ls libs/asap7.lib
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

MIT License

## Citation

If you use this toolkit in your research, please cite:

```bibtex
@software{ai4eda_toolkit,
  title={AI4EDA Data Toolkit},
  author={AI4EDA Team},
  year={2026},
  url={https://github.com/your-org/AI4EDA-OpenABC-Data-Toolkit}
}
```

## Acknowledgments

- Berkeley ABC team for the ABC synthesis tool
- YosysHQ for Yosys-ABC integration
- PyTorch Geometric team for the graph learning framework
- OpenABC project for dataset inspiration

## Contact

For questions and feedback, please open an issue on GitHub.

---

**Note**: This toolkit is designed for research and educational purposes. For production use, please ensure proper testing and validation.
