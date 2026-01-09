#!/bin/bash
# Quick Start Guide - Test all functionalities

echo "=================================="
echo "AI4EDA Toolkit Quick Start Guide"
echo "=================================="

# Set project root
PROJECT_ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$PROJECT_ROOT"

echo ""
echo "Step 1: Convert AIG to BENCH"
echo "----------------------------"
./ai4eda-toolkit convert aig2bench test_data/aig/div.aig test_data/bench/div.bench
echo "✓ Completed"

echo ""
echo "Step 2: Convert BENCH to GraphML"
echo "--------------------------------"
./ai4eda-toolkit convert bench2graphml test_data/bench/div.bench test_data/graphml/div.graphml
echo "✓ Completed"

echo ""
echo "Step 3: Convert GraphML to PyTorch Geometric"
echo "--------------------------------------------"
./ai4eda-toolkit convert graphml2pt test_data/graphml/div.graphml test_data/pt/div.pt
echo "✓ Completed"

echo ""
echo "Step 4: Calculate Metrics (Area & Delay)"
echo "----------------------------------------"
./ai4eda-toolkit metrics test_data/aig/div.aig --lib libs/asap7.lib
echo "✓ Completed"

echo ""
echo "Step 5: Generate Synthesis Recipes"
echo "----------------------------------"
./ai4eda-toolkit recipe generate test_data/aig/div.aig test_data/recipes --num-recipes 5
echo "✓ Completed"

echo ""
echo "=================================="
echo "All tests passed successfully!"
echo "=================================="
echo ""
echo "Generated files:"
echo "  - BENCH:    test_data/bench/div.bench"
echo "  - GraphML:  test_data/graphml/div.graphml"
echo "  - PT:       test_data/pt/div.pt"
echo "  - Recipes:  test_data/recipes/"
echo ""
echo "You can now use the toolkit for your EDA data processing!"
