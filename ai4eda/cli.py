#!/usr/bin/env python3
"""
AI4EDA Data Toolkit - Command Line Interface
Main entry point for the toolkit
"""

import sys
import argparse
from pathlib import Path

# Version info
__version__ = "0.1.0"


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        prog='ai4eda',
        description='AI4EDA Data Toolkit - EDA data processing and format conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert AIG to BENCH
  ai4eda convert aig2bench input.aig output.bench

  # Convert BENCH to GraphML
  ai4eda convert bench2graphml input.bench output.graphml

  # Convert GraphML to PyTorch Geometric
  ai4eda convert graphml2pt input.graphml output.pt

  # Convert Verilog to AIG
  ai4eda convert verilog2aig input.v output.aig

  # Calculate metrics (area/delay)
  ai4eda metrics input.aig --lib asap7.lib

  # Generate synthesis recipes
  ai4eda recipe generate input.aig output_dir --num-recipes 10
        """
    )

    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Format conversion')
    convert_subparsers = convert_parser.add_subparsers(dest='conversion', help='Conversion type')

    # AIG to BENCH
    aig2bench_parser = convert_subparsers.add_parser('aig2bench', help='Convert AIG to BENCH')
    aig2bench_parser.add_argument('input', help='Input .aig file or directory')
    aig2bench_parser.add_argument('output', help='Output .bench file or directory')
    aig2bench_parser.add_argument('--abc-path', help='Path to ABC executable')
    aig2bench_parser.add_argument('--batch', action='store_true', help='Batch convert directory')
    aig2bench_parser.add_argument('--recursive', action='store_true', help='Recursively search subdirectories')

    # BENCH to GraphML
    bench2graphml_parser = convert_subparsers.add_parser('bench2graphml', help='Convert BENCH to GraphML')
    bench2graphml_parser.add_argument('input', help='Input .bench file or directory')
    bench2graphml_parser.add_argument('output', help='Output .graphml file or directory')
    bench2graphml_parser.add_argument('--batch', action='store_true', help='Batch convert directory')
    bench2graphml_parser.add_argument('--recursive', action='store_true', help='Recursively search subdirectories')

    # GraphML to PT
    graphml2pt_parser = convert_subparsers.add_parser('graphml2pt', help='Convert GraphML to PyTorch Geometric')
    graphml2pt_parser.add_argument('input', help='Input .graphml file or directory')
    graphml2pt_parser.add_argument('output', help='Output .pt file or directory')
    graphml2pt_parser.add_argument('--batch', action='store_true', help='Batch convert directory')
    graphml2pt_parser.add_argument('--recursive', action='store_true', help='Recursively search subdirectories')

    # Verilog to AIG
    verilog2aig_parser = convert_subparsers.add_parser('verilog2aig', help='Convert Verilog to AIG')
    verilog2aig_parser.add_argument('input', help='Input .v file or directory')
    verilog2aig_parser.add_argument('output', help='Output .aig file or directory')
    verilog2aig_parser.add_argument('--yosys-abc-path', help='Path to yosys-abc executable')
    verilog2aig_parser.add_argument('--top-module', help='Top module name')
    verilog2aig_parser.add_argument('--batch', action='store_true', help='Batch convert directory')
    verilog2aig_parser.add_argument('--recursive', action='store_true', help='Recursively search subdirectories')

    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Calculate area and delay metrics')
    metrics_parser.add_argument('input', help='Input .aig or .bench file')
    metrics_parser.add_argument('--lib', required=True, help='Liberty library file')
    metrics_parser.add_argument('--abc-path', help='Path to ABC executable')
    metrics_parser.add_argument('--opt-script', default='', help='ABC optimization script')
    metrics_parser.add_argument('--batch', action='store_true', help='Batch process directory')

    # Recipe command
    recipe_parser = subparsers.add_parser('recipe', help='Synthesis recipe operations')
    recipe_subparsers = recipe_parser.add_subparsers(dest='recipe_cmd', help='Recipe command')

    # Generate recipe
    recipe_gen_parser = recipe_subparsers.add_parser('generate', help='Generate synthesis recipes')
    recipe_gen_parser.add_argument('input', help='Input file')
    recipe_gen_parser.add_argument('output_dir', help='Output directory for recipes')
    recipe_gen_parser.add_argument('--num-recipes', type=int, default=10, help='Number of recipes to generate')
    recipe_gen_parser.add_argument('--lib', help='Liberty library file')

    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Handle commands
    if args.command == 'convert':
        handle_convert(args)
    elif args.command == 'metrics':
        handle_metrics(args)
    elif args.command == 'recipe':
        handle_recipe(args)
    else:
        parser.print_help()
        sys.exit(1)


def handle_convert(args):
    """Handle conversion commands"""
    if args.conversion == 'aig2bench':
        from ai4eda.converters.aig_to_bench import AigToBenchConverter
        converter = AigToBenchConverter(args.abc_path)

        if args.batch or Path(args.input).is_dir():
            print(f"Converting AIG files in {args.input} to BENCH...")
            stats = converter.convert_batch(args.input, args.output, args.recursive)
            print(f"Total: {stats['total']}, Success: {stats['success']}, Failed: {stats['failed']}")
        else:
            print(f"Converting {args.input} to {args.output}...")
            success, msg = converter.convert(args.input, args.output)
            print(f"{'Success' if success else 'Failed'}: {msg}")

    elif args.conversion == 'bench2graphml':
        from ai4eda.converters.bench_to_graphml import BenchToGraphMLConverter
        converter = BenchToGraphMLConverter()

        if args.batch or Path(args.input).is_dir():
            print(f"Converting BENCH files in {args.input} to GraphML...")
            stats = converter.convert_batch(args.input, args.output, args.recursive)
            print(f"Total: {stats['total']}, Success: {stats['success']}, Failed: {stats['failed']}")
        else:
            print(f"Converting {args.input} to {args.output}...")
            success, msg = converter.convert(args.input, args.output)
            print(f"{'Success' if success else 'Failed'}: {msg}")

    elif args.conversion == 'graphml2pt':
        from ai4eda.converters.graphml_to_pt import GraphMLToPTConverter
        converter = GraphMLToPTConverter()

        if args.batch or Path(args.input).is_dir():
            print(f"Converting GraphML files in {args.input} to PT...")
            stats = converter.convert_batch(args.input, args.output, args.recursive)
            print(f"Total: {stats['total']}, Success: {stats['success']}, Failed: {stats['failed']}")
        else:
            print(f"Converting {args.input} to {args.output}...")
            success, msg = converter.convert(args.input, args.output)
            print(f"{'Success' if success else 'Failed'}: {msg}")

    elif args.conversion == 'verilog2aig':
        from ai4eda.converters.verilog_to_aig import VerilogToAigConverter
        converter = VerilogToAigConverter(args.yosys_abc_path)

        if args.batch or Path(args.input).is_dir():
            print(f"Converting Verilog files in {args.input} to AIG...")
            stats = converter.convert_batch(args.input, args.output, args.recursive)
            print(f"Total: {stats['total']}, Success: {stats['success']}, Failed: {stats['failed']}")
        else:
            print(f"Converting {args.input} to {args.output}...")
            success, msg = converter.convert(args.input, args.output, args.top_module)
            print(f"{'Success' if success else 'Failed'}: {msg}")


def handle_metrics(args):
    """Handle metrics calculation"""
    from ai4eda.core.metrics import MetricsCalculator

    calculator = MetricsCalculator(args.lib, args.abc_path)

    if args.batch or Path(args.input).is_dir():
        print(f"Calculating metrics for files in {args.input}...")
        # Determine file pattern
        file_pattern = "*.aig" if Path(args.input).glob("*.aig") else "*.bench"
        stats = calculator.calculate_batch(args.input, file_pattern, args.opt_script)
        print(f"Total: {stats['total']}, Success: {stats['success']}, Failed: {stats['failed']}")
        for metric in stats['metrics'][:10]:  # Show first 10
            print(f"  {Path(metric['file']).name}: Area={metric['area']:.2f}, Delay={metric['delay']:.2f}")
    else:
        print(f"Calculating metrics for {args.input}...")
        file_ext = Path(args.input).suffix
        if file_ext == '.aig':
            area, delay, msg = calculator.calculate_from_aig(args.input, args.opt_script)
        else:
            area, delay, msg = calculator.calculate_from_bench(args.input, args.opt_script)

        if area is not None and delay is not None:
            print(f"Success - Area: {area:.2f}, Delay: {delay:.2f}")
        else:
            print(f"Failed: {msg}")


def handle_recipe(args):
    """Handle recipe generation"""
    from ai4eda.core.synthesis_recipe import SynthesisRecipeGenerator

    if args.recipe_cmd == 'generate':
        generator = SynthesisRecipeGenerator(args.lib)
        print(f"Generating {args.num_recipes} synthesis recipes...")

        sequences = generator.generate_optimization_sequences(args.num_recipes)

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, operations in enumerate(sequences):
            recipe_file = output_dir / f'recipe_{i}.script'
            output_file = output_dir / f'output_{i}.bench'
            script = generator.generate_basic_recipe(args.input, str(output_file), operations)
            generator.save_recipe_to_file(script, str(recipe_file))

        print(f"Generated {args.num_recipes} recipes in {args.output_dir}")


if __name__ == '__main__':
    main()
