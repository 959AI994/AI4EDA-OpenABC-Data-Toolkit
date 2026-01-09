# Binary Tools Directory

This directory should contain the compiled binary tools required by the toolkit.

## Required Tools

You need to compile and place the following tools in this directory:

- **`abc`** - ABC synthesis tool
- **`yosys-abc`** - Yosys-ABC tool (from Yosys project)

## Installation Instructions

### Option 1: Compile from Source

#### ABC Tool

```bash
git clone https://github.com/berkeley-abc/abc.git
cd abc
make
cp abc /path/to/AI4EDA-OpenABC-Data-Toolkit/bin/
```

#### Yosys-ABC Tool

```bash
git clone https://github.com/YosysHQ/yosys.git
cd yosys
make
cp yosys-abc /path/to/AI4EDA-OpenABC-Data-Toolkit/bin/
```

### Option 2: Use System Installed Tools

If you have ABC and Yosys-ABC installed system-wide, the toolkit will automatically fall back to using them if the binaries are not found in this directory.

## Verification

After placing the binaries, verify they work:

```bash
./bin/abc -h
./bin/yosys-abc -h
```

Or test with the toolkit:

```bash
ai4eda convert verilog2aig test_data/verilog/test.v test_output.aig
```