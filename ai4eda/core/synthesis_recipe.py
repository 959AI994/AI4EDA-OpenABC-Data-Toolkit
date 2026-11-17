#!/usr/bin/env python3
"""
Synthesis Recipe Generator
Generates ABC synthesis scripts for logic optimization
"""

import os
import math
import random
from pathlib import Path
from typing import List, Optional, Dict


# Stable GUALO token IDs: index + 1. Zero is reserved for padding.
GUALO_OPS = (
    'refactor', 'refactor -z', 'refactor -l', 'refactor -l -z',
    'rewrite', 'rewrite -z', 'rewrite -l', 'rewrite -l -z',
    'resub', 'resub -z', 'resub -l', 'resub -l -z', 'balance',
)


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
                                        max_ops: int = 8, *, distribution: str = 'uniform',
                                        min_ops: int = 3, mean: Optional[float] = None,
                                        std: Optional[float] = None, seed: Optional[int] = None,
                                        unique: bool = False, vocabulary: str = 'default') -> List[List[str]]:
        """
        Generate multiple random optimization sequences

        Args:
            num_sequences: Number of sequences to generate
            max_ops: Maximum operations per sequence
            distribution: 'uniform' (legacy default) or 'gaussian'. Gaussian
                lengths are drawn from N(mean,std), rejected outside [min,max],
                then rounded to the nearest integer (not clipped).
            min_ops: Minimum number of operations per recipe.
            mean, std: Gaussian parameters, default max_ops/2 and
                max(max_ops/4, 1). For a fixed length, mean defaults to that length.
            seed: Optional local RNG seed, independent of global RNG state.
            unique: Reject duplicate operation sequences.
            vocabulary: 'default' or the stable 13-action 'gualo' vocabulary.

        Returns:
            List of operation sequences
        """
        sequences = []
        available_ops = [
            'balance', 'rewrite', 'refactor', 'resub',
            'rewrite -z', 'refactor -z', 'resub -z',
            'resub -K 6', 'resub -K 8', 'resub -K 10'
        ]

        if distribution not in ('uniform', 'gaussian'):
            raise ValueError('Unknown sampling distribution')
        if vocabulary not in ('default', 'gualo'):
            raise ValueError('Unknown operation vocabulary')
        if num_sequences < 0 or min_ops < 1 or max_ops < min_ops:
            raise ValueError('Require count>=0 and 1<=min_ops<=max_ops')
        if vocabulary == 'gualo':
            available_ops = list(GUALO_OPS)
        if mean is None:
            mean = min_ops if min_ops == max_ops else max_ops / 2
        if std is None:
            std = max(max_ops / 4, 1)
        if distribution == 'gaussian' and (
            not math.isfinite(mean) or not math.isfinite(std)
            or std <= 0 or not min_ops <= mean <= max_ops
        ):
            raise ValueError('Gaussian mean must be inside bounds and std must be finite and positive')
        if unique and num_sequences > sum(
            len(available_ops) ** n for n in range(min_ops, max_ops + 1)
        ):
            raise ValueError('Requested more unique sequences than the vocabulary permits')
        rng = random.Random(seed) if seed is not None else random
        seen = set()
        # Bound both duplicate retries and Gaussian rejection attempts.
        budget = max(10000, num_sequences * 1000)
        attempts = 0
        while len(sequences) < num_sequences:
            attempts += 1
            if attempts > budget:
                raise ValueError('Sampling exhausted its attempt budget; relax the requested settings')
            if min_ops == max_ops:
                seq_length = min_ops
            elif distribution == 'uniform':
                seq_length = rng.randint(min_ops, max_ops)
            else:
                sample = rng.gauss(mean, std)
                if not min_ops <= sample <= max_ops:
                    continue
                seq_length = round(sample)
            sequence = tuple(rng.choice(available_ops) for _ in range(seq_length))
            if unique and sequence in seen:
                continue
            seen.add(sequence)
            sequences.append(list(sequence))

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
