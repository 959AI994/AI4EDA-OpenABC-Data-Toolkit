#!/usr/bin/env python3
"""
Quick test to verify web application setup
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test all necessary imports"""
    print("Testing imports...")
    try:
        from flask import Flask
        print("  ✓ Flask imported")

        from ai4eda.converters.aig_to_bench import AigToBenchConverter
        print("  ✓ AigToBenchConverter imported")

        from ai4eda.converters.bench_to_graphml import BenchToGraphMLConverter
        print("  ✓ BenchToGraphMLConverter imported")

        from ai4eda.converters.graphml_to_pt import GraphMLToPTConverter
        print("  ✓ GraphMLToPTConverter imported")

        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_app_config():
    """Test Flask app configuration"""
    print("\nTesting Flask app configuration...")
    try:
        from app import app, CONVERSIONS

        print(f"  ✓ App created successfully")
        print(f"  ✓ {len(CONVERSIONS)} conversion types configured:")
        for key, conv in CONVERSIONS.items():
            print(f"    - {key}: {conv['name']}")

        print(f"  ✓ Upload folder: {app.config['UPLOAD_FOLDER']}")
        print(f"  ✓ Output folder: {app.config['OUTPUT_FOLDER']}")

        return True
    except Exception as e:
        print(f"  ✗ App configuration failed: {e}")
        return False


def test_directories():
    """Test that required directories exist"""
    print("\nTesting directories...")
    web_dir = Path(__file__).parent

    dirs_to_check = [
        'templates',
        'static',
        'static/css',
        'static/js',
        'uploads',
        'outputs'
    ]

    all_exist = True
    for dir_name in dirs_to_check:
        dir_path = web_dir / dir_name
        if dir_path.exists():
            print(f"  ✓ {dir_name}/ exists")
        else:
            print(f"  ✗ {dir_name}/ missing")
            all_exist = False

    return all_exist


def test_files():
    """Test that required files exist"""
    print("\nTesting files...")
    web_dir = Path(__file__).parent

    files_to_check = [
        'app.py',
        'requirements.txt',
        'start_server.sh',
        'run_daemon.sh',
        'templates/index.html',
        'static/css/style.css',
        'static/js/main.js'
    ]

    all_exist = True
    for file_name in files_to_check:
        file_path = web_dir / file_name
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  ✓ {file_name} ({size} bytes)")
        else:
            print(f"  ✗ {file_name} missing")
            all_exist = False

    return all_exist


def main():
    """Run all tests"""
    print("=" * 60)
    print("AI4EDA Web Interface - Setup Verification")
    print("=" * 60)

    results = {
        'Imports': test_imports(),
        'App Configuration': test_app_config(),
        'Directories': test_directories(),
        'Files': test_files()
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")

    if all(results.values()):
        print("\n✓ All tests passed! Web application is ready to run.")
        print("\nTo start the server, run:")
        print("  ./start_server.sh")
        print("  or")
        print("  ./run_daemon.sh start")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
