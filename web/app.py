#!/usr/bin/env python3
"""
AI4EDA Data Toolkit - Web Interface
Flask-based web application for EDA data format conversion
"""

import os
import sys
import uuid
import zipfile
import requests
import secrets
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename

# Add parent directory to path to import ai4eda modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai4eda.converters.aig_to_bench import AigToBenchConverter
from ai4eda.converters.bench_to_graphml import BenchToGraphMLConverter
from ai4eda.converters.graphml_to_pt import GraphMLToPTConverter
from ai4eda.converters.verilog_to_aig import VerilogToAigConverter
from ai4eda.converters.aig_to_pt import AigToPTConverter
from ai4eda.converters.verilog_to_pt import VerilogToPTConverter
from ai4eda.core.metrics import MetricsCalculator

# Load deployment-specific values; .env is intentionally excluded from Git.
load_dotenv(Path(__file__).with_name(".env"))

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['OUTPUT_FOLDER'] = Path(__file__).parent / 'outputs'
app.config['SECRET_KEY'] = os.getenv('AI4EDA_SECRET_KEY') or secrets.token_hex(32)

# Ensure directories exist
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)

# DeepSeek API Configuration (Volcengine)
VOLCENGINE_CONFIG = {
    "api_key": os.getenv("VOLCENGINE_API_KEY", ""),
    "base_url": os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
    "default_model": os.getenv("VOLCENGINE_MODEL", "deepseek-v3-1-250821"),
    "timeout": 120
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'aig': ['.aig'],
    'bench': ['.bench'],
    'graphml': ['.graphml'],
    'verilog': ['.v', '.sv'],
    'pt': ['.pt']
}

# Conversion configurations
CONVERSIONS = {
    'aig2bench': {
        'name': 'AIG to BENCH',
        'input': 'aig',
        'output': '.bench',
        'description': 'Convert And-Inverter Graph to BENCH format'
    },
    'bench2graphml': {
        'name': 'BENCH to GraphML',
        'input': 'bench',
        'output': '.graphml',
        'description': 'Convert BENCH netlist to GraphML format'
    },
    'graphml2pt': {
        'name': 'GraphML to PyTorch',
        'input': 'graphml',
        'output': '.pt',
        'description': 'Convert GraphML to PyTorch Geometric format'
    },
    'verilog2aig': {
        'name': 'Verilog to AIG',
        'input': 'verilog',
        'output': '.aig',
        'description': 'Convert Verilog HDL to AIG format'
    },
    'aig2pt': {
        'name': 'AIG to PyTorch (Direct)',
        'input': 'aig',
        'output': '.pt',
        'description': 'One-step conversion from AIG to PyTorch Geometric'
    },
    'verilog2pt': {
        'name': 'Verilog to PyTorch (Direct)',
        'input': 'verilog',
        'output': '.pt',
        'description': 'One-step conversion from Verilog to PyTorch Geometric'
    }
}


def allowed_file(filename, file_type):
    """Check if file extension is allowed"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS.get(file_type, [])


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', conversions=CONVERSIONS)


@app.route('/api/convert', methods=['POST'])
def convert():
    """Handle file conversion"""
    try:
        # Get conversion type
        conversion_type = request.form.get('conversion_type')
        if not conversion_type or conversion_type not in CONVERSIONS:
            return jsonify({'error': 'Invalid conversion type'}), 400

        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file type
        conv_config = CONVERSIONS[conversion_type]
        if not allowed_file(file.filename, conv_config['input']):
            return jsonify({
                'error': f'Invalid file type. Expected: {ALLOWED_EXTENSIONS[conv_config["input"]]}'
            }), 400

        # Generate unique ID for this conversion
        conversion_id = str(uuid.uuid4())

        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = app.config['UPLOAD_FOLDER'] / f"{conversion_id}_{filename}"
        file.save(input_path)

        # Generate output filename
        output_filename = Path(filename).stem + conv_config['output']
        output_path = app.config['OUTPUT_FOLDER'] / f"{conversion_id}_{output_filename}"

        # Perform conversion
        success, message = perform_conversion(
            conversion_type,
            str(input_path),
            str(output_path),
            request.form
        )

        # Clean up input file
        try:
            input_path.unlink()
        except:
            pass

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'download_url': f'/api/download/{conversion_id}_{output_filename}',
                'filename': output_filename
            })
        else:
            return jsonify({'error': message}), 500

    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500


def perform_conversion(conversion_type, input_path, output_path, form_data):
    """Perform the actual conversion"""
    try:
        if conversion_type == 'aig2bench':
            converter = AigToBenchConverter()
            success, msg = converter.convert(input_path, output_path)

        elif conversion_type == 'bench2graphml':
            converter = BenchToGraphMLConverter()
            success, msg = converter.convert(input_path, output_path)

        elif conversion_type == 'graphml2pt':
            converter = GraphMLToPTConverter()
            success, msg = converter.convert(input_path, output_path)

        elif conversion_type == 'verilog2aig':
            top_module = form_data.get('top_module', None)
            converter = VerilogToAigConverter()
            success, msg = converter.convert(input_path, output_path, top_module)

        elif conversion_type == 'aig2pt':
            converter = AigToPTConverter()
            success, msg = converter.convert(input_path, output_path, keep_intermediate=False)

        elif conversion_type == 'verilog2pt':
            top_module = form_data.get('top_module', None)
            converter = VerilogToPTConverter()
            success, msg = converter.convert(input_path, output_path, top_module, keep_intermediate=False)

        else:
            return False, f'Unknown conversion type: {conversion_type}'

        return success, msg

    except Exception as e:
        return False, f'Conversion error: {str(e)}'


@app.route('/api/download/<filename>')
def download(filename):
    """Download converted file"""
    try:
        file_path = app.config['OUTPUT_FOLDER'] / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename.split('_', 1)[1]  # Remove UUID prefix
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/info')
def info():
    """Get toolkit information"""
    try:
        import torch
        import torch_geometric
        from ai4eda.utils.version_compat import get_pyg_version

        pyg_version = get_pyg_version()

        return jsonify({
            'toolkit_version': '0.1.0',
            'pytorch_version': torch.__version__,
            'pyg_version': torch_geometric.__version__,
            'pyg_major': f"{pyg_version[0]}.x" if pyg_version else "Unknown",
            'supported_conversions': len(CONVERSIONS)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/convert/batch', methods=['POST'])
def convert_batch():
    """Handle batch file conversion"""
    try:
        conversion_type = request.form.get('conversion_type')
        if not conversion_type or conversion_type not in CONVERSIONS:
            return jsonify({'error': 'Invalid conversion type'}), 400

        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files uploaded'}), 400

        conv_config = CONVERSIONS[conversion_type]
        results = []

        # Extract files from ZIP if present
        all_files = []
        for file in files:
            if file.filename.endswith('.zip'):
                # Handle ZIP file
                zip_id = str(uuid.uuid4())
                zip_path = app.config['UPLOAD_FOLDER'] / f"{zip_id}_{secure_filename(file.filename)}"
                file.save(zip_path)

                try:
                    import shutil
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        extract_dir = app.config['UPLOAD_FOLDER'] / f"{zip_id}_extracted"
                        extract_dir.mkdir(exist_ok=True)
                        zip_ref.extractall(extract_dir)

                        # Find all valid files in extracted directory
                        for root, dirs, filenames in os.walk(extract_dir):
                            for filename in filenames:
                                if allowed_file(filename, conv_config['input']):
                                    filepath = Path(root) / filename
                                    # Copy to temporary location with sanitized filename
                                    temp_id = str(uuid.uuid4())
                                    # Use secure_filename to sanitize the filename
                                    safe_name = secure_filename(filename)
                                    temp_path = app.config['UPLOAD_FOLDER'] / f"{temp_id}_{safe_name}"
                                    shutil.copy2(filepath, temp_path)
                                    all_files.append((filename, temp_path))

                    # Clean up ZIP and extracted files
                    zip_path.unlink()
                    shutil.rmtree(extract_dir)

                except zipfile.BadZipFile:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': 'Invalid ZIP file'
                    })
                    continue
            else:
                # Handle regular file
                if file.filename == '':
                    continue

                conversion_id = str(uuid.uuid4())
                filename = secure_filename(file.filename)
                input_path = app.config['UPLOAD_FOLDER'] / f"{conversion_id}_{filename}"
                file.save(input_path)
                all_files.append((filename, input_path))

        # Process all collected files
        for filename, input_path in all_files:
            if not allowed_file(filename, conv_config['input']):
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': f'Invalid file type. Expected: {ALLOWED_EXTENSIONS[conv_config["input"]]}'
                })
                try:
                    input_path.unlink()
                except:
                    pass
                continue

            # Generate unique ID and output filename
            conversion_id = str(uuid.uuid4())
            output_filename = Path(filename).stem + conv_config['output']
            output_path = app.config['OUTPUT_FOLDER'] / f"{conversion_id}_{output_filename}"

            # Perform conversion
            success, message = perform_conversion(
                conversion_type,
                str(input_path),
                str(output_path),
                request.form
            )

            # Clean up input file
            try:
                input_path.unlink()
            except:
                pass

            if success:
                results.append({
                    'filename': filename,
                    'success': True,
                    'message': message,
                    'download_url': f'/api/download/{conversion_id}_{output_filename}',
                    'output_filename': output_filename
                })
            else:
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': message
                })

        return jsonify({
            'results': results,
            'total': len(results),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success'])
        })

    except Exception as e:
        return jsonify({'error': f'Batch conversion failed: {str(e)}'}), 500


@app.route('/api/metrics', methods=['POST'])
def calculate_metrics():
    """Calculate metrics for a single file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get parameters
        lib_file = request.form.get('lib_file', 'asap7')
        opt_script = request.form.get('opt_script', '')

        # Handle library selection
        if lib_file == 'custom':
            if 'custom_lib' not in request.files:
                return jsonify({'error': 'Custom library file not provided'}), 400
            # Save custom library temporarily
            custom_lib = request.files['custom_lib']
            lib_path = app.config['UPLOAD_FOLDER'] / f"temp_{uuid.uuid4()}.lib"
            custom_lib.save(lib_path)
        else:
            # Map library names to file paths
            lib_mapping = {
                'asap7': 'asap7.lib',
                'nangate45': 'nangate45.lib'
            }
            lib_filename = lib_mapping.get(lib_file, 'asap7.lib')
            lib_path = Path(__file__).parent.parent / 'libs' / lib_filename

        # Save uploaded file
        conversion_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        input_path = app.config['UPLOAD_FOLDER'] / f"{conversion_id}_{filename}"
        file.save(input_path)

        # Calculate metrics
        calculator = MetricsCalculator(str(lib_path))
        file_ext = Path(filename).suffix

        if file_ext == '.aig':
            area, delay, msg = calculator.calculate_from_aig(str(input_path), opt_script)
        elif file_ext == '.bench':
            area, delay, msg = calculator.calculate_from_bench(str(input_path), opt_script)
        else:
            return jsonify({'error': 'Unsupported file format. Use .aig or .bench'}), 400

        # Clean up
        try:
            input_path.unlink()
            if lib_file == 'custom' and lib_path.exists():
                lib_path.unlink()
        except:
            pass

        if area is not None and delay is not None:
            return jsonify({
                'success': True,
                'filename': filename,
                'area': float(area),
                'delay': float(delay),
                'message': msg or 'Metrics calculated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': msg or 'Metrics calculation failed'
            }), 500

    except Exception as e:
        return jsonify({'error': f'Metrics calculation failed: {str(e)}'}), 500


@app.route('/api/metrics/batch', methods=['POST'])
def calculate_metrics_batch():
    """Calculate metrics for multiple files"""
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files uploaded'}), 400

        # Get parameters
        lib_file = request.form.get('lib_file', 'asap7')
        opt_script = request.form.get('opt_script', '')

        # Handle library selection
        if lib_file == 'custom':
            if 'custom_lib' not in request.files:
                return jsonify({'error': 'Custom library file not provided'}), 400
            custom_lib = request.files['custom_lib']
            lib_path = app.config['UPLOAD_FOLDER'] / f"temp_{uuid.uuid4()}.lib"
            custom_lib.save(lib_path)
        else:
            # Map library names to file paths
            lib_mapping = {
                'asap7': 'asap7.lib',
                'nangate45': 'nangate45.lib'
            }
            lib_filename = lib_mapping.get(lib_file, 'asap7.lib')
            lib_path = Path(__file__).parent.parent / 'libs' / lib_filename

        calculator = MetricsCalculator(str(lib_path))
        results = []

        # Extract files from ZIP if present
        all_files = []
        for file in files:
            if file.filename.endswith('.zip'):
                # Handle ZIP file
                zip_id = str(uuid.uuid4())
                zip_path = app.config['UPLOAD_FOLDER'] / f"{zip_id}_{secure_filename(file.filename)}"
                file.save(zip_path)

                try:
                    import shutil
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        extract_dir = app.config['UPLOAD_FOLDER'] / f"{zip_id}_extracted"
                        extract_dir.mkdir(exist_ok=True)
                        zip_ref.extractall(extract_dir)

                        # Find all valid files in extracted directory
                        for root, dirs, filenames in os.walk(extract_dir):
                            for filename in filenames:
                                if Path(filename).suffix in ['.aig', '.bench']:
                                    filepath = Path(root) / filename
                                    # Copy to temp location with sanitized filename
                                    temp_id = str(uuid.uuid4())
                                    safe_name = secure_filename(filename)
                                    temp_path = app.config['UPLOAD_FOLDER'] / f"{temp_id}_{safe_name}"
                                    shutil.copy2(filepath, temp_path)
                                    all_files.append((filename, temp_path))

                    # Clean up ZIP and extracted files
                    zip_path.unlink()
                    shutil.rmtree(extract_dir)

                except zipfile.BadZipFile:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': 'Invalid ZIP file'
                    })
                    continue
            else:
                # Handle regular file
                if file.filename == '':
                    continue

                filename = secure_filename(file.filename)
                conversion_id = str(uuid.uuid4())
                input_path = app.config['UPLOAD_FOLDER'] / f"{conversion_id}_{filename}"
                file.save(input_path)
                all_files.append((filename, input_path))

        # Process all collected files
        for filename, input_path in all_files:
            file_ext = Path(filename).suffix

            if file_ext not in ['.aig', '.bench']:
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': 'Unsupported file format'
                })
                try:
                    input_path.unlink()
                except:
                    pass
                continue

            # Calculate metrics
            if file_ext == '.aig':
                area, delay, msg = calculator.calculate_from_aig(str(input_path), opt_script)
            else:
                area, delay, msg = calculator.calculate_from_bench(str(input_path), opt_script)

            # Clean up
            try:
                input_path.unlink()
            except:
                pass

            if area is not None and delay is not None:
                results.append({
                    'filename': filename,
                    'success': True,
                    'area': float(area),
                    'delay': float(delay),
                    'message': msg or 'Success'
                })
            else:
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': msg or 'Calculation failed'
                })

        # Clean up custom library
        if lib_file == 'custom' and lib_path.exists():
            try:
                lib_path.unlink()
            except:
                pass

        return jsonify({
            'results': results,
            'total': len(results),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success'])
        })

    except Exception as e:
        return jsonify({'error': f'Batch metrics calculation failed: {str(e)}'}), 500


@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    return send_from_directory('static', path)


def call_deepseek_api(verilog_code, user_prompt):
    """Call DeepSeek API to analyze Verilog code"""
    if not VOLCENGINE_CONFIG["api_key"]:
        return False, "AI analysis is not configured. Set VOLCENGINE_API_KEY on the server."
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {VOLCENGINE_CONFIG['api_key']}"
        }

        system_message = """You are an expert in Verilog HDL and digital circuit design.
You can analyze Verilog code, explain functionality, identify issues, suggest optimizations,
and answer questions about the design."""

        user_message = f"""Here is a Verilog code:

```verilog
{verilog_code}
```

User's question/request: {user_prompt}

Please analyze the code and provide a detailed response."""

        payload = {
            "model": VOLCENGINE_CONFIG['default_model'],
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        response = requests.post(
            f"{VOLCENGINE_CONFIG['base_url']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=VOLCENGINE_CONFIG['timeout']
        )

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                analysis = result['choices'][0]['message']['content']
                return True, analysis
            else:
                return False, "No response from API"
        else:
            return False, f"API Error: {response.status_code} - {response.text}"

    except requests.exceptions.Timeout:
        return False, "API request timeout. Please try again."
    except Exception as e:
        return False, f"Error calling API: {str(e)}"


@app.route('/api/analyze', methods=['POST'])
def analyze_verilog():
    """Analyze Verilog code using DeepSeek API with Yosys pre-check"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file type
        if not allowed_file(file.filename, 'verilog'):
            return jsonify({'error': 'Invalid file type. Expected .v or .sv file'}), 400

        # Get user prompt
        user_prompt = request.form.get('prompt', '').strip()
        if not user_prompt:
            return jsonify({'error': 'Please provide a prompt/question'}), 400

        if not VOLCENGINE_CONFIG["api_key"]:
            return jsonify({"error": "AI analysis is not configured. Set VOLCENGINE_API_KEY on the server."}), 503

        # Read Verilog file content
        try:
            verilog_code = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({'error': 'File encoding error. Please ensure the file is UTF-8 encoded'}), 400

        # Check file size (limit to 100KB of code for API)
        if len(verilog_code) > 100000:
            return jsonify({'error': 'File too large. Maximum size is 100KB'}), 400

        # Check if this is a debug request
        is_debug_request = 'debug' in user_prompt.lower() or 'bug' in user_prompt.lower()

        # If debug request, run Yosys syntax check first
        yosys_check_result = None
        if is_debug_request:
            yosys_check_result = check_verilog_with_yosys(verilog_code, secure_filename(file.filename))

        # Prepare the prompt for LLM
        if is_debug_request and yosys_check_result:
            if yosys_check_result['has_errors']:
                # Yosys found errors - enhance prompt with error info
                enhanced_prompt = f"""{user_prompt}

**Yosys Synthesis Check Results:**
The code has synthesis errors. Yosys reported the following issues:

```
{yosys_check_result['errors']}
```

Please analyze these synthesis errors and provide:
1. Clear explanation of each error
2. Root cause of the problems
3. Specific code fixes
4. Best practices to avoid similar issues"""
            else:
                # Yosys check passed
                enhanced_prompt = f"""{user_prompt}

**Yosys Synthesis Check Results:**
✓ The code passed Yosys syntax and basic synthesis checks.

However, please still analyze for:
1. Logical bugs that synthesis won't catch
2. Potential race conditions or timing issues
3. Non-synthesizable constructs that might cause problems
4. Code quality and best practices
5. Any edge cases or corner case bugs"""

            user_prompt = enhanced_prompt

        # Call DeepSeek API
        success, result = call_deepseek_api(verilog_code, user_prompt)

        if success:
            return jsonify({
                'success': True,
                'filename': secure_filename(file.filename),
                'analysis': result,
                'prompt': user_prompt,
                'yosys_check': yosys_check_result
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 500

    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


def check_verilog_with_yosys(verilog_code, filename):
    """Run Yosys syntax check on Verilog code"""
    import subprocess
    import tempfile

    try:
        # Save verilog code to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
            f.write(verilog_code)
            temp_file = f.name

        # Yosys script for basic syntax check
        yosys_script = f"""
read_verilog {temp_file}
hierarchy -check
proc
"""

        # Try to find yosys
        yosys_path = os.getenv("YOSYS_PATH", "yosys")

        # Run Yosys
        result = subprocess.run(
            [yosys_path, '-p', yosys_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Clean up temp file
        try:
            os.unlink(temp_file)
        except:
            pass

        # Check for errors
        output = result.stderr + result.stdout
        has_errors = result.returncode != 0 or 'ERROR:' in output

        if has_errors:
            # Extract error messages
            error_lines = [line for line in output.split('\n') if 'ERROR:' in line or 'syntax error' in line.lower()]
            errors = '\n'.join(error_lines[:10])  # Limit to first 10 errors
        else:
            errors = ""

        return {
            'success': not has_errors,
            'has_errors': has_errors,
            'errors': errors,
            'full_output': output[:1000]  # Limit output size
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'has_errors': True,
            'errors': 'Yosys check timeout (code may be too complex)',
            'full_output': ''
        }
    except Exception as e:
        # If Yosys check fails, don't block the analysis
        return {
            'success': False,
            'has_errors': False,
            'errors': f'Could not run Yosys check: {str(e)}',
            'full_output': ''
        }


# Cleanup old files periodically (optional)
def cleanup_old_files(max_age_hours=24):
    """Remove files older than max_age_hours"""
    import time
    cutoff = time.time() - (max_age_hours * 3600)

    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        for file_path in folder.glob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                try:
                    file_path.unlink()
                except:
                    pass


if __name__ == '__main__':
    # Clean up old files on startup
    cleanup_old_files()

    # Run the app
    print("\n" + "="*60)
    print("AI4EDA Data Toolkit - Web Interface")
    print("="*60)
    print(f"Starting web server...")
    host = os.getenv("AI4EDA_HOST", "127.0.0.1")
    port = int(os.getenv("AI4EDA_PORT", "5000"))
    print(f"Access the application at: http://{host}:{port}")
    print(f"Press Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run(host=host, port=port, debug=os.getenv('AI4EDA_DEBUG', '0') == '1')
