# Binary Tools Directory

This directory should contain the compiled binary tools required by the toolkit.

## Required Tools

You need to compile and place the following tools in this directory:

- **`abc`** - ABC synthesis tool
- **`yosys`** - Yosys synthesis tool (from Yosys project)
- **`yosys-abc`** - Yosys-ABC tool (from Yosys project, optional)

## Installation Instructions

### Option 1: Compile from Source

#### ABC Tool

```bash
git clone https://github.com/berkeley-abc/abc.git
cd abc
```

**⚠️ Important: ABC Source Code Modification Required**

Before compiling ABC, you need to modify the `write_bench` function in ABC's source code to ensure it outputs in **BENCH format** instead of **LUT format**. 

The `write_bench` function is typically located in `abc/src/base/io/ioWriteBenc.c`. You need to modify the function to output standard BENCH format (gate-level netlist) rather than LUT format.

**Step 1: Locate the file**
```bash
cd abc/src/base/io
vim ioWriteBenc.c  # or use your preferred editor
```

**Step 2: Find the `write_bench` function**

Search for the function definition:
```c
int Abc_WriteBench( ... )
```

**Step 3: Modify the format selection**

In the `write_bench` function, you'll typically find code that determines whether to output in LUT format or BENCH format. Look for conditional statements or format flags. You need to modify it to always use BENCH format.

**Example modification pattern** (the exact code may vary depending on ABC version):

Look for code similar to this pattern:

```c
// BEFORE (may output LUT format):
int fLut = 0;  // or similar flag variable
// ... some code that sets fLut based on conditions ...

if ( fLut ) {
    // LUT format output code (using Abc_NodeIsLut or similar functions)
    // This section outputs LUT primitives
} else {
    // BENCH format output code (gate-level netlist)
    // This section outputs gates like AND, OR, NOT, etc.
}

// AFTER (force BENCH format):
int fLut = 0;  // Force to 0 to always use BENCH format
// Comment out or remove code that sets fLut = 1
// fLut = 1;  // <- Comment this out

if ( 0 ) {  // Always false, so LUT section is skipped
    // LUT format output code (will not execute)
} else {
    // BENCH format output code (always executes)
}
```

Or alternatively:

```c
// BEFORE:
if ( /* condition that might be true for LUT */ ) {
    // LUT output
} else {
    // BENCH output
}

// AFTER:
// Force BENCH format by changing the condition to always be false
if ( 0 ) {  // Always false
    // LUT output (never executes)
} else {
    // BENCH output (always executes)
}
```

**What to look for:**
- Variables named `fLut`, `fBench`, `format`, `Format`, `pFormat`, or similar
- Function calls like `Abc_NodeIsLut()`, `Abc_NtkHasLut()`, or similar that check for LUT format
- Conditional statements (`if`, `switch`) that select between formats
- Comments mentioning "LUT", "lut", "bench", "BENCH", or format selection

**The key modification:** Ensure the code path that writes standard gate-level BENCH format (AND, OR, NOT gates) is always executed, and skip the LUT format code path.

**Step 4: Verify the modification**

After modification, ensure the function will output gate-level BENCH format (with gates like AND, OR, NOT, etc.) instead of LUT format (with LUT primitives).

**Step 5: Compile ABC**

After making the modification:
```bash
cd abc  # Make sure you're in the ABC root directory
make
cp abc /path/to/AI4EDA-OpenABC-Data-Toolkit/bin/
```

**Step 6: Test the modification**

Verify that `write_bench` outputs BENCH format:
```bash
./bin/abc -c "read_aiger test.aig; write_bench test.bench; quit"
cat test.bench  # Should show gate-level netlist (AND, OR, NOT), not LUT format
```

#### Yosys Tool

```bash
git clone https://github.com/YosysHQ/yosys.git
cd yosys
make
cp yosys /path/to/AI4EDA-OpenABC-Data-Toolkit/bin/
```

#### Yosys-ABC Tool (Optional)

```bash
git clone https://github.com/YosysHQ/yosys.git
cd yosys
make
cp yosys-abc /path/to/AI4EDA-OpenABC-Data-Toolkit/bin/
```

### Option 2: Use System Installed Tools

If you have ABC and Yosys installed system-wide, the toolkit will automatically fall back to using them if the binaries are not found in this directory.

## Verification

After placing the binaries, verify they work:

```bash
./bin/abc -h
./bin/yosys --version
./bin/yosys-abc -h
```

Or test with the toolkit:

```bash
ai4eda convert verilog2aig test_data/verilog/test.v test_output.aig
```