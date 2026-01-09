#!/usr/bin/env python3
"""
Synthesis Recipe Generator
Generates ABC synthesis scripts for logic optimization
"""

import os
from pathlib import Path
from typing import List, Optional, Dict


class SynthesisRecipeGenerator:
    """Generate synthesis recipes (ABC scripts) for logic optimization"""

    # Common ABC optimization commands
    COMMON_OPS = [
        'balance',
        'rewrite',
        'refactor',
        'resub',
        'rewrite -z',
        'refactor -z',
        'resub -z',
        'balance'
    ]

    def __init__(self, lib_path: Optional[str] = None):
        """
        Initialize recipe generator

        Args:
            lib_path: Path to Liberty library file (optional)
        """
        self.lib_path = lib_path

    def generate_basic_recipe(self, input_file: str, output_file: str,
                             operations: Optional[List[str]] = None) -> str:
        """
        Generate a basic synthesis recipe

        Args:
            input_file: Input file path (.aig or .bench)
            output_file: Output file path
            operations: List of ABC operations to apply

        Returns:
            ABC script string
        """
        if operations is None:
            operations = self.COMMON_OPS

        # Determine read command based on input file type
        input_ext = Path(input_file).suffix
        if input_ext == '.aig':
            read_cmd = f'read_aiger {input_file}'
        elif input_ext == '.bench':
            read_cmd = f'read_bench {input_file}'
        else:
            read_cmd = f'read {input_file}'

        # Build script
        script_lines = [read_cmd]

        # Add library if specified
        if self.lib_path:
            script_lines.append(f'read_lib {self.lib_path}')

        # Add strash
        script_lines.append('strash')

        # Add operations
        script_lines.extend(operations)

        # Add output command
        output_ext = Path(output_file).suffix
        if output_ext == '.aig':
            script_lines.append(f'write_aiger {output_file}')
        elif output_ext == '.bench':
            script_lines.append(f'write_bench {output_file}')
        else:
            script_lines.append(f'write {output_file}')

        return '; '.join(script_lines)

    def generate_multi_step_recipe(self, input_file: str, output_dir: str,
                                   operations: List[str],
                                   save_intermediate: bool = True) -> str:
        """
        Generate recipe with intermediate step saving

        Args:
            input_file: Input file path
            output_dir: Directory for intermediate outputs
            operations: List of ABC operations
            save_intermediate: Whether to save intermediate results

        Returns:
            ABC script string
        """
        # Determine read command
        input_ext = Path(input_file).suffix
        if input_ext == '.aig':
            read_cmd = f'read_aiger {input_file}'
        elif input_ext == '.bench':
            read_cmd = f'read_bench {input_file}'
        else:
            read_cmd = f'read {input_file}'

        script_lines = [read_cmd]

        # Add library if specified
        if self.lib_path:
            script_lines.append(f'read_lib {self.lib_path}')

        # Add strash
        script_lines.append('strash')

        # Save initial state
        if save_intermediate:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            initial_output = output_path / 'step_0.bench'
            script_lines.append(f'write_bench {initial_output}')

        # Add operations with intermediate saves
        for i, op in enumerate(operations, 1):
            script_lines.append(op)
            if save_intermediate:
                step_output = output_path / f'step_{i}.bench'
                script_lines.append(f'write_bench {step_output}')

        return '; '.join(script_lines)

    def generate_optimization_sequences(self, num_sequences: int = 10,
                                        max_ops: int = 8) -> List[List[str]]:
        """
        Generate multiple random optimization sequences

        Args:
            num_sequences: Number of sequences to generate
            max_ops: Maximum operations per sequence

        Returns:
            List of operation sequences
        """
        import random

        sequences = []
        available_ops = [
            'balance', 'rewrite', 'refactor', 'resub',
            'rewrite -z', 'refactor -z', 'resub -z',
            'resub -K 6', 'resub -K 8', 'resub -K 10'
        ]

        for _ in range(num_sequences):
            seq_length = random.randint(3, max_ops)
            sequence = [random.choice(available_ops) for _ in range(seq_length)]
            sequences.append(sequence)

        return sequences

    def save_recipe_to_file(self, script: str, output_file: str):
        """
        Save recipe to a file

        Args:
            script: ABC script string
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            f.write(script)

    def generate_batch_recipes(self, design_names: List[str],
                               input_dir: str, output_dir: str,
                               num_recipes: int = 100) -> Dict[str, List[str]]:
        """
        Generate multiple recipes for multiple designs

        Args:
            design_names: List of design names
            input_dir: Input directory containing design files
            output_dir: Output directory for recipes
            num_recipes: Number of recipes per design

        Returns:
            Dictionary mapping design names to recipe file paths
        """
        recipe_files = {}

        for design_name in design_names:
            design_recipes = []

            # Find input file
            input_path = Path(input_dir)
            design_file = None
            for ext in ['.aig', '.bench', '.v']:
                potential_file = input_path / f'{design_name}{ext}'
                if potential_file.exists():
                    design_file = potential_file
                    break

            if design_file is None:
                continue

            # Generate recipes
            sequences = self.generate_optimization_sequences(num_recipes)

            for i, operations in enumerate(sequences):
                # Create recipe
                recipe_dir = Path(output_dir) / design_name
                recipe_dir.mkdir(parents=True, exist_ok=True)
                recipe_file = recipe_dir / f'recipe_{i}.script'

                # Generate script
                output_bench = recipe_dir / f'{design_name}_opt_{i}.bench'
                script = self.generate_basic_recipe(
                    str(design_file),
                    str(output_bench),
                    operations
                )

                # Save
                self.save_recipe_to_file(script, str(recipe_file))
                design_recipes.append(str(recipe_file))

            recipe_files[design_name] = design_recipes

        return recipe_files


def generate_synthesis_recipe(input_file: str, output_file: str,
                              operations: Optional[List[str]] = None,
                              lib_path: Optional[str] = None) -> str:
    """
    Convenience function to generate a synthesis recipe

    Args:
        input_file: Input file path
        output_file: Output file path
        operations: List of ABC operations
        lib_path: Optional Liberty library path

    Returns:
        ABC script string
    """
    generator = SynthesisRecipeGenerator(lib_path)
    return generator.generate_basic_recipe(input_file, output_file, operations)
